"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

import pprint
from decimal import Decimal
import tempfile, os

import orm
from datetime import datetime as DateTime


class Authors(orm.Model):
    """Authors catalog"""
    _tableId = 1
    # id field is already present 
    first_name = orm.CharField(maxLength = 100)
    last_name = orm.CharField(maxLength = 100)


class Books(orm.Model):
    """Books catalog"""
    _tableId = 2
    # id field is already present 
    name = orm.CharField(maxLength = 100, default = 'a very good book!!!')
    price = orm.fields.DecimalField(maxDigits = 10, fractionDigits = 2, default = '0.00', index = True) # 2 decimal places
    author = orm.RecordField('Authors', index = True)
    publication_date = orm.fields.DateField()
    timestamp = orm.fields.DateTimeField()
#    fan = orm.AnyRecordField(index=True) # None means that this field may contain reference to any other table in the DB

#    _indexes = [orm.Index([author, fan])] # additional and/or more sophisticated (f.e. composite) indexes

    def save(self): # lte's override save
        self.timestamp = DateTime.now()
        super().save()

class CatalogModel(orm.Model):
    deleted = orm.BooleanField()

class Streets(CatalogModel):
    street_name = orm.CharField(maxLength = 50)


#fd, filePath = tempfile.mkstemp(suffix='.sqlite')
#os.close(fd)
#db = orm.connect('sqlite://' + filePath)
db = orm.connect('sqlite://:memory:')
#db = orm.connect('mysql://root@localhost/test')
#db.execute('DROP TABLE IF EXISTS authors')
#db.execute('DROP TABLE IF EXISTS books')

query = db.getCreateTableQuery(Authors)
print('\nGetting the CREATE TABLE query for table Authors:\n', query)
for _query in query.split('\n\n'):
    db.execute(_query)


query = db.getCreateTableQuery(Books)
print('\nGetting the CREATE TABLE query for table Books:\n', query)
for _query in query.split('\n\n'):
    db.execute(_query)


#print(Authors.id.table, Books.id.table) # though id is inherited from base model - you can see that now each table has its own id field

authorsData = (
    dict(first_name = 'Sam', last_name = 'Williams'),
    dict(first_name = 'Steven', last_name = 'Levy'),
    dict(first_name = 'Richard', last_name = 'Stallman')
)
print('\nInserting authors:')
authors = []
for data in authorsData:
    author = Authors(db = db, **data)
    author.save()
    print(author)
    authors.append(author)

booksData = (
    dict(name = "Free as in Freedom: Richard Stallman's Crusade for Free Software",
         author = authors[0].id, price = '9.55', publication_date = '2002-03-08'),
    dict(name = "Hackers: Heroes of the Computer Revolution - 25th Anniversary Edition",
         author = authors[1], price = '14.95', publication_date = '2010-03-27'),
    dict(name = "In The Plex: How Google Thinks, Works, and Shapes Our Lives",
         author = authors[1], price = '13.98', publication_date = '2011-04-12'),
    dict(name = "Crypto: How the Code Rebels Beat the Government Saving Privacy in the Digital Age",
         author = authors[1], price = '23.00', publication_date = '2002-01-15'),
)
print('\nInserting books:')
for data in booksData:
    book = Books(db = db, **data)
    book.save()
    print(book)



# where in form of `where = (14 < Books.price < '15.00')` do not work as expected
# as it is transformed by Python into `where = (14 < Books.price) and (Books.price < '15.00')` 
# making as result `where = (Books.price < '15.00')`
print('\nSELECT query:')
print(db._select('id', from_ = Books, where = (15 > Books.price > '14.00'), limit = 10))
print(db.select(Books.id, from_ = Books, where = (Books.price > '15'), limit = 10))
book = Books.getOne(db, where = (Books.price > 15))
print("print(book, book.author)")
print(book, book.author)

print('\nUPDATE query:')
print(db._update(Books.name('_' + book.name), Books.price(Books.price + 1), where = (Books.id == book.id)))
db.update(Books.name('A new title with raised price'), Books.price(Books.price + 1), where = (Books.id == book.id))
print(Books.getOne(db, where = (Books.id == book.id)))


print('\nAuthors count')
pprint.pprint(list(db.select(Authors.first_name, Authors.COUNT()).dictresult()))
pprint.pprint(list(db.select(Authors.first_name, Authors.last_name).dictresult()))

print('\nSelecting one book with id=1:\n ', db.select('*', from_ = [Books, orm.Join(Authors, Books.author == Authors.id)], where = (Books.id == 1)))

book = Books(db, ('name', "Just for Fun."), ('author', authors[0]), ('price', '11.20'),
             ('publication_date', '2002-12-01'))
book.author = Authors.getOne(db, id = 3) # Richard Stallman (?)
book.save()
print('\nNew saved book with wrong author:\n ', book)

author = Authors(db, **dict(first_name = 'Linus', last_name = 'Torvalds'))
print('\nCreated a new author, but did not save it:\n ', author)

book.author = author # No! It's Linus Tovalds the author of this book!
print('\nAssigned the book this new unsaved author. book.author_id should be None as the new author is not saved yet:\n ', book)
print('But book.author should be the one we assigned:', book.author)

author.save()
print('\nSaved the new author. It should have now an id and a timestamp:\n ', author)

print('\nAfter saving the new author book.author_id should have changed:\n ', book)

print('\nRetreving book with id 1:')
book = Books.getOne(db, id = 1, select_related = True)
print(book)
print('\nbook.author automatically retrives the author from the db:\n ', book.author)
#os.unlink(filePath) # delete the temporary db file
