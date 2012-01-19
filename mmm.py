from pprint import pprint

import orm




#db = orm.connect('mysql://root@localhost/test')
#pprint(db.getTables())
#columns = db.getColumns('authors')
#print(columns)
#pprint(list(map(str, columns)))


db = orm.connect('sqlite:///tmp/tmpwd1jj9.sqlite')
pprint(db.getTables())
columns = db.getColumns('books')
print(columns)
pprint(list(map(str, columns)))
