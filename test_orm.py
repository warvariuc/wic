#!/usr/bin/python3
"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

import pprint
from decimal import Decimal
import tempfile, os

import orm
from datetime import datetime as DateTime


class Author(orm.Model):
    """Author catalog"""
    # id field is already present 
    first_name = orm.CharField(max_length=100, comment='Author\'s first name')
    last_name = orm.CharField(max_length=100, comment='Author\'s last name')


class Book(orm.Model):
    """Book catalog"""
    # id field is already present 
    name = orm.CharField(max_length=100, default='a very good book!!!')
    price = orm.DecimalField(max_digits=10, decimal_places=2, default='0.00', index=True) # 2 decimal places
    author = orm.RecordField('Author', index=True)
    publication_date = orm.DateField()
    timestamp = orm.DateTimeField()
#    fan = orm.AnyRecordField(index=True) # None means that this field may contain reference to any other table in the DB

#    _indexes = [orm.Index([author, fan])] # additional and/or more sophisticated (f.e. composite) indexes

    def save(self): # let's override save
        self.timestamp = DateTime.now()
        super().save()

class CatalogModel(orm.Model):
    deleted = orm.BooleanField()

class Streets(CatalogModel):
    street_name = orm.CharField(max_length=50)


##################################################################
test = ('sqlite', 'mysql', 'postgresql')[0]
if test == 'sqlite':
    fd, filePath = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
#    db = orm.connect('sqlite://' + filePath)
    db = orm.connect('sqlite://:memory:')
elif test == 'mysql':
    db = orm.connect('mysql://root@localhost/test')
elif test == 'postgresql':
    db = orm.connect('postgresql://postgres@localhost/test')

db.execute('DROP TABLE IF EXISTS authors')
db.execute('DROP TABLE IF EXISTS books')

queries = db.get_create_table_query(Author)
print('\nGetting the CREATE TABLE query for table Author:\n', queries)
for _query in queries:
    db.execute(_query)


queries = db.get_create_table_query(Book)
print('\nGetting the CREATE TABLE query for table Book:\n', queries)
for _query in queries:
    db.execute(_query)

db.commit()

#print(Author.id.table, Book.id.table) # though id is inherited from base model - you can see that now each table has its own id field

authorsData = (
    dict(first_name='Sam', last_name='Williams'),
    dict(first_name='Steven', last_name='Levy'),
    dict(first_name='Richard', last_name='Stallman')
)
print('\nInserting authors:')
authors = []
for data in authorsData:
    author = Author(db=db, **data)
    author.save()
    print(author)
    authors.append(author)

booksData = (
    dict(name="Free as in Freedom: Richard Stallman's Crusade for Free Software",
         author=authors[0], price='9.55', publication_date='2002-03-08'),
    dict(name="Hackers: Heroes of the Computer Revolution - 25th Anniversary Edition",
         author=authors[1], price='14.95', publication_date='2010-03-27'),
    dict(name="In The Plex: How Google Thinks, Works, and Shapes Our Lives",
         author=authors[1], price='13.98', publication_date='2011-04-12'),
    dict(name="Crypto: How the Code Rebels Beat the Government Saving Privacy in the Digital Age",
         author=authors[1], price='23.00', publication_date='2002-01-15'),
)
print('\nInserting books:')
for data in booksData:
    book = Book(db=db, **data)
    book.save()
    print(book)



# where in form of `where = (14 < Book.price < '15.00')` do not work as expected
# as it is transformed by Python into `where = (14 < Book.price) and (Book.price < '15.00')` 
# making as result `where = (Book.price < '15.00')`
print('\nSELECT query:')
where = (15 > Book.price > '14.00')
print(db._select('id', from_=Book, where=where, limit=10))
print(db.select(Book.id, from_=Book, where=(Book.price > '15'), limit=10))
book = Book.objects.get_one(db, where=(Book.price > 15))
print("print(book, book.author)")
print(book, book.author)

print('\nUPDATE query:')
print(db._update(Book.name('_' + book.name), Book.price(Book.price + 1), where=(Book.id == book.id)))
db.update(Book.name('A new title with raised price'), Book.price(Book.price + 1), where=(Book.id == book.id))
print(Book.objects.get_one(db, where=(Book.id == book.id)))


print('\nAuthors count')
pprint.pprint(list(db.select(Author.COUNT()).dictresult()))
pprint.pprint(list(db.select(Author.first_name, Author.last_name).dictresult()))

print('\nSelecting one book with id=1:\n ', db.select('*', from_=[Book, orm.Join(Author, Book.author == Author.id)], where=(Book.id == 1)))

book = Book(db, ('name', "Just for Fun."), ('author', authors[0]), ('price', '11.20'),
            ('publication_date', '2002-12-01'))
book.author = Author.objects.get_one(db, id=3) # Richard Stallman (?)
book.save()
print('\nNew saved book with wrong author:\n ', book)

author = Author(db, **dict(first_name='Linus', last_name='Torvalds'))
print('\nCreated a new author, but did not save it:\n ', author)

book.author = author # No! It's Linus Tovalds the author of this book!
import ipdb; ipdb.set_trace()
print('\nAssigned the book this new unsaved author. book.author_id should be None as the new author is not saved yet:\n ', book)
print('But book.author should be the one we assigned:', book.author)

author.save()
print('\nSaved the new author. It should have now an id and a timestamp:\n ', author)

print('\nAfter saving the new author book.author_id should have changed:\n ', book)

print('\nRetreving book with id 1:')
book = Book.get_one(db, id=1, select_related=True)
print(book)
print('\nbook.author automatically retrives the author from the db:\n ', book.author)
#os.unlink(filePath) # delete the temporary db file
