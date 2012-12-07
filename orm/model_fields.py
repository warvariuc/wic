__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from datetime import datetime as DateTime, date as Date
from decimal import Decimal

import orm
from orm import Nil
from . import adapters, models


class Expression():
    """Expression - pair of operands and operation on them.
    """

    sort = 'ASC'  # default sorting

    def __init__(self, operation, left=Nil, right=Nil, type=None, **kwargs):
        """Create an expression.
        @param operation: string with the operation name (defined in adapters)
        @param left: left operand
        @param right: right operand
        @param type: cast type field
        """
        if left is not Nil and not type:
            if isinstance(left, ModelField):
                self.type = left
            elif isinstance(left, Expression):
                self.type = left.type
            else:
                self.type = None
                #left = str(left)
                #raise Exception('Cast target must be an Expression/Field.')
        else:
            self.type = type
        self.operation = operation
        self.left = left  # left operand
        self.right = right  # right operand
        self.__dict__.update(kwargs)  # additional arguments

    def __and__(self, other):
        return Expression('_AND', self, other)

    def __or__(self, other):
        return Expression('_OR', self, other)

    def __eq__(self, other):
        return Expression('_EQ', self, other)

    def __ne__(self, other):
        return Expression('_NE', self, other)

    def __gt__(self, other):
        return Expression('_GT', self, other)

    def __ge__(self, other):
        return Expression('_GE', self, other)

    def __lt__(self, other):
        return Expression('_LT', self, other)

    def __le__(self, other):
        return Expression('_LE', self, other)

    def __add__(self, other):
        return Expression('_ADD', self, other)

    def __neg__(self):
        """-Field: sort DESC"""
        self.sort = 'DESC'  # TODO: should return new Expression
        return self

    def __pos__(self):
        """+Field: sort ASC"""
        self.sort = 'ASC'
        return self

    def UPPER(self):
        return Expression('_UPPER', self)

    def LOWER(self):
        return Expression('_LOWER', self)

    def IN(self, *items):
        """The IN clause."""
        return Expression('_IN', self, items)

    def LIKE(self, pattern):
        assert isinstance(pattern, str), 'Pattern must be a string.'
        return Expression('_LIKE', self, pattern)

    def __str__(self, db=None):
        """Construct the text of the WHERE clause from this Expression.
        @param db: GenericAdapter subclass to use for rendering.
        """
        args = [arg for arg in (self.left, self.right) if arg is not Nil]  # filter nil operands
        if not args:  # no args - treat operation as representation of the entire operation
            return self.operation
        db = db or orm.GenericAdapter
        operation = getattr(db, self.operation)  # get the operation function from adapter
        return operation(*args)  # execute the operation


class FieldExpression(Expression):
    """Expression which holds a single field.
    """
    def __init__(self, field):
        assert isinstance(field, ModelField)
        super().__init__('_MODELFIELD', field)
        # `model` attribute is needed to extract `from_` tables
        self.model = field.model

    def __call__(self, value):
        return self.left(value)


class ModelField(Expression, models.ModelAttr):
    """Abstract model field. It's inherited from Expression just for the sake of autocomplete
    in Python IDEs.
    """
    def __init__(self, column, db_index='', label='', default=None):
        """Base initialization method. Called from subclasses.
        @param column: Column instance
        @param db_index: name of the index type, or True - 'index' to be used
        @param label: verbose name, can be used in forms
        @param default: default value, can be callable
        """
        self.name = self._model_attr_info.name
        self.model = self._model_attr_info.model
        if not self.name.islower() or self.name.startswith('_'):
            raise orm.ModelError('Field `%s` in model `%s`: field names must be lowercase and '
                                 'must not start with `_`.'
                                 % (self.name, orm.get_object_path(self._model_attr_info.model)))
        assert isinstance(column, adapters.Column)
        self.column = column
        assert isinstance(db_index, (str, bool, db_indexes.DbIndex))
        self.db_index = db_index
        assert isinstance(label, str)
        self.label = label or self.name.replace('_', ' ').capitalize()
        self._default = default

    def __get__(self, record, model):
        if record is not None:
            # called as an instance attribute
            try:
                return record.__dict__[self.name]
            except KeyError:
                raise AttributeError('Value for field `%s` was not set yet' % self.name)
        # called as a class attribute
        return FieldExpression(self)

    def __call__(self, value):
        """You can use Field(...)(value) to return a tuple for INSERT.
        """
        return (self, value)

    def _cast(self, value):
        """Converts a value to Field's comparable type. Default implementation.
        """
        return value

    @property
    def default(self):
        """Returns the default value for this field.
        """
        if callable(self._default):
            return self._default()
        return self._default


# remove Expression from Field base classes, which was put for IDE autocomplete to work
_field_base_classes = list(ModelField.__bases__)
_field_base_classes.remove(Expression)
ModelField.__bases__ = tuple(_field_base_classes)


####################################################################################################
# Fields
####################################################################################################

class IdField(ModelField):
    """Primary integer autoincrement key. ID - implicitly present in each model.
    """
    def __init__(self, db_name='', label=''):
        # 9 digits - int32 - should be enough
        super().__init__(adapters.Column('INT', db_name or self._model_attr_info.name,
                                         precision=9, unsigned=True, nullable=True,
                                         autoincrement=True),
                         'primary', label, default=None)

    def __set__(self, record, value):
        record.__dict__[self.name] = None if value is None else int(value)


class CharField(ModelField):
    """Field for storing strings of certain length.
    """
    def __init__(self, max_length, default=None, db_index='', db_name='', label='',
                 comment='', nullable=True, db_default=Nil):
        """Initialize a CHAR field.
        @param max_length: maximum length in bytes of the string to be stored in the DB
        @param default: default value to store in the DB
            If no default value is declared explicitly, the default value is the null value.
        @param db_index: index type to be applied on the corresponding column in the DB
        @param db_name: name of the column in the DB table
        @param label: short description of the field (e.g.for for forms)
        @param comment: comment for the field
        @param nullable: whether the db column can have NULL values. A NULL value represents the
            complete absence of value within the column, not that it is merely blank.
        """
        super().__init__(adapters.Column('CHAR', db_name or self._model_attr_info.name,
                                         precision=max_length, default=db_default,
                                         comment=comment, nullable=nullable),
                         db_index, label, default)


class TextField(ModelField):
    """Field for storing strings of any length."""
    def __init__(self, default=None, db_index='', db_name='', label='', comment='',
                 nullable=True, db_default=Nil):
        if db_index:
            assert isinstance(db_index, orm.DbIndex)
        super().__init__(adapters.Column('TEXT', db_name or self._model_attr_info.name,
                                         default=db_default, comment=comment),
                         db_index, label, default)


class IntegerField(ModelField):

    def __init__(self, max_digits=9, default=None, autoincrement=False, db_index='',
                 db_name='', label='', nullable=True, db_default=Nil, comment=''):
        super().__init__(adapters.Column('INT', db_name or self._model_attr_info.name,
                                         precision=max_digits, unsigned=True,
                                         nullable=nullable, default=db_default,
                                         autoincrement=autoincrement, comment=comment),
                         db_index, label, default)

    def __set__(self, record, value):
        if not isinstance(value, int) and value is not None:
            raise exceptions.RecordValueError('Provide an int')
        record.__dict__[self.name] = value


class DecimalField(ModelField):

    def __init__(self, max_digits, decimal_places, default=None, db_index='', db_name='',
                 label='', nullable=True, db_default=Nil, comment=''):
        super().__init__(adapters.Column('DECIMAL', db_name or self._model_attr_info.name,
                                         precision=max_digits, scale=decimal_places,
                                         default=db_default, nullable=nullable,
                                         comment=comment),
                         db_index, label, default)

    def __set__(self, record, value):
        if not isinstance(value, Decimal) and value is not None:
            try:
                value = Decimal(value)
            except ValueError as exc:
                raise exceptions.RecordValueError('Provide a Decimal: %s' % exc)
        record.__dict__[self.name] = None if value is None else Decimal(value)


class DateField(ModelField):

    def __init__(self, default=None, db_index='', db_name='', label='', nullable=True,
                 db_default=Nil, comment=''):
        super().__init__(adapters.Column('DATE', db_name or self._model_attr_info.name,
                                         default=db_default, nullable=nullable,
                                         comment=comment),
                         db_index, label, default)

    def __set__(self, record, value):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d').date()
        elif not isinstance(value, Date) and value is not None:
            raise exceptions.RecordValueError('Provide a datetime.date or a string in format '
                                              '"%Y-%m-%d" with a valid date.')
        record.__dict__[self.name] = value


class DateTimeField(ModelField):

    def __init__(self, default=None, db_index='', db_name='', label='', db_default=Nil,
                 nullable=True, comment=''):
        super().__init__(adapters.Column('DATETIME', db_name or self._model_attr_info.name,
                                         default=db_default, nullable=nullable,
                                         comment=comment),
                         db_index, label, default)

    def __set__(self, record, value):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        elif not isinstance(value, DateTime) and value is not None:
            raise exceptions.RecordValueError('Provide a datetime.datetime or a string in format '
                                              '"%Y-%m-%d %H:%M:%S.%f" with valid date-time.')
        record.__dict__[self.name] = value


class BooleanField(ModelField):

    def __init__(self, default=None, db_index='', db_name='', label='', db_default=Nil,
                 nullable=True, comment=''):
        super().__init__(adapters.Column('INT', db_name or self._model_attr_info.name,
                                         precision=1, default=db_default, nullable=nullable,
                                         comment=comment),
                         db_index, label, default)

    def __set__(self, record, value):
        if not isinstance(value, bool) and value is not None:
            raise exceptions.RecordValueError('Provide a bool or None.')
        record.__dict__[self.name] = value


class _RecordId():
    """Descriptor for keeping id of a related record.
    """
    def __init__(self, record_field):
        """
        @param record_field: related record field
        """
        assert isinstance(record_field, RelatedRecordField)
        self._record_field = record_field

    def __set__(self, record, value):
        """Setter for this attribute."""
        if not isinstance(value, int) and value is not None:
            raise exceptions.RecordValueError('You can assign only int or None to %s.%s'
                                              % (orm.get_object_path(record),
                                                 self._record_field._name))
        record.__dict__[self._record_field._name] = value

    def __get__(self, record, model):
        if record is None:  # called as a class attribute
            return self

        # called as an instance attribute
        value = record.__dict__.get(self._record_field._name)
        if value is None or isinstance(value, int):
            return value
        elif isinstance(value, self._record_field.related_model):
            return value.id
        else:
            raise TypeError('This should not have happened: private attribute is not a record of '
                            'required model, id or None')


class RelatedRecordField(ModelField):
    """Field for storing ids to related records.
    """
    def __init__(self, related_model, db_index='', db_name='', label='', db_default=Nil,
                 nullable=True, comment=''):
        """
        @param related_model: a Model subclass of which record is referenced
        @param index: True if simple index, otherwise string with index type ('index', 'unique')
        """
        # 9 digits - int32 - ought to be enough for anyone ;)
        super().__init__(adapters.Column('INT', db_name or self._model_attr_info.name + '_id',
                                         precision=9, unsigned=True, default=db_default,
                                         nullable=nullable, comment=comment),
                         db_index, label)
        self._related_model = related_model  # path to the model
        self._name = self.name + '_id'  # name of the attribute which keeps id of the related record
        setattr(self.model, self._name, _RecordId(self))

    def __get__(self, record, model):
        if record is None:  # called as a class attribute
            return super().__get__(None, model)

        # called as an instance attribute
        value = record.__dict__.get(self._name)
        if value is None or isinstance(value, self.related_model):
            # the attribute was set None or record
            return value
        elif isinstance(value, int):
            # the attribute was set to an integer id
            related_record = self.related_model.objects.get_one(record._db, id=value)
            record.__dict__[self._name] = related_record
            return related_record
        else:
            raise TypeError('This should not have happened: private attribute is not a record of '
                            'required model, id or None')

    def __set__(self, record, value):
        """Setter for this field."""
        if not isinstance(value, self.related_model) and value is not None:
            raise exceptions.RecordValueError(
                'You can assign to `%s.%s` attribute only instances of model `%s` or None'
                % (orm.get_object_path(self.model), self.name,
                   orm.get_object_path(self.related_model))
            )
        record.__dict__[self._name] = value

    def __call__(self, value):
        """You can use Field(...)(value) to return a tuple for INSERT.
        """
        if isinstance(value, self.related_model):
            value = value.id
        elif not isinstance(value, int) and value is not None:
            raise exceptions.RecordValueError('Bad value. Pass a `%s` instance, int or None'
                                              % orm.get_object_path(self.related_model))
        return (self, value)

    @orm.LazyProperty
    def related_model(self):
        if orm.is_model(self._related_model):
            return self._related_model
        elif isinstance(self._related_model, str):
            if self._related_model == 'self':
                return self._model_attr_info.model
            return orm.get_object_by_path(self._related_model, self.model.__module__)
        else:
            raise exceptions.ModelError('Referred model must be a Model or a string with its path.')

    def _cast(self, value):
        """Convert a value into another value which is ok for this Field.
        """
        if isinstance(value, self.related_model):
            return value.id
        try:
            return int(value)
        except ValueError:
            raise exceptions.QueryError('Record ID must be an integer.')


#class TableIdField(Field):
#    """This field stores id of a given table in this DB."""
#    def _init_(self, index = ''):
#        super()._init_(Column('INT', self, precision = 5, unsigned = True), None, index)
#
#    def cast(self, value):
#        if isinstance(value, (orm.Model, orm.ModelMeta)):
#        # Table.tableIdField == Table -> Table.tableIdField == Table._tableId
#            return value._tableId
#        try:
#            return int(value)
#        except ValueError:
#            raise SyntaxError('Table ID must be an integer.')
#
#class AnyRelatedRecordField(Field):
#    """This field stores id of a row of any table.
#    It's a virtual field - it creates two real fields: one for keeping Record ID and another one
#     for Table ID.
#    """
#    def _init(self, index= ''):
#        super()._init(None, None) # no column, but later we create two fields
#
#        tableIdField = TableIdField(name= self.name + '_table', table= self.table)
#        tableIdField._init()
#        setattr(self.table, tableIdField.name, tableIdField)
#
#        recordIdField = RecordIdField(name= self.name + '_record', table= self.table)
#        recordIdField._init(None) # no refered table
#        setattr(self.table, recordIdField.name, recordIdField)
#
#        self.table._indexes.append(orm.Index([tableIdField, recordIdField], index))
#
#        self._fields = dict(tableId= tableIdField, itemId= recordIdField) # real fields
#
#    def __eq__(self, other):
#        assert isinstance(other, orm.Model)
#        return Expression('AND',
#                  Expression('EQ', self._fields['tableId'], other._tableId),
#                  Expression('EQ', self._fields['itemId'], other.id))


def COUNT(expression=None, distinct=False):
    if expression is None or isinstance(expression, Expression):
        return Expression('_COUNT', None, distinct=distinct)
    elif orm.is_model(expression):
        return Expression('_COUNT', None, model=expression)
    else:
        raise orm.QueryError('Argument must be a Field, an Expression or a Table.')


def MAX(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_MAX', expression)


def MIN(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_MIN', expression)


def UPPER(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_UPPER', expression)


def LOWER(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_LOWER', expression)


def CONCAT(*expressions):
    "Concatenate two or more expressions/strings."
    for expression in expressions:
        assert isinstance(expression, (str, Expression)), \
            'Argument must be a Field or an Expression or a str.'
    return Expression('_CONCAT', expressions)


from . import db_indexes, exceptions
