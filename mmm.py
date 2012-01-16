from pprint import pprint

import orm


ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters


db = orm.connect('mysql://root@localhost/test', ADAPTERS)

pprint(db.getTables())
columns = db.getColumns('authors')
print(columns)
pprint(list(map(str, columns)))