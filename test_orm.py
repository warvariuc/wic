"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

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
    author_id = orm.RecordIdField('Authors', index = True)
    publication_date = orm.fields.DateField()
    timestamp = orm.fields.DateTimeField()
#    fan = orm.AnyRecordField(index=True) # None means that this field may contain reference to any other table in the DB

#    _indexes = [orm.Index([author, fan])] # additional and/or more sophisticated (f.e. composite) indexes

    def save(self):
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

print('\nCREATE TABLE query for Authors table:')
print(db.getCreateTableQuery(Authors))

for query in db.getCreateTableQuery(Authors).split('\n\n'):
    db.execute(query)

print('\nCREATE TABLE query for Books table:')
print(db.getCreateTableQuery(Books))
for query in db.getCreateTableQuery(Books).split('\n\n'):
    db.execute(query)


#print(Authors.id.table, Books.id.table) # though id is inherited from base model - you can see that now each table has its own id field

print('\nInserting authors:')
authorsData = (
    dict(first_name = 'Sam', last_name = 'Williams'),
    dict(first_name = 'Steven', last_name = 'Levy'),
    dict(first_name = 'Richard', last_name = 'Stallman')
)
authors = []
for data in authorsData:
    author = Authors(db = db, **data)
    author.save()
    print(author)
    authors.append(author)

print('\nInserting books:')
booksData = (
    dict(name = "Free as in Freedom: Richard Stallman's Crusade for Free Software",
         author_id = authors[0].id, price = '9.55', publication_date = '2002-03-08'),
    dict(name = "Hackers: Heroes of the Computer Revolution - 25th Anniversary Edition",
         author_id = authors[1].id, price = '14.95', publication_date = '2010-03-27'),
    dict(name = "In The Plex: How Google Thinks, Works, and Shapes Our Lives",
         author_id = authors[1].id, price = '13.98', publication_date = '2011-04-12'),
    dict(name = "Crypto: How the Code Rebels Beat the Government Saving Privacy in the Digital Age",
         author_id = authors[1].id, price = '23.00', publication_date = '2002-01-15'),
)
for data in booksData:
    book = Books(db = db, **data)
    book.save()
    print(book)



# where in form of `where = (14 < Books.price < '15.00')` do not work as expected
# as it is transformed by Python into `where = (14 < Books.price) and (Books.price < '15.00')` 
# making as result `where = (Books.price < '15.00')`
print('\nSELECT query:')
print(db._select(Books.id, where = (15 > Books.price > '14.00'), limit = (0, 10)))
print(db.select(Books, where = (Books.price > '15'), limit = (0, 10)))
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


book = Books(db, ('name', "Just for Fun."), ('author_id', authors[0].id), ('price', '11.20'),
             ('publication_date','2002-12-01'))
print(author)
book.save()
print(author)

author = Authors(db, **dict(first_name = 'Linus', last_name = 'Torvalds'))
book.author = author

#os.unlink(filePath) # delete the temporary db file
