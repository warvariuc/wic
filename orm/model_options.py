from collections import OrderedDict

import orm
from . import models


class ModelOptions(models.ModelAttr):

    def __init__(self, db_name = '', indexes = None, ordering = None):
        if not db_name:
            db_name = self._modelAttrInfo.model.__name__ + 's'
            db_name = ''.join('_' + c.lower() if c.isupper() else c for c in db_name).strip('_')
        self.db_name = db_name  # db table name

        self.fields = {}
        for attrName, attr in self._modelAttrInfo.model.__dict__.items():
            if isinstance(attr, fields.ModelField):
                self.fields[attrName] = attr

        self.ordering = ordering or []  # default order for select when not specified - overriden

        indexes = orm.listify(indexes or [])
        # analyze indexes
        for index in indexes:
            assert isinstance(index, orm_indexes.Index)
            if index._modelAttrInfo.model is None:
                index.__init__(modelAttrInfo = self._modelAttrInfo)

        for field in self.fields.values():
            index = field.index
            if isinstance(index, bool):
                index = 'index' if index else ''
            if isinstance(index, str):  # index type name is given
                index = orm_indexes.Index([orm_indexes.IndexField(field)], index)
            assert isinstance(index, orm_indexes.Index)
            indexes.append(index)
#            indexesDict = OrderedDict() # to filter duplicate indexes by index name
#            for index in indexes:
#                if index.model is not NewModel: # inherited index
#                    if not isinstance(index, orm.Index):
#                        raise orm.ModelError('Found a non Index in the _indexes.')
#                    if index.model is not NewModel:
#                        # index was inherited from parent model - recreate it with fields from new model
#                        indexFields = [orm.IndexField(NewModel[indexField.field.name], indexField.sortOrder, indexField.prefixLength)
#                                       for indexField in index.indexFields] # replace fields by name with fields from new model
#                        index = orm.Index(indexFields, index.type, index.name, index.method, **index.other)
#                    for indexField in index.indexFields:
#                        if issubclass(NewModel, indexField.field.model):
#                            indexField.field = NewModel[indexField.field.name] # to assure that field from this model, and from parent, is used
#                        else:
#                            raise orm.ModelError('Field `%s` in index is not from model `%s`.' % (indexField.field, NewModel))
#                indexesDict[index.name] = index

        self.indexes = indexes

from . import fields, indexes as orm_indexes
