from pprint import pprint
from decimal import Decimal
import tempfile, os

import orm


class Authors(orm.Model):
    '''Authors catalog'''
    _tableId = 1
    # id field is already present 
    first_name = orm.StringField(maxLength= 100)
    last_name = orm.StringField(maxLength= 100)


class Books(orm.Model):
    '''Books catalog'''
    _tableId = 2
    # id field is already present 
    name = orm.StringField(maxLength= 100, defaultValue= 'a very good book!!!')
    price = orm.fields.DecimalField(totalDigits= 10, fractionDigits= 2, defaultValue= '0.00', index= True) # 2 decimal places
    author_id = orm.RecordIdField('Authors', index= True)
    publication_date = orm.StringField(maxLength= 10)
#    fan = orm.AnyRecordField(index=True) # None means that this field may contain reference to any other table in the DB

#    _indexes = [orm.Index([author, fan])] # additional and/or more sophisticated (f.e. composite) indexes

ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters

fd, filePath = tempfile.mkstemp(suffix= '.sqlite')
os.close(fd)

db = orm.connect('sqlite://' + filePath, ADAPTERS)

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

#print('\nCREATE TABLE query for Authors table:')
print(db.getCreateTableQuery(Authors))
for query in db.getCreateTableQuery(Authors).split('\n\n'): 
    db.execute(query)

#print('\nCREATE TABLE query for Books table:')
print(db.getCreateTableQuery(Books))
for query in db.getCreateTableQuery(Books).split('\n\n'): 
    db.execute(query)


#print(Authors.id.table, Books.id.table) # though id is inehrited from base model - you can see that now each table has its own id field

print('\nInserting authors:')
authorsData = (dict(first_name= 'Linus', last_name= 'Torvalds'),
           dict(first_name= 'Sam', last_name= 'Williams'),
           dict(first_name= 'Steven', last_name= 'Levy'),
           dict(first_name= 'Richard', last_name= 'Stallman')
)
authors = []
for data in authorsData:
    data['db'] = db
    author = Authors(**data)
    author.save() 
    print(author)
    authors.append(author)

print('\nInserting books:')
booksData = (dict(name= '''Free as in Freedom: Richard Stallman's Crusade for Free Software''', 
                  author_id= authors[1].id, price= '9.55', publication_date= '08.03.2002'),
             dict(name= '''Hackers: Heroes of the Computer Revolution - 25th Anniversary Edition''', 
                  author_id= authors[2].id, price= '14.95', publication_date= '27.03.2010'),
             dict(name= '''In The Plex: How Google Thinks, Works, and Shapes Our Lives''', 
                  author_id= authors[2].id, price= '13.98', publication_date= '12.04.2011'),
             dict(name= '''Just for Fun.''', 
                  author_id= authors[0].id, price= '11.21', publication_date= '01.12.2002'),
)
for data in booksData:
    data['db'] = db
    book = Books(**data)
    book.save() 
    print(book)



print('\nSELECT query:')
print(db._select(Books.id, where= (Books.price > 5), limit= (0, 10)))
pprint(db.select(Books.id, Books.name, where= (Books.price > 14), limit= (0, 10)))
print(Books.getOne(db, where= (Books.price > 14)))

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


#os.unlink(filePath) # delete the temporary db file