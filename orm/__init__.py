import logging

logger = logging.getLogger("wic.orm")

from orm.fields import IdField, StringField, DecimalFieldI, ReferenceField
from orm.tables import Table
from orm.adapters import SqliteAdapter, DbAdapter as _DbAdapter

defaultDbAdapter = _DbAdapter()
