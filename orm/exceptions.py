class DbError(Exception):
    """Base exception on operations with DB."""

class ConnectionError(DbError):
    """"""

class OrmError(Exception):
    """Base exception for ORM errors"""

class AdapterNotFound(OrmError):
    """Suitable db adapter no found for the specified protocol."""

class RecordNotFound(OrmError):
    """"""

class TooManyRecords(OrmError):
    """Got too many records (usually where one was expected - got more than one)."""

class SaveError(OrmError):
    """Record save error."""

class ModelError(OrmError):
    """A problem with a model."""

class TableError(OrmError):
    """A problem with a db table structure."""


class TableMissing(TableError):
    
    def __init__(self, db, model):
        """A corresponding table for a model was not found in the db.
        @param db: which db [adapter]
        @param model: which model 
        """
        self.db = db
        self.model = model

    def __str__(self):
        return 'Table `%(model)s` does not exist in database `%(db)s`' % self.__dict__


class ColumnError(TableError):
    """A problem with a db table column structure."""

class ColumnMissing(TableError):
    """A column for a model is missing in the corresponding db table."""

