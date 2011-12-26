class DbError(Exception):
    """Base exception on operations with DB."""

class ConnectionError(DbError):
    """"""

class OrmError(Exception):
    """Base exception for ORM errors"""

class RecordNotFound(OrmError):
    """"""

class TooManyRecords(OrmError):
    """Got too many records (usually where one was expected - got more than one)."""

class SaveError(OrmError):
    """Record save error."""
