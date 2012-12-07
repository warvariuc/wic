"""QueryManager methods are intended to do "table-wide" things.
"""
from . import models


def _prepare_record_values(model, row):
    """Prepare values to be passed to Model instance init.
    """
    data = {}
    for i, field in enumerate(model._meta.fields.values()):
        field_name = field.name
        if isinstance(field, model_fields.RelatedRecordField):
            field_name = field._name
        data[field_name] = row[i]
    return data


class QueryManager(models.ModelAttr):
    """Through this manager a Model interfaces with a database.
    """
    def __init__(self):
        # URLs of database adapters the model was successfully checked against
        self.model = self._model_attr_info.model
        self._checked_dbs = set()

    def __get__(self, record, model):
        assert model is self.model
        if record is not None:
            # called as an instance attribute
            raise AttributeError('Query manager is not accessible via records (Model instances)')
        # called as a class attribute
        if model._meta.abstract:
            raise exceptions.ModelError('You cannot use query manager on abstract models.')
        return self

    def check_table(self, db):
        """Check if corresponding table for this model exists in the db and has all necessary
        columns. Add check_table call in very model method that uses a db.
        """
        if not isinstance(db, adapters.GenericAdapter):
            raise exceptions.AdapterError('Need a database adapter.')
        if db.url in self._checked_dbs:
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
        self._checked_dbs.add(db.url)

    def create(self, db, *args, **kwargs):
        record = self.model(db, *args, **kwargs)
        record.save()
        return record

    def get_one(self, db, where=None, id=None, select_related=False):
        """Get a single record which falls under the given condition.
        @param db: db adapter to use to getting the record
        @param where: expression to use for filter
        @param id: id of the record, if you want to fetch one record by its id
        """
        if id:
            where = (self.model.id == id)

        records = list(self.model.objects.get(db, where, limit=2,
                                              select_related=select_related))
        if not records:  # not found
            raise self.model.RecordNotFound(db.render(where))
        if len(records) > 1:
            raise self.model.MultipleRecordsFound
        return records[0]

    def get(self, db, where, orderby=False, limit=False, select_related=False):
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
        fields = list(model)
        from_ = [model]
        record_fields = []  # list of RelatedRecordField fields
        if select_related:
            for i, field_expression in enumerate(model):
                field = field_expression.left
                if isinstance(field, model_fields.RelatedRecordField):
                    record_fields.append((i, field))
                    fields.extend(field.related_model)
                    # left join
                    from_.append(models.LeftJoin(field.related_model,
                                                 on=(field_expression == field.related_model.id)))

        #print(db._select(*fields, from_ = from_, where = where, orderby = orderby, limit = limit))
        # retrieve the values from the DB
        rows = db.select(*fields, from_=from_, where=where, orderby=orderby, limit=limit)

        for row in rows:
            # create the record from the values
            data = _prepare_record_values(model, row)
            record = model(db, **data)

            if select_related:
                field_start = len(model)
                for i, record_field in record_fields:
                    related_model = record_field.related_model
                    field_end = field_start + len(related_model)
                    if row[i] is None:
                        related_record = None
                    else:
                        # if related_record.id is None: # missing record !!! integrity error
                        data = _prepare_record_values(related_model, row[field_start:field_end])
                        related_record = related_model(db, **data)
                    setattr(record, record_field.name, related_record)
                    field_start = field_end
            yield record

    def delete(self, db, where):
        """Delete records in the table which fall under the given condition.
        """
        self.check_table(db)
        db.delete(self, where=where)
        db.commit()

    def get_count(self, db, where=None):
        """Request number of records in the table.
        """
        self.check_table(db)
        model = self.model
        count_expression = model.COUNT(where)
        count = db.select(count_expression, from_=model).value(0, count_expression)
        logger.debug('Model.get_count(%s, db= %s, where= %s) = %s'
                     % (model, db, where, count))
        return count

    def _handle_table_missing(self, db):
        """Default implementation of situation when upon checking there was not found the table
        corresponding to this model in the db.
        """
        raise exceptions.TableMissing(db, self.model)


from . import adapters, model_fields, exceptions, logger
