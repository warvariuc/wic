class DbError(Exception):
    """Base exception on operations with DB."""

class ConnectionError(DbError):
    """"""

class RecordNotFound(DbError):
    """"""

class TooManyRecords(DbError):
    """Got too many records (usually where one was expected - got more than one)."""
