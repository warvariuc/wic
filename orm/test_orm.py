"""
Tests for ORM
"""
__author__ = 'Victor Varvariuc <victor.varvariuc@gmail.com>'

import unittest
from datetime import date as Date, datetime as DateTime
from decimal import Decimal

import orm


#orm.sql_logger.setLevel(orm.logging.DEBUG)


def setUpModule():
    pass


def tearDownModule():
    pass


class TestModelAttr(unittest.TestCase):

    def test_model_attr(self):

        class ModelAttribute(orm.ModelAttr):
            sequence = 0

            def __init__(self):
                self.sequence = self.sequence + 1

        class ModelAttributeSubclass(ModelAttribute):
            def __init__(self):
                self.sequence = self.sequence + 1
                assert ModelAttribute is not super(ModelAttributeSubclass)
                super().__init__()

        class TestModel(orm.Model):
            attr1 = ModelAttribute()
            self.assertEqual(attr1.sequence, 0)
            attr2 = ModelAttributeSubclass()
            self.assertEqual(attr2.sequence, 0)

        self.assertEqual(TestModel.attr1.sequence, 1)
        self.assertEqual(TestModel.attr2.sequence, 2)


class TestModels(unittest.TestCase):

    def test_model_options(self):

        ok = False
        try:
            class TestModel(orm.Model):
                _meta = object()
        except orm.ModelError:
            ok = True
        self.assertTrue(ok, '`_meta` should be only instance of ModelOptions.')

        class TestModel1(orm.Model):
            field1 = orm.IntegerField()
            _meta = orm.ModelOptions(
                db_name='test1234',
            )

        self.assertIsInstance(TestModel1._meta, orm.ModelOptions)
        self.assertEqual(TestModel1._meta.db_name, 'test1234')
        # Model._meta.fields should be a {fieldName: Field, ...}
        self.assertIsInstance(TestModel1._meta.fields, dict)
        for fieldName, field in TestModel1._meta.fields.items():
            self.assertIsInstance(fieldName, str)
            self.assertIsInstance(field, orm.ModelField)

        class TestModel2(TestModel1):
            pass

        # _meta should be per Model, as each model contains its own fields, name, etc.
        self.assertIsNot(TestModel1._meta, TestModel2._meta)
        # as db_name was not given, it is calculated from Model name
        self.assertEqual(TestModel2._meta.db_name, 'test_model2')

        class TestModel3(orm.Model):
            last_name = orm.CharField(max_length=100)
            first_name = orm.CharField(max_length=100)
            # you can specify name of the fields in indexes
            _meta = orm.ModelOptions(
                db_indexes=orm.DbUnique('last_name', 'first_name'),
            )

        # test indexes in _meta
        self.assertIsInstance(TestModel3._meta.db_indexes, list)
        # primary index for id and our compound index
        self.assertEqual(len(TestModel3._meta.db_indexes), 2)
        for index in TestModel3._meta.db_indexes:
            self.assertIsInstance(index, orm.DbIndex)
            self.assertIsInstance(index.index_fields, list)

        self.assertEqual(len(TestModel3._meta.db_indexes[0].index_fields), 2)
        self.assertIsInstance(TestModel3._meta.db_indexes[0].index_fields[0].field, orm.CharField)
        self.assertIsInstance(TestModel3._meta.db_indexes[0].index_fields[1].field, orm.CharField)
        self.assertEqual(TestModel3._meta.db_indexes[0].type, 'unique')

        self.assertEqual(len(TestModel3._meta.db_indexes[1].index_fields), 1)
        self.assertIsInstance(TestModel3._meta.db_indexes[1].index_fields[0].field, orm.IdField)
        self.assertEqual(TestModel3._meta.db_indexes[1].type, 'primary')

        # you can specify fields in indexes
        class TestModel4(orm.Model):
            last_name = orm.CharField(max_length=100)
            first_name = orm.CharField(max_length=100)
            _meta = orm.ModelOptions(
                db_indexes=orm.DbUnique(last_name, first_name)
            )

        # you can specify more sophisticated indexes
        class TestModel5(orm.Model):
            name = orm.CharField(max_length=100)
            description = orm.TextField()
            birth_date = orm.DateField()
            _meta = orm.ModelOptions(
                db_indexes=(orm.DbIndex(orm.DbIndexField(name, 'desc'),
                            orm.DbIndexField(description, prefix_length=30)),
                            orm.DbIndex(birth_date))
            )

    def test_model_inheritance(self):

        class TestModel1(orm.Model):
            field1 = orm.CharField(max_length=100)

        class TestModel2(TestModel1):
            field1 = orm.IntegerField()
            field2 = orm.CharField(max_length=100)

        self.assertIsNot(TestModel2.field1, TestModel1.field1)
        self.assertIsInstance(TestModel1.field1.left, orm.CharField)
        self.assertIsInstance(TestModel2.field1.left, orm.IntegerField)
        self.assertIs(TestModel1.field1.left.model, TestModel1)
        self.assertIs(TestModel2.field1.left.model, TestModel2)


class TestModelFields(unittest.TestCase):

    def test_model_field_name(self):

        ok = False
        try:
            class TestModel1(orm.Model):
                _field = orm.IntegerField()
        except orm.ModelError:
            ok = True
        self.assertTrue(ok, 'Models should not accept fields with names starting with `_`')

        class TestModel2(orm.Model):
            integer_field = orm.IntegerField()

        # Model.field returns Expression, not Field
        self.assertIsInstance(TestModel2.integer_field, orm.FieldExpression)
        self.assertEqual(TestModel2.integer_field.left.name, 'integer_field')
        self.assertIsInstance(TestModel2.integer_field, orm.FieldExpression)

    def test_record_values(self):

        class TestModel2(orm.Model):
            integer_field = orm.IntegerField()
            record_field = orm.RelatedRecordField('self')

        class TestModel3(orm.Model):
            pass

        # create a record from the model
        record = TestModel2(None)
        record1 = TestModel2(None, id=101)
        record2 = TestModel2(None)
        record3 = TestModel3(None)

        # the assignment should fail, only integers should be accepted
        self.assertRaises(orm.RecordValueError, setattr, record, 'integer_field', '1')
        # try to assign a record of another model
        self.assertRaises(orm.RecordValueError, setattr, record, 'record_field', record3)

        record2.record_field = record
        self.assertEqual(record2.record_field, record)
        self.assertEqual(record2.record_field_id, None)

        record2.record_field_id = record1.id
        # no adapter was given, when the record was created
        self.assertRaises(orm.AdapterError, getattr, record2, 'record_field')
        self.assertEqual(record2.record_field_id, record1.id)

        record2.record_field = None
        self.assertEqual(record2.record_field, None)
        self.assertEqual(record2.record_field_id, None)

        record2.record_field_id = None
        self.assertEqual(record2.record_field, None)
        self.assertEqual(record2.record_field_id, None)


class TestExpressions(unittest.TestCase):

    def test_id_field(self):

        class TestModel1(orm.Model):
            field1 = orm.IntegerField()
            field2 = orm.CharField(max_length=100)

        class TestModel2(orm.Model):
            field3 = orm.RelatedRecordField(TestModel1)

        self.assertEqual(str(TestModel1.id == 1), '(test_model1.id = 1)')
        self.assertEqual(str(TestModel1.field1 == 1), '(test_model1.field1 = 1)')
        self.assertEqual(str(TestModel1.field2 == 1), "(test_model1.field2 = '1')")
        self.assertEqual(str(TestModel2.field3 == 3), "(test_model2.field3_id = 3)")


class TestModelsPostgresql(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
#        CREATE USER test WITH PASSWORD 'test';
#        CREATE DATABASE test;
#        GRANT ALL PRIVILEGES ON DATABASE test TO test;
        db = orm.connect('postgresql://test:test@localhost/test')
        cls.db = db

        # Drops all tables from the test database
        db.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type != 'VIEW' AND table_name NOT LIKE 'pg_ts_%%'
        """)
        for (table_name,) in db.cursor.fetchall():
            db.execute('DROP TABLE %s CASCADE' % table_name)

    @classmethod
    def tearDownClass(cls):
        cls.db.disconnect()

    def runTest(self):

        class Author(orm.Model):
            """Authors catalog
            """
            # `id` and `timestamp` fields already present
            last_name = orm.CharField(max_length=100, comment='Author\'s last name')
            first_name = orm.CharField(max_length=100, comment='Author\'s first name')
            created_at = orm.DateTimeField()

            _meta = orm.ModelOptions(
                db_name='authors',
                db_indexes=orm.DbUnique(last_name, first_name),
            )

        class Book(orm.Model):
            """Books catalog
            """
            name = orm.CharField(max_length=100, default='A very good book!!!')
            price = orm.DecimalField(max_digits=10, decimal_places=2, default='0.00',
                                     db_index=True)  # 2 decimal places
            author = orm.RelatedRecordField(Author, db_index=True)
            publication_date = orm.DateField()
            is_favorite = orm.BooleanField()

        db = self.db
        for model in (Author, Book):
            for query in db.get_create_table_query(model):
                db.execute(query)
        db.commit()

        # several ways creating new records
        # Model(db, (Model.field1, field1_value), (Model.field2, field2_value), ...)
        # Model(db, Model.field1(field1_value), Model.field2(field2_value), ...)
        # Model(db, (field1_name, field1_value), (field2_name, field2_value), ...)
        # Model(db, field1_name=field1_value, field2_name=field2_value, ...)

        author_data = (
            ('first_name', 'last_name'),
            ('Sam', 'Williams'),
            ('Steven', 'Levy'),
            ('Richard', 'Stallman'),
        )
        authors = []
        for data in author_data[1:]:
            data = dict(zip(author_data[0], data))
            author = Author.objects.create(db=db, **data)
            authors.append(author)

        book_data = (
            (Book.name, 'author', 'price', 'publication_date', 'is_favorite'),
            ("Free as in Freedom: Richard Stallman's Crusade for Free Software",
             authors[0], Decimal('9.55'), Date(2002, 3, 8), False),
            ("Hackers: Heroes of the Computer Revolution - 25th Anniversary Edition",
             authors[1], Decimal('14.95'), Date(2010, 3, 27), True),
            ("In The Plex: How Google Thinks, Works, and Shapes Our Lives",
             authors[1], Decimal('13.98'), Date(2011, 4, 12), False),
            ("Crypto: How the Code Rebels Beat the Government Saving Privacy in the Digital Age",
             authors[1], Decimal('23.00'), Date(2002, 1, 15), False),
            ("Книга с русским названием",
             None, Decimal('0.00'), Date(2000, 2, 29), True),
        )
        books = []
        for data in book_data[1:]:
            data = zip(book_data[0], data)
            book = Book.objects.create(db, *data)
            books.append(book)

        for book_id in range(1, 4):
            db.execute("""
                SELECT id, name, author_id, price, publication_date, is_favorite
                FROM book
                WHERE id = %s
            """, (book_id,))
            raw = db.cursor.fetchall()
            rows = db.select(*Book, where=(Book.id == book_id))
            book = Book.objects.get_one(db, id=book_id)
            field_data = (
                ('id', int),
                ('name', str),
                ('author_id', int),
                ('price', Decimal),
                ('publication_date', Date),
                ('is_favorite', bool),
            )
            for i, (field_name, value_type) in enumerate(field_data):
                field = getattr(Book, field_name)
                if isinstance(field, orm.model_fields._RecordId):
                    field = getattr(Book, field._record_field.name)
                # check value type
                # value in the DB
                self.assertIsInstance(raw[0][i], value_type)
                # value in Rows instance
                self.assertIsInstance(rows.value(0, field), value_type)
                # value in the record
                self.assertIsInstance(getattr(book, field_name), value_type)
                # check value equality
                if i == 0:
                    original_value = i
                else:
                    original_value = book_data[book_id][i - 1]
                    if isinstance(original_value, orm.Model):
                        original_value = original_value.id
                    self.assertEqual(original_value, raw[0][i])
                self.assertEqual(raw[0][i], rows.value(0, field))
                self.assertEqual(raw[0][i], getattr(book, field_name))

        # `where` in form of `(14 < Book.price < '15.00')` does not work as expected
        # as it is transformed by Python into `(14 < Book.price) and (Book.price < '15.00')`
        # resulting in `where = (Book.price < '15.00')`
        self.assertEqual(str((15 > Book.price > '14.00')), "(book.price > '14.00')")
        # SELECT query
        db.select(Book.id, from_=Book, where=(Book.price > '15'), limit=10)
        book = Book.objects.get_one(db, where=(Book.price > 15))

        # UPDATE query
        old_price = book.price
        new_title = 'A new title with raised price'
        last_query = db.get_last_query()
        db.update(
            Book.name(new_title),
            Book.price(Book.price + 1),
            where=(Book.id == book.id)
        )
        self.assertEqual(db._queries[-2], last_query)
        book = Book.objects.get_one(db, where=(Book.id == book.id))
        self.assertEqual(db._queries[-3], last_query)
        self.assertEqual(book.price, old_price + 1)
        self.assertEqual(book.name, new_title)

        # Authors count
        list(db.select(Author.COUNT()).dictresult())
        list(db.select(Author.first_name, Author.last_name).dictresult())

        # Selecting all fields for book with id=1
        rows = db.select(
            *(list(Book) + list(Author)),
            from_=[Book, orm.Join(Author, Book.author == Author.id)],
            where=(Book.id == 1)
        )
        self.assertIsInstance(rows.value(0, Book.id), int)

        assert issubclass(Author.RecordNotFound, orm.RecordNotFound)
        self.assertIsNot(Author.RecordNotFound, orm.RecordNotFound)
        # try to get non-existent record
        self.assertRaises(Author.RecordNotFound, Author.objects.get_one, db, id=12345)

        # New saved book with wrong author
        book = Book(db, ('name', "Just for Fun."), ('author', authors[0]), ('price', '11.20'),
                    ('publication_date', '2002-12-01'))
        book.author = Author.objects.get_one(db, id=3)  # Richard Stallman (?)
        book.save()

        # Created a new author, but did not save it
        author = Author(db, **dict(first_name='Linus', last_name='Torvalds'))
        self.assertIsNone(author.id)

        book.author = author  # No! It's Linus Torvalds the author of this book!
        # Assigned the book this new unsaved author
        # `book.author_id` should be None as the new author was not saved yet
        self.assertIsNone(book.author_id)
        # But `book.author` should be the one we assigned
        self.assertEqual(book.author, author)

        # Saved the new author. It should have now an id and a timestamp
        author.save()
        self.assertIsInstance(author.id, int)
        self.assertIsInstance(author.timestamp, DateTime)

        # After saving the new author `book.author_id` should have changed
        self.assertEqual(book.author_id, author.id)

        # Retreving book with id 1
        book = Book.objects.get_one(db, id=1)
        # Accessing `book.author` should automatically retrieve the author from the db:')
        last_query = db.get_last_query()
        book.author
        self.assertEqual(db._queries[-2], last_query)

        # Retreving book with id 1
        book = Book.objects.get_one(db, id=1, select_related=True)
        last_query = db.get_last_query()
        # Accessing `book.author` should NOT make a query to the db, as `select_related` was used
        book.author
        self.assertEqual(db.get_last_query(), last_query)