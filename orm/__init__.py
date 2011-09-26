import logging

logger = logging.getLogger("wic.orm")

from orm.fields import *
from orm.tables import Table
from orm.adapters import *

defaultDbAdapter = DbAdapter()

