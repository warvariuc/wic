import orm


class IndexField():
    """Helper class for defining a field for index
    """
    def __init__(self, field, sortOrder = 'asc', prefixLength = None):
        assert isinstance(field, orm.fields.Field), 'Pass Field instances.'
        assert sortOrder in ('asc', 'desc'), 'Sort order must be `asc` or `desc`.'
        assert isinstance(prefixLength, int) or prefixLength is None, \
            'Index prefix length must None or int.'
        self.field = field
        self.sortOrder = sortOrder
        self.prefixLength = prefixLength


class Index():
    """A database table index.
    """
    def __init__(self, indexFields, type = 'index', name = '', method = '', **kwargs):
        """
        @param indexFields: list of IndexField instances
        @param type: index, primary, unique, fulltext, spatial - specific fot the db
        @param method: btree, hash, gist, gin - specific fot the db
        """
        assert isinstance(indexFields, (list, tuple)) and indexFields, \
            'Pass a list of indexed fields.'
        model = None
        for indexField in indexFields:
            assert isinstance(indexField, IndexField), 'Pass IndexField instances.'
            model = model or indexField.field.model
            assert indexField.field.model is model, 'Indexed fields should be from the same table!'

        self.model = model

        if type is True:
            type = 'index'

        assert isinstance(type, str) and type

        if name == '':
            # if name was not given compose it from the names of all fields involved in the index
            for indexField in indexFields:
                name += indexField.field.name + '_'
            name += type # and add index type at the end
        self.name = name

        self.indexFields = list(indexFields) # fields involved in this index
        self.type = type # index type: unique, primary, etc.
        self.method = method # if empty - will be used default for this type of DB
        self.other = kwargs # other parameters for a specific DB adapter

    def __str__(self):
        return '{} `{}` ON ({}) {}'.format(self.type, self.name,
            ', '.join(str(indexField.field) for indexField in self.indexFields), self.method)

#    def _copy(self, model):
#        """Create a copy of the index with copy of fields in the index with the given model."""
#        assert isinstance(model, orm.ModelMeta), 'Pass a Model.'
#        indexFields = [indexField for indexField in self.indexFields]
#        return Index(indexFields, self.type, self.name, self.method, **self.other)


class Unique(Index):
    """Convenience class for defining a unique index.
    """
    def __init__(self, *args, **kwargs):
        kwargs['type'] = 'unique'
        super().__init__(*args, **kwargs)
