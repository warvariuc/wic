"""Note: model options (db table name, ordering, ...) in kept in `Model._meta` attribute are not
inherited from the parent model.
"""
from collections import OrderedDict

import orm
from . import models


class ModelOptions(models.ModelAttr):

    def __init__(self, db_name='', db_indexes=None, ordering=None,
                 abstract=False):
        """Model settings
        @param db_name: name of the corresponding table in the database
        @param ordering: The default ordering for DB rows. This is a tuple or list of fields.
            Each field can be prefixed with '-' or '+' to indicate ascending/descending fethcing
            order. Fields without a leading "-" will be ordered ascending. Use None to order
            randomly.
        @param abstract: whether the model is abstract. Abstract base classes are useful when you
            want to put some common information into a number of other models. You write your base
            class and put abstract=True in the _meta attribute. This model will then not be used to
            create any database table.
        """
        # TODO: add `proxy` argument, similarly to Django
        if not db_name:
            # create db name from model class name
            db_name = self._model_attr_info.model.__name__ + 's'
            db_name = ''.join('_' + c.lower() if c.isupper() else c for c in db_name).strip('_')
        self.db_name = db_name  # db table name

        # create list of fields
        _fields = {}
        for attr_name, attr in self._model_attr_info.model.__dict__.items():
            if isinstance(attr, model_fields.ModelField):
                _fields[attr_name] = attr
        # sort by creation order
        self.fields = OrderedDict(sorted(_fields.items(), key=lambda i: i[1]._creationOrder))

        self.ordering = ordering or []  # default order for select when not specified - overriden

        db_indexes = orm.listify(db_indexes or [])
        # analyze indexes
        for db_index in db_indexes:
            assert isinstance(db_index, orm_indexes.DbIndex)
            if db_index._model_attr_info.model is None:
                db_index.__init__(model_attr_info=self._model_attr_info)

        for field in self.fields.values():
            db_index = field.db_index
            if isinstance(db_index, bool):
                db_index = 'index' if db_index else ''
            if isinstance(db_index, str):  # index type name is given
                if not db_index:
                    continue
                index = orm_indexes.DbIndex(orm_indexes.DbIndexField(field), type=db_index)
                index.__init__(model_attr_info=self._model_attr_info)
            assert isinstance(index, orm_indexes.DbIndex)
            db_indexes.append(index)

        self.db_indexes = db_indexes
        self.abstract = abstract


from . import model_fields, db_indexes as orm_indexes
