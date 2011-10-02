import logging

logger = logging.getLogger("wic.orm")

from orm.fields import IdField, StringField, DecimalFieldI, ReferenceField
from orm.tables import Table
from orm.adapters import SqliteAdapter, Adapter as _Adapter

defaultDbAdapter = _Adapter()
