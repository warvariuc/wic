'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''

from pprint import pprint
from decimal import Decimal
import tempfile, os

import orm
from datetime import datetime as DateTime


class Authors(orm.Model):
    '''Authors catalog'''
    _tableId = 1
    # id field is already present 
    first_name = orm.CharField(maxLength= 100)
    last_name = orm.CharField(maxLength= 100)


class Books(orm.Model):
    '''Books catalog'''
    _tableId = 2
    # id field is already present 
    name = orm.CharField(maxLength= 100, defaultValue= 'a very good book!!!')
    price = orm.fields.DecimalField(maxDigits= 10, fractionDigits= 2, defaultValue= '0.00', index= True) # 2 decimal places
    author_id = orm.RecordIdField('Authors', index= True)
    publication_date = orm.fields.DateField(defaultValue= None)
    timestamp = orm.fields.DateTimeField(defaultValue= None)
#    fan = orm.AnyRecordField(index=True) # None means that this field may contain reference to any other table in the DB

#    _indexes = [orm.Index([author, fan])] # additional and/or more sophisticated (f.e. composite) indexes

    def save(self):
        self.timestamp = DateTime.now()
        super().save()
    

ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters

fd, filePath = tempfile.mkstemp(suffix= '.sqlite')
os.close(fd)
db = orm.connect('sqlite://' + filePath, ADAPTERS)
#db = orm.connect('mysql://root@localhost/test', ADAPTERS)
#db.execute('DROP TABLE IF EXISTS authors')
#db.execute('DROP TABLE IF EXISTS books')

#print('\nCREATE TABLE query for Authors table:')
print(db.getCreateTableQuery(Authors))
for query in db.getCreateTableQuery(Authors).split('\n\n'): 
    db.execute(query)

#print('\nCREATE TABLE query for Books table:')
print(db.getCreateTableQuery(Books))
for query in db.getCreateTableQuery(Books).split('\n\n'): 
    db.execute(query)


#print(Authors.id.table, Books.id.table) # though id is inherited from base model - you can see that now each table has its own id field

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
                  author_id= authors[1]._id, price= '9.55', publication_date= '2002-03-08'),
             dict(name= '''Hackers: Heroes of the Computer Revolution - 25th Anniversary Edition''', 
                  author_id= authors[2]._id, price= '14.95', publication_date= '2010-03-27'),
             dict(name= '''In The Plex: How Google Thinks, Works, and Shapes Our Lives''', 
                  author_id= authors[2]._id, price= '13.98', publication_date= '2011-04-12'),
             dict(name= '''Just for Fun.''', 
                  author_id= authors[0]._id, price= '11.20', publication_date= '2002-12-01'),
)
for data in booksData:
    data['db'] = db
    book = Books(**data)
    book.save() 
    print(book)



print('\nSELECT query:')
print(db._select(Books._id, where= (Books.price > '14.00'), limit= (0, 10)))
pprint(db.select(Books, where= (Books.price > '14'), limit= (0, 10)))
book = Books.getOne(db, where= (Books.price > 14))
print(book)


#os.unlink(filePath) # delete the temporary db file