import re

import orm
from . import models, fields


class ModelOptions(models.ModelAttr):

    def __init__(self, db_name = '', indexes = None, ordering = None):
        if not db_name:
            db_name = self._modelAttrInfo.model.__name__ + 's'
            db_name = re.sub('(.)([A-Z])', r'\1_\2', db_name).lower()
        self.db_name = db_name  # db table name

        self.fields = {}
        for attrName, attr in self._modelAttrInfo.model.__dict__.items():
            if isinstance(attr, fields.ModelField):
                self.fields[attrName] = attr

        self.ordering = ordering or []  # default order for select when not specified - overriden

        indexes = orm.listify(indexes or [])
        # analyze indexes
        for index in indexes:
            assert isinstance(index, orm.Index)
            index.__init__(modelAttrInfo = self._modelAttrInfo)
        self.indexes = indexes


#        if isinstance(index, bool):
#            index = 'index' if index else ''
#        if isinstance(index, str):  # index type name is given
#            index = orm.Index([orm.IndexField(self)], index)
#        assert isinstance(index, orm.Index)
#        self.model._indexes.append(index)
#        indexesDict = OrderedDict() # to filter duplicate indexes by index name
#        for index in NewModel._indexes:
#            if index.model is not NewModel: # inherited index
#                if not isinstance(index, orm.Index):
#                    raise orm.ModelError('Found a non Index in the _indexes.')
#                if index.model is not NewModel:
#                    # index was inherited from parent model - recreate it with fields from new model
#                    indexFields = [orm.IndexField(NewModel[indexField.field.name], indexField.sortOrder, indexField.prefixLength)
#                                   for indexField in index.indexFields] # replace fields by name with fields from new model
#                    index = orm.Index(indexFields, index.type, index.name, index.method, **index.other)
#                for indexField in index.indexFields:
#                    if issubclass(NewModel, indexField.field.model):
#                        indexField.field = NewModel[indexField.field.name] # to assure that field from this model, and from parent, is used
#                    else:
#                        raise orm.ModelError('Field `%s` in index is not from model `%s`.' % (indexField.field, NewModel))
#            indexesDict[index.name] = index
