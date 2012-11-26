from collections import OrderedDict

import orm
from . import models


class ModelOptions(models.ModelAttr):

    def __init__(self, db_name = '', indexes = None, ordering = None):
        if not db_name:
            # create db name from model class name
            db_name = self._model_attr_info.model.__name__ + 's'
            db_name = ''.join('_' + c.lower() if c.isupper() else c for c in db_name).strip('_')
        self.db_name = db_name  # db table name

        # create list of fields
        _fields = {}
        for attrName, attr in self._model_attr_info.model.__dict__.items():
            if isinstance(attr, fields.ModelField):
                _fields[attrName] = attr
        # sort by creation order
        self.fields = OrderedDict(sorted(_fields.items(), key = lambda i: i[1]._creationOrder))

        self.ordering = ordering or []  # default order for select when not specified - overriden

        indexes = orm.listify(indexes or [])
        # analyze indexes
        for index in indexes:
            assert isinstance(index, orm_indexes.Index)
            if index._model_attr_info.model is None:
                index.__init__(modelAttrInfo = self._model_attr_info)

        for field in self.fields.values():
            index = field.index
            if isinstance(index, bool):
                index = 'index' if index else ''
            if isinstance(index, str):  # index type name is given
                if not index:
                    continue
                index = orm_indexes.Index(orm_indexes.IndexField(field), type = index)
                index.__init__(modelAttrInfo = self._model_attr_info)
            assert isinstance(index, orm_indexes.Index)
            indexes.append(index)

        self.indexes = indexes


from . import fields, indexes as orm_indexes
