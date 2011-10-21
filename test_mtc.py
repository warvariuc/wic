from pprint import pprint

import orm


class Regions(orm.Table):
    _tableId = 1
    region_name = orm.StringField(maxLength=60)
    region_type_name = orm.StringField(maxLength=20)


ADAPTERS = dict(sqlite=orm.SqliteAdapter, mysql=orm.MysqlAdapter) # available adapters


dbAdapter = orm.connect('sqlite://../mtc.sqlite', ADAPTERS)

#print('\nBooks indexes:')
#for index in Books._indexes:
#    print(' ', index)
#    
#print('\nTextual representation of a field:')
#print(Books.author)
#
print('\nRegions table fields:')
for field in Regions:
    print(' ', field)
#
#print('\nTextual representation of a Table:')
#print(Books)
#
#print('\nCREATE TABLE query for Authors table:')
#print(Authors.getCreateStatement(orm.defaultAdapter))
#
#print('\nCREATE TABLE query for Books table:')
#print(Books.getCreateStatement(orm.defaultAdapter))


#print('\nTextual representation of an item:')
#print(book)
#
#print(book.id, book.name, book.price) # None - the book wasn't saved yet

#print(dbAdapter._select((Books.price > 5), limitby=(0,10)))
pprint(dbAdapter._select((Regions.id != None), orderby=[Regions.region_type_name, -Regions.region_name], limitby=(0,10)))
