from . import models


class IndexField():
    """Helper class for defining a field for index
    """
    def __init__(self, field, sortOrder = 'asc', prefixLength = None):
        assert isinstance(field, fields.ModelField), 'Pass Field instances.'
        assert sortOrder in ('asc', 'desc'), 'Sort order must be `asc` or `desc`.'
        assert isinstance(prefixLength, int) or prefixLength is None, \
            'Index prefix length must None or int.'
        self.field = field
        self.sortOrder = sortOrder
        self.prefixLength = prefixLength


class Index(models.ModelAttr):
    """A database table index.
    """
    def __init__(self, *indexFields, type = 'index', name = '', method = ''):
        """
        @param indexFields: list of IndexField instances
        @param type: index, primary, unique, fulltext, spatial - specific fot the db
        @param method: btree, hash, gist, gin - specific fot the db
        """
        assert indexFields, 'Need at least one Field or IndexField'

        model = None
        indexFields = list(indexFields)
        for i, indexField in enumerate(indexFields):
            if isinstance(indexField, str):  # field name passed
                indexField = self._modelAttrInfo.model.__dict__[indexField]
            if isinstance(indexField, fields.ModelField):  # a field
                indexField = IndexField(indexField)
                indexFields[i] = indexField
            else:
                assert isinstance(indexField, IndexField), \
                    'Pass a field name or Field/IndexField instances.'
            model = model or indexField.field.model
            assert indexField.field.model is model, 'Indexed fields should be from the same table!'

        if type is True:
            type = 'index'

        assert isinstance(type, str) and type

        if name == '':
            # if name was not given compose it from the names of all fields involved in the index
            for indexField in indexFields:
                name += indexField.field.name + '_'
            name += type  # and add index type at the end
        self.name = name

        self.indexFields = indexFields  # fields involved in this index
        self.type = type  # index type: unique, primary, etc.
        self.method = method  # if empty - will be used default for this type of DB

    def __str__(self):
        return '{} `{}` ON ({}) {}'.format(self.type, self.name,
            ', '.join(str(indexField.field) for indexField in self.indexFields), self.method)

#    def _copy(self, model):
#        """Create a copy of the index with copy of fields in the index with the given model."""
#        assert isinstance(model, models.ModelMeta), 'Pass a Model.'
#        indexFields = [indexField for indexField in self.indexFields]
#        return Index(indexFields, self.type, self.name, self.method, **self.other)


class Unique(Index):
    """Convenience class for defining a unique index.
    """
    def __init__(self, *indexFields, name = '', method = ''):
        """
        @param indexFields: list of IndexField instances
        @param method: btree, hash, gist, gin - specific fot the db
        """
        import ipdb; from pprint import pprint; ipdb.set_trace()
        super().__init__(*indexFields, type = 'unique', name = name, method = method)
    
    def test(self):
        pass


from . import fields
