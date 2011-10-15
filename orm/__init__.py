import logging

logger = logging.getLogger("wic.orm")

_fieldsCount = 0 # will be used to track the original definition order of the fields 

from orm.fields import IdField, StringField, DecimalFieldI, RecordIdField, AnyRecordIdField
from orm.tables import Table, Record, Index
from orm.adapters import SqliteAdapter, MysqlAdapter, Adapter as _Adapter

defaultAdapter = _Adapter()
