from . import models


class QueryManager(models.ModelAttr):
    """Through this manager a Model interfaces with a database.
    """
    def __init__(self):
        # URIs of database adapters the model was successfully checked against
        self.model = self._model_attr_info.model
        self._checked_dbs = set()

    def check_table(self, db):
        """Check if corresponding table for this model exists in the db and has all necessary columns.
        Add check_table call in very model method that uses a db.
        """
        assert isinstance(db, adapters.GenericAdapter), 'Need a database adapter'
        if db.uri in self._checked_dbs:
            # this db was already checked
            return
        model = self.model
        logger.debug('Model.check_table: checking db table %s' % model)
        table_name = model._meta.db_name
        if table_name not in db.get_tables():
            self._handle_table_missing(db)
        model_columns = {field.column.name: field.column for field in model._meta.fields.values()}
        db_columns = db.get_columns(table_name)
#        logger.debug(pprint.pformat(list(column.str() for column in dbColumns.values())))
#        logger.debug(pprint.pformat(list(column.str() for column in modelColumns.values())))
        for column_name, column in model_columns.items():
            db_column = db_columns.pop(column_name, None)
            if not db_column:  # model column is not found in the db
                print('Column in the db not found: %s' % column.str())
        logger.debug('CREATE TABLE query:\n%s' % db.get_create_table_query(model))
        self._checked_dbs.add(db.uri)

    def create(self, db, *args, **kwargs):
        record = self.model(db, *args, **kwargs)
        record.save()
        return record

    def get_one(self, db, where = None, id = None, select_related = False):
        """Get a single record which falls under the given condition.
        @param db: db adapter to use to getting the record
        @param where: expression to use for filter
        @param id: id of the record, if you want to fetch one record by its id
        """
        self.check_table(db)

        if id:
            where = (self.model.id == id)

        records = list(self.model.objects.get(db, where, limit = 2,
                                              select_related = select_related))
        if not records:  # not found
            raise exceptions.RecordNotFound(db.render(where))
        if len(records) == 1:
            return records[0]
        raise exceptions.TooManyRecords

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
        self.check_table(db)
        orderby = orderby or model._meta.ordering  # use default table ordering if no ordering given
        fields_ = list(model)
        from_ = [model]
        record_fields = []
        if select_related:
            for i, field in enumerate(model):
                if isinstance(field, fields.RecordField):
                    record_fields.append((i, field))
                    fields_.extend(field.refer_model)
                    from_.append(models.LeftJoin(field.refer_model, field == field.refer_model.id))
        #print(db._select(*fields, from_ = from_, where = where, orderby = orderby, limit = limit))
        rows = db.select(*fields_, from_ = from_, where = where, orderby = orderby, limit = limit)
        for row in rows:
            record = model(db, *zip(model, row))
            if select_related:
                field_offset = len(model)
                for i, record_field in record_fields:
                    refer_model = record_field.refer_model
                    if row[i] is None:
                        refer_record = None
                    else:
                        # if referRecord.id is None: # missing record !!! integrity error
                        refer_record = refer_model(db, *zip(refer_model, row[field_offset:]))
                    setattr(record, record_field.name, refer_record)
                    field_offset += len(refer_model)
            yield record

    def delete(self, db, where):
        """Delete records in this table which fall under the given condition.
        """
        self.check_table(db)
        db.delete(self, where = where)
        db.commit()

    def get_count(self, db, where = None):
        """Request number of records in this table.
        """
        model = self.model
        model.check_table(db)
        count = model.COUNT(where)
        count = db.select(count, from_ = model).value(0, count)
        logger.debug('Model.get_count(%s, db= %s, where= %s) = %s' % (model, db, where, count))
        return count

    def _handle_table_missing(self, db):
        """Default implementation of situation when upon checking
        there was not found the table corresponding to this model in the db.
        """
        raise exceptions.TableMissing(db, self.model)

from . import adapters, fields, exceptions, signals, logger
