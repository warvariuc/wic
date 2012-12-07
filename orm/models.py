__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import inspect
from datetime import datetime as DateTime, date as Date
from decimal import Decimal
from collections import OrderedDict

import orm
from orm import Nil


class ModelAttrInfo():
    """Information about an attribute of a Model
    """
    def __init__(self, model, name):
        """
        @param model: model class to which the attribute belongs
        @param name: name of the attribute in the model class 
        """
        if model is not None:
            assert orm.is_model(model)
            assert isinstance(name, str) and name
#            assert hasattr(model, name), 'Model %s does not have an attribute with name %s' \
#                % (orm.get_object_path(model), name)
        self.model = model
        self.name = name


class ProxyInit():
    """A descriptor to hook accesss to `__init__` of a Model attribute, which needs postponed
    initialiaztion only when the model is fully initialized.
    """
    def __init__(self, cls):
        """
        @param cls: model attribute class
        """
        if not isinstance(cls.__init__, ProxyInit):
            self.orig_init = cls.__init__  # original __init__
            cls.__init__ = self

    def __get__(self, obj, cls):

        if obj is not None:

            orig_init = self.orig_init

            def proxy_init(self, *args, **kwargs):
                """This will replace `__init__` method of a Model attribute, will remember
                initialization arguments and will call the original `__init__` when information
                about the model attribute is passed.
                """
#                print('ModelAttrStubMixin.__init__', self.__class__.__name__, args, kwargs)
                model_attr_info = kwargs.pop('model_attr_info', None)
                if model_attr_info:
                    self._model_attr_info = model_attr_info
                else:
                    obj._initArgs = args
                    obj._initKwargs = kwargs
                if self._model_attr_info.model is not None:
                    orig_init(self, *self._initArgs, **self._initKwargs)
#            return MethodType(__init__, obj)
            # functions are descriptors, to be able to work as bound methods
            return proxy_init.__get__(obj, cls)

        return self


class ModelAttr():
    """Mixin class for Model attributes, which holds information about initialization arguments,
    `__init__` being called only after the model is completely defined.
    Usually `__init__` is called  by the Model metaclass.
    """
    __creationCounter = 0  # will be used to track the definition order of the attributes in models
    _model_attr_info = ModelAttrInfo(None, None)  # model attribute information, set by `_init_`

    def __new__(cls, *args, **kwargs):
        """Create the object, but prevent calling its `__init__` method, montkey patching it with a
        stub, remembering the initizalization arguments. The real `__init__` can be called later.
        """
        # create the object normally
        self = super().__new__(cls)
        ModelAttr.__creationCounter += 1
        self._creationOrder = ModelAttr.__creationCounter
#        print('ModelAttrMixin.__new__', cls, repr(self))
        ProxyInit(cls)  # monkey patching `__init__` with our version
        return self


class ModelBase(type):
    """Metaclass for all models.
    It gives names to all fields and makes instances for fields for each of the models.
    It has some class methods for models.
    """
    def __new__(cls, name, bases, attrs):
        NewModel = super().__new__(cls, name, bases, attrs)

        parent_models = [base for base in bases if isinstance(base, ModelBase)]
        if not parent_models:
            # If this isn't a subclass of Model, don't do anything special.
            return NewModel

        try:

            logger.debug('Finishing initialization of model `%s`' % orm.get_object_path(NewModel))

            model_attrs = OrderedDict()
            for attr_name, attr in inspect.getmembers(NewModel):
                if isinstance(attr, ModelAttr):
                    model_attrs[attr_name] = attr

            _meta = model_attrs.pop('_meta', None)
            assert isinstance(_meta, model_options.ModelOptions), \
                '`_meta` attribute should be instance of ModelOptions'
            # sort by definition order - for the correct recreation order
            model_attrs = sorted(model_attrs.items(), key=lambda i: i[1]._creationOrder)

            for attr_name, attr in model_attrs:
                if attr._model_attr_info.model:  # inherited field
                    # make its copy for the new model
                    _attr = attr.__class__(*attr._initArgs, **attr._initKwargs)
                    _attr._creationOrder = attr._creationOrder
                    attr = _attr
                try:
                    attr.__init__(model_attr_info=ModelAttrInfo(NewModel, attr_name))
                except Exception:
                    logger.debug('Failed to init a model attribute: %s.%s'
                                 % (orm.get_object_path(NewModel), attr_name))
                    raise
                setattr(NewModel, attr_name, attr)

            # process _meta at the end, when all fields should have been initialized
            if _meta._model_attr_info.model is not None:  # inherited
                _meta = model_options.ModelOptions()  # override
            _meta.__init__(model_attr_info=ModelAttrInfo(NewModel, '_meta'))
            NewModel._meta = _meta

            # make per model exceptions
            NewModel.RecordNotFound = type(
                'RecordNotFound',
                tuple(parent_model.RecordNotFound
                      for parent_model in parent_models),
                {'__module__': NewModel.__module__}
            )
            NewModel.MultipleRecordsFound = type(
                'MultipleRecordsFound',
                tuple(parent_model.MultipleRecordsFound
                      for parent_model in parent_models),
                {'__module__': NewModel.__module__}
            )

        except Exception as exc:
            raise exceptions.ModelError(str(exc))

        return NewModel

    def __getitem__(self, field_name):
        """Get a Model field by name - Model['field_name'].
        """
        if field_name in self._meta.fields:
            return getattr(self, field_name)  # to ensure descriptor behavior
        raise exceptions.ModelFieldError

    def __iter__(self):
        """Get Table fields.
        """
        for field_name in self._meta.fields:
            yield getattr(self, field_name)  # to ensure descriptor behavior

    def __len__(self):
        return len(self._meta.fields)

    def __str__(self):
        return self._meta.db_name


from . import model_fields, signals, logger, exceptions, model_options, query_manager, adapters


class Model(metaclass=ModelBase):
    """Base class for all models. Class attributes - the fields.
    Instance attributes - the values for the corresponding model fields.
    """
    objects = query_manager.QueryManager()
    _meta = model_options.ModelOptions(abstract=True)

    RecordNotFound = exceptions.RecordNotFound
    MultipleRecordsFound = exceptions.MultipleRecordsFound

    # default fields
    # row id. This field is present in all model
    id = model_fields.IdField()
    # version of the record - datetime (with milliseconds) of the last update of this record
    timestamp = model_fields.DateTimeField()

    def __init__(self, db, *args, **kwargs):
        """Create a model instance - a record.
        @param db: db adapter in which to save the table record or from which it was fetched
        @param *args: tuples (ModelField or field_name, value)
        @param **kwargs: {field_name: fieldValue}
        """
        if not isinstance(db, adapters.GenericAdapter) and db is not None:
            raise exceptions.RecordError('`db` should be a GenericAdapter instance')
        self._db = db

        model = None
        for arg in args:
            assert isinstance(arg, (list, tuple)) and len(arg) == 2, \
                'Pass tuples with 2 items: (field, value).'
            field, value = arg
            if isinstance(field, str):
                field = self.__class__[field]
            assert isinstance(field, model_fields.FieldExpression), 'First arg must be a Field.'
            field = field.left
            _model = field.model
            model = model or _model
            assert model is _model, 'Pass fields from the same model'
            kwargs[field.name] = value

        # make values for fields
        for field_name, field in self._meta.fields.items():
            # is this a field name?
            field_value = kwargs.pop(field_name, Nil)
            if field_value is Nil and isinstance(field, model_fields.RelatedRecordField):
                # a related record id?
                field_value = kwargs.pop(field._name, Nil)
                if field_value is not Nil:
                    field_name = field._name

            if field_value is Nil:
                field_value = field.default

            try:
                setattr(self, field_name, field_value)
            except exceptions.RecordValueError as exc:
                raise exceptions.RecordValueError(str(exc))

        if kwargs:
            raise exceptions.ModelError('Got unknown field names: %s' % ', '.join(kwargs))

    def __getitem__(self, field):
        """Get a Record Field value by key.
        key: either a Field instance or name of the field.
        """
        model = self.__class__
        if isinstance(field, model_fields.FieldExpression):
            field = field.left
        if isinstance(field, model_fields.ModelField):
            assert field.model is model, 'This field is from another model.'
            attr_name = field.name
        elif isinstance(field, str):
            field = model[field]
            attr_name = field.name
        else:
            raise TypeError('Pass either a Field or its name.')
        return getattr(self, attr_name)

    def delete(self):
        """Delete this record.
        """
        db = self._db
        self.objects.check_table(db)
        model = self.__class__
        signals.pre_delete.send(sender=model, record=self)
        db.delete(model, where=(model.id == self.id))
        db.commit()
        signals.post_delete.send(sender=model, record=self)
        self.id = None

    def save(self):
        db = self._db
        model = self.__class__
        model.objects.check_table(db)
        self.timestamp = DateTime.now()
        values = []  # list of tuples (Field, value)
        for field in model._meta.fields.values():
            value = Nil
            if isinstance(field, model_fields.RelatedRecordField):
                value = getattr(self, field._name)
            else:
                value = self[field]

            values.append(field(value))

        signals.pre_save.send(sender=model, record=self)

        is_new = not self.id
        if is_new:  # new record
            self.id = db.insert(*values)
        else:  # existing record
            rows_count = db.update(*values, where=(model.id == self.id))
            if not rows_count:
                raise orm.exceptions.RecordSaveError('Looks like the record was deleted: table=`%s`'
                                                     ', id=%s' % (model, self.id))
        db.commit()

        signals.post_save.send(sender=model, record=self, is_new=is_new)

    def __str__(self):
        """Human readable presentation of the record.
        """
        values = []
        for field_name, field in self._meta.fields.items():
            if isinstance(field, model_fields.RelatedRecordField):
                field_name = field._name
            field_value = getattr(self, field_name)
            if isinstance(field_value, (Date, DateTime, Decimal)):
                field_value = str(field_value)
            values.append("%s= %r" % (field_name, field_value))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(values))

    @classmethod
    def COUNT(cls, where=None):
        """Get COUNT expression for this table.
        @param where: WHERE expression
        """
        return orm.COUNT(where or cls)  # COUNT expression


class Join():
    """Object holding parameters for a join.
    """
    def __init__(self, model, on, type=''):
        """
        @param model: table to join
        @param on: join condition
        @param type: join type. if empty - INNER JOIN
        """
        assert orm.is_model(model), 'Pass a model class.'
        assert isinstance(on, orm.Expression), 'WHERE should be an Expression.'
        self.model = model  # table to join
        self.on = on  # expression defining join condition
        self.type = type  # join type. if empty - INNER JOIN


class LeftJoin(Join):
    """Left join parameters.
    """
    def __init__(self, table, on):
        super().__init__(table, on, 'left')
