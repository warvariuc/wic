import logging

logger = logging.getLogger("wic.orm")

from orm.fields import IdField, StringField, DecimalFieldI, ReferField
from orm.tables import Table
from orm.adapters import SqliteAdapter, Adapter as _Adapter

defaultAdapter = _Adapter()
