import logging

logger = logging.getLogger("wic.orm")

from orm.fields import IdField, StringField, DecimalFieldI, ItemField, AnyItemField
from orm.catalogs import Catalog
from orm.adapters import SqliteAdapter, Adapter as _Adapter

defaultAdapter = _Adapter()
