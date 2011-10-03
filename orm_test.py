from pprint import pprint

import orm


class Authors(orm.Table):
    ''''''
    _tableId = 1
    # id field is already present 
    first_name = orm.StringField(maxLength=100)
    last_name = orm.StringField(maxLength=100)


class Books(orm.Table):
    ''''''
    _tableId = 2
    # id field is already present 
    name = orm.StringField(maxLength=100, defaultValue='a very good book!!!')
    price = orm.DecimalFieldI(maxDigits=10, decimalPlaces=2, defaultValue='0.00') # 2 decimal places
    old_price = orm.DecimalFieldI(maxDigits=10, decimalPlaces=2, defaultValue='0.00') # 2 decimal places
    author = orm.ItemField(Authors)
    fan = orm.fields.AnyItemField() # None means that this field may contain reference to any other table in the DB



ADAPTERS = dict(sqlite=orm.SqliteAdapter) # available adapters

def connect(uri, makeDefault=True):
    '''Search for suitable adapter by protocol'''
    for dbType, dbAdapterClass in ADAPTERS.items(): 
        uriStart = dbType + '://'
        if uri.startswith(uriStart):
            dbAdapter = dbAdapterClass(uri[len(uriStart):])
            if makeDefault:
                global defaultDbAdapter
                defaultDbAdapter = dbAdapter
            return dbAdapter



#db = connect('sqlite://conf/databases/test.sqlite')
#print(Authors.id.table, Books.id.table) # though id is inehrited from base model - you can see that now each table has its personal id field

author = Authors(first_name='Linus', last_name='Torvalds', id=1) # new item in books catalog 

book = Books(name='Just for Fun: The Story of an Accidental Revolutionary',
                 price='14.99') # new item in books catalog 
print(book.id, book.name, book.price) # None - the book wasn't saved yet
print(((Books.price != None) & (Books.price > Books.old_price))._render())

where = ((Books.author == author) | ((1 <= Books.id) & (Books.price > 9.99)))
print(where._render())

print(((1 < Books.price) & (Books.price.IN(3, 4, 5)))._render())

print(((Books.fan == author) | ((1 <= Books.id) & (Books.price > 9.99)))._render())

#book.author = Authors.load(1)
#book.save(adapter)
#bookId = book.id
#print(bookId)

#book = Books.load(bookId)
#book.price -= Decimal('3.75')
#book.save()
#book.lock(False) # unlock table record

#books = Books((Books.id >= bookId) & (Books.price >= Decimal('0.01'))).select(adapter)
#print(books[0])

#Persons(Persons.name.like('J%')).update(name='James')
#>>> 1 # number of affected rows

#Persons(Persons.id.in(1, 1001)).select()
#>>> 1 # number of affected rows

### delete records by query
#Persons(Persons.name.lower() == 'jim').delete()


