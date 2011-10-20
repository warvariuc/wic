from pprint import pprint

import orm


class Authors(orm.Table):
    '''Authors catalog'''
    _tableId = 1
    # id field is already present 
    first_name = orm.StringField(maxLength=100)
    last_name = orm.StringField(maxLength=100)


class Books(orm.Table):
    '''Books catalog'''
    _tableId = 2
    # id field is already present 
    name = orm.StringField(maxLength=100, defaultValue='a very good book!!!')
    price = orm.DecimalFieldI(maxDigits=10, decimalPlaces=2, defaultValue='0.00', index=True) # 2 decimal places
    old_price = orm.DecimalFieldI(maxDigits=10, decimalPlaces=2, defaultValue='0.00') # 2 decimal places
    author = orm.RecordIdField('Authors', index=True)
    fan = orm.fields.RecordIdField(None, index=True) # None means that this field may contain reference to any other table in the DB

#    _indexes = [orm.Index([author, fan])] # additional and/or more sophisticated (f.e. composite) indexes

ADAPTERS = dict(sqlite=orm.SqliteAdapter, mysql=orm.MysqlAdapter) # available adapters

def connect(uri):
    '''Search for suitable adapter by protocol'''
    for dbType, dbAdapterClass in ADAPTERS.items(): 
        uriStart = dbType + '://'
        if uri.startswith(uriStart):
            dbAdapter = dbAdapterClass(uri[len(uriStart):])
            return dbAdapter



dbAdapter = connect('mysql://conf/databases/test.sqlite')
orm.defaultAdapter = dbAdapter

#print('\nBooks indexes:')
#for index in Books._indexes:
#    print(' ', index)
#    
#print('\nTextual representation of a field:')
#print(Books.author)
#
#print('\nBooks fields:')
#for i in Books:
#    print(' ', i)
#
#print('\nTextual representation of a Table:')
#print(Books)
#
#print('\nCREATE TABLE query for Authors table:')
#print(Authors.getCreateStatement(orm.defaultAdapter))
#
#print('\nCREATE TABLE query for Books table:')
#print(Books.getCreateStatement(orm.defaultAdapter))


#print(Authors.id.table, Books.id.table) # though id is inehrited from base model - you can see that now each table has its personal id field

author = Authors.new(dbAdapter, first_name='Linus', last_name='Torvalds', id=1) # new item in books catalog 

book = Books.new(dbAdapter, name='Just for Fun: The Story of an Accidental Revolutionary',
                 price='14.99') # new item in books catalog 

#print('\nA Books item values:')
#for i in book:
#    print(' ', i)

print('\nTextual representation of an item:')
print(book)

print(book.id, book.name, book.price) # None - the book wasn't saved yet
print(((Books.price != None) & (Books.price > Books.old_price))._render())

where = ((Books.author == author) | ((1 <= Books.id) & (Books.price > 9.99)))
print(where._render())

print(((1 < Books.price) & (Books.price.IN(3, 4, 5)))._render())

print('\nSELECT query:')
print(dbAdapter._select((Books.price > 5), limitby=(0,10)))

#print(Books(Books.price > 5).select(dbAdapter, join=[Authors]))

#print(Books((Books.fan == author) | ((1 <= Books.id) & (Books.price > 9.99)))._render())

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


