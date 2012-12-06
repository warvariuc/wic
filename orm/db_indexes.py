from . import models


class DbIndexField():
    """Helper class for defining a field for index
    """
    def __init__(self, field, sort_order='asc', prefix_length=None):
        assert isinstance(field, model_fields.ModelField), 'Pass Field instances.'
        assert sort_order in ('asc', 'desc'), 'Sort order must be `asc` or `desc`.'
        assert isinstance(prefix_length, int) or prefix_length is None, \
            'Index prefix length must None or int.'
        self.field = field
        self.sort_order = sort_order
        self.prefix_length = prefix_length


class DbIndex(models.ModelAttr):
    """A database table index.
    """
    def __init__(self, *index_fields, type='index', name='', method=''):
        """
        @param index_fields: list of DbIndexField instances
        @param type: index, primary, unique, fulltext, spatial - specific fot the db
        @param method: btree, hash, gist, gin - specific fot the db
        """
#        print('Index.__init')
        assert index_fields, 'Need at least one Field or DbIndexField'

        model = None
        index_fields = list(index_fields)
        for i, index_field in enumerate(index_fields):
            if isinstance(index_field, str):  # field name passed
                index_field = self._model_attr_info.model.__dict__[index_field]
            if isinstance(index_field, model_fields.ModelField):  # a field
                index_field = DbIndexField(index_field)
                index_fields[i] = index_field
            else:
                assert isinstance(index_field, DbIndexField), \
                    'Pass a field name or Field/DbIndexField instances.'
            model = model or index_field.field.model
            assert index_field.field.model is model, 'Indexed fields should be from the same model!'

        if type is True:
            type = 'index'

        assert isinstance(type, str) and type

        if name == '':
            # if name was not given compose it from the names of all fields involved in the index
            for index_field in index_fields:
                name += index_field.field.name + '_'
            name += type  # and add index type at the end
        self.name = name

        self.index_fields = index_fields  # fields involved in this index
        self.type = type  # index type: unique, primary, etc.
        self.method = method  # if empty - will be used default for this type of DB

    def __str__(self):
        return '%s `%s` ON (%s) %s' % (self.type, self.name,
                                       ', '.join(str(index_field.field)
                                                 for index_field in self.index_fields),
                                       self.method)

#    def _copy(self, model):
#        """Create a copy of the index with copy of fields in the index with the given model."""
#        assert isinstance(model, models.ModelMeta), 'Pass a Model.'
#        index_fields = [index_field for index_field in self.index_fields]
#        return Index(index_fields, self.type, self.name, self.method, **self.other)


class DbUnique(DbIndex):
    """Convenience class for defining a unique index.
    """
    def __init__(self, *db_index_fields, name='', method=''):
        """
        @param index_fields: list of DbIndexField instances
        @param method: btree, hash, gist, gin - specific fot the db
        """
#        print('DbUnique.__init')
        super().__init__(*db_index_fields, type='unique', name=name, method=method)


from . import model_fields
