import orm
from orm import signals, logger, exceptions


class QueryManager():
    """
    Through this manager a Model interfaces with a database.
    """
    def __init__(self, *args, **kwargs):
        model = kwargs.pop('model', None)
        if not model:  # model is passed by the Model metaclass
            self._initArgs = args
            self._initKwwargs = kwargs
            return

        # model was passed by Model metaclass
        assert orm.isModel(model)
        self.model = model
        self._init_(*self._initArgs, **self._initKwargs)  # real initialization

    def _init_(self):
        # URIs of database adapters the model was successfully checked against
        self._checkedDbs = set()

    def checkTable(self, db):
        """Check if corresponding table for this model exists in the db and has all necessary columns.
        Add checkTable call in very model method that uses a db.
        """
        assert isinstance(db, orm.GenericAdapter), 'Need a database adapter'
        if db.uri in self._checkedDbs:
            # this db was already checked
            return
        model = self.model
        logger.debug('Model.checkTable: checking db table %s' % model)
        tableName = model._name
        if tableName not in db.getTables():
            self._handleTableMissing(db)
#        import pprint
        modelColumns = {field.column.name: field.column for field in model}
        dbColumns = db.getColumns(tableName)
#        logger.debug(pprint.pformat(list(column.str() for column in dbColumns.values())))
#        logger.debug(pprint.pformat(list(column.str() for column in modelColumns.values())))
        for columnName, column in modelColumns.items():
            dbColumn = dbColumns.pop(columnName, None)
            if not dbColumn:  # model column is not found in the db
                print('Column in the db not found: %s' % column.str())
        logger.debug('CREATE TABLE query:\n%s' % db.getCreateTableQuery(model))
        self._checkedDbs.add(db.uri)

    def getOne(self, db, where = None, id = None, select_related = False):
        """Get a single record which falls under the given condition.
        @param db: db adapter to use to getting the record
        @param where: expression to use for filter
        @param id: id of the record, if you want to fetch one record by its id
        """
        self.checkTable(db)

        if id:
            where = (self.model.id == id)

        records = list(self.model.get(db, where, limit = 2, select_related = select_related))
        if not records:  # not found
            raise orm.RecordNotFound(db.render(where))
        if len(records) == 1:
            return records[0]
        raise orm.TooManyRecords

    def get(self, db, where, orderby = False, limit = False, select_related = False):
        """Get records from this table which fall under the given condition.
        @param db: adapter to use
        @param where: condition to filter
        @param order: list of field to sort by
        @param limit: tuple (from, to)
        @param select_related: whether to retrieve objects related by foreign keys in the same query
        """
        model = self.model
        logger.debug("Model.get('%s', db= %s, where= %s, limit= %s)" % (model, db, where, limit))
        self.checkTable(db)
        orderby = orderby or model._ordering  # use default table ordering if no ordering passed
        fields = list(model)
        from_ = [model]
        recordFields = []
        if select_related:
            for i, field in enumerate(model):
                if isinstance(field, orm.RecordField):
                    recordFields.append((i, field))
                    fields.extend(field.referTable)
                    from_.append(orm.LeftJoin(field.referTable, field == field.referTable.id))
        #print(db._select(*fields, from_ = from_, where = where, orderby = orderby, limit = limit))
        rows = db.select(*fields, from_ = from_, where = where, orderby = orderby, limit = limit)
        for row in rows:
            record = model(db, *zip(model, row))
            if select_related:
                fieldOffset = len(model)
                for i, recordField in recordFields:
                    referTable = recordField.referTable
                    if row[i] is None:
                        referRecord = None
                    else:
                        # if referRecord.id is None: # missing record !!! integrity error
                        referRecord = referTable(db, *zip(referTable, row[fieldOffset:]))
                    setattr(record, recordField.name, referRecord)
                    fieldOffset += len(referTable)
            yield record

    def delete(self, db, where):
        """Delete records in this table which fall under the given condition.
        """
        self.checkTable(db)
        db.delete(self, where = where)
        db.commit()

    def getCount(self, db, where = None):
        """Request number of records in this table.
        """
        model = self.model
        model.checkTable(db)
        count = model.COUNT(where)
        count = db.select(count, from_ = model).value(0, count)
        logger.debug('Model.getCount(%s, db= %s, where= %s) = %s' % (model, db, where, count))
        return count

    def _handleTableMissing(self, db):
        """Default implementation of situation when upon checking
        there was not found the table corresponding to this model in the db.
        """
        raise exceptions.TableMissing(db, self.model)