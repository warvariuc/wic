"""
Unit tests for ORM
"""
__author__ = 'Victor Varvariuc <victor.varvariuc@gmail.com>'

import sys
import os
import unittest

import orm


def setUpModule():
    pass


def tearDownModule():
    pass


class TestModelAttr(unittest.TestCase):

    def testModelAttr(self):

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



#
#class TestModelsSqlite(unittest.TestCase):
#    @classmethod
#    def setUpClass(cls):
#        cls.db = orm.connect('sqlite://:memory:')
#
#    @classmethod
#    def tearDownClass(cls):
#        cls.db = None  # disconnect?    
#
#    def test_create_table_from_model(self):
#
#        query = self.db.get_create_table_query(TestModel)
#        for _query in query.split('\n\n'):
#            self.db.execute(_query)


class TestModelsPostgresql(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
#        CREATE USER test WITH PASSWORD 'test';
#        CREATE DATABASE test;
#        GRANT ALL PRIVILEGES ON DATABASE test TO test;
        cls.db = orm.connect('postgresql://test:test@localhost/test')

    @classmethod
    def tearDownClass(cls):
        cls.db.disconnect()

    def runTest(self):

        class Author(orm.Model):
            """Authors catalog
            """
            # id field already present 
            last_name = orm.CharField(max_length = 100, comment = 'Author\'s last name')
            first_name = orm.CharField(max_length = 100, comment = 'Author\'s first name')
            created_at = orm.DateTimeField()

            _meta = orm.ModelOptions(
                db_name = 'authors',
                indexes = orm.Unique(last_name, first_name),
            )

        class Book(orm.Model):
            """Books catalog
            """
            # id field already present 
            name = orm.CharField(max_length = 100, default = 'A very good book!!!')
            price = orm.DecimalField(max_digits = 10, fractionDigits = 2, default = '0.00',
                                    index = True)  # 2 decimal places
            author = orm.RecordField(Author, index = True)
            publication_date = orm.DateField()

        db = self.db
        for model in (Author, Book):
            db.execute(db._drop_table(model))
            for query in db.get_create_table_query(model):
                db.execute(query)
        db.commit()

        authorData = (
            ('first_name', 'last_name'),
            ('Sam', 'Williams'),
            ('Steven', 'Levy'),
            ('Richard', 'Stallman'),
            ('Имя', 'Фамилия'),
        )
        authors = []
        for data in authorData[1:]:
            data = dict(zip(authorData[0], data))
            author = Author.objects.create(db = db, **data)
            print(author)
            authors.append(author)

        bookData = (
            ('name', 'authorid', 'price', 'publication_date'),
            ("Free as in Freedom: Richard Stallman's Crusade for Free Software",
                 authors[0], '9.55', '2002-03-08'),
            ("Hackers: Heroes of the Computer Revolution - 25th Anniversary Edition",
                 authors[1], '14.95', '2010-03-27'),
            ("In The Plex: How Google Thinks, Works, and Shapes Our Lives",
                 authors[1], '13.98', '2011-04-12'),
            ("Crypto: How the Code Rebels Beat the Government Saving Privacy in the Digital Age",
                 authors[1], '23.00', '2002-01-15'),
            ("Книга с русским названием",
                 authors[3], '00.00', '2000-02-29'),
        )
        books = []
        for data in bookData[1:]:
            data = dict(zip(bookData[0], data))
            book = Book.objects.create(db = db, **data)
            print(book)
            books.append(book)


class TestModels(unittest.TestCase):

    def testModelOptions(self):

        try:
            class TestModel(orm.Model):
                _meta = object()
        except orm.ModelError:
            pass
        else:
            self.fail('`_meta` should be only instance of ModelOptions.')

        class TestModel1(orm.Model):
            field1 = orm.IntegerField()
            _meta = orm.ModelOptions(
                db_name = 'test1234',
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
        self.assertEqual(TestModel2._meta.db_name, 'test_model2s')

        class Author(orm.Model):
            last_name = orm.CharField(max_length = 100)
            first_name = orm.CharField(max_length = 100)
            # you can specify name of the fields in indexes
            _meta = orm.ModelOptions(
                indexes = orm.Unique('last_name', 'first_name'),
            )

        # test indexes in _meta
        self.assertIsInstance(Author._meta.indexes, list)
        # primary index for id and our compound index
        self.assertEqual(len(Author._meta.indexes), 2)
        for index in Author._meta.indexes:
            self.assertIsInstance(index, orm.Index)
            self.assertIsInstance(index.index_fields, list)

        self.assertEqual(len(Author._meta.indexes[0].index_fields), 2)
        self.assertIsInstance(Author._meta.indexes[0].index_fields[0].field, orm.CharField)
        self.assertIsInstance(Author._meta.indexes[0].index_fields[1].field, orm.CharField)
        self.assertEqual(Author._meta.indexes[0].type, 'unique')

        self.assertEqual(len(Author._meta.indexes[1].index_fields), 1)
        self.assertIsInstance(Author._meta.indexes[1].index_fields[0].field, orm.IdField)
        self.assertEqual(Author._meta.indexes[1].type, 'primary')

        # you can specify fields in indexes
        class Author1(orm.Model):
            last_name = orm.CharField(max_length = 100)
            first_name = orm.CharField(max_length = 100)
            _meta = orm.ModelOptions(
                indexes = orm.Unique(last_name, first_name)
            )

        # you can specify more sophisticated indexes
        class Author2(orm.Model):
            name = orm.CharField(max_length = 100)
            description = orm.TextField()
            birth_date = orm.DateField()
            _meta = orm.ModelOptions(
                indexes = (orm.Index(orm.IndexField(name, 'desc'),
                                    orm.IndexField(description, prefix_length = 30)),
                           orm.Index(birth_date))
            )

    def testModelField(self):

        try:
            class TestModel1(orm.Model):
                _field = orm.IntegerField()
        except orm.ModelError:
            pass
        else:
            self.fail('Models should not accept fields with names starting with `_`')

        class TestModel2(orm.Model):
            field1 = orm.IntegerField()

        self.assertIsInstance(TestModel2.field1, orm.FieldExpression)
        self.assertEqual(TestModel2.field1.left.name, 'field1')
        # Model.field returns Expression, not Field
        self.assertIsInstance(TestModel2.field1, orm.FieldExpression)

    def testModelInheritance(self):

        class TestModel1(orm.Model):
            field1 = orm.CharField(max_length = 100)

        class TestModel2(TestModel1):
            field1 = orm.IntegerField()
            field2 = orm.CharField(max_length = 100)

        self.assertIsNot(TestModel2.field1, TestModel1.field1)
        self.assertIsInstance(TestModel1.field1.left, orm.CharField)
        self.assertIsInstance(TestModel2.field1.left, orm.IntegerField)
        self.assertIs(TestModel1.field1.left.model, TestModel1)
        self.assertIs(TestModel2.field1.left.model, TestModel2)


class TestExpressions(unittest.TestCase):

    def testIdFied(self):

        class TestModel1(orm.Model):
            field1 = orm.IntegerField()
            field2 = orm.CharField(max_length = 100)

        class TestModel2(orm.Model):
            field3 = orm.RecordField(TestModel1)

        self.assertEqual(str(TestModel1.id == 1), '(test_model1s.id = 1)')
        self.assertEqual(str(TestModel1.field1 == 1), '(test_model1s.field1 = 1)')
        self.assertEqual(str(TestModel1.field2 == 1), "(test_model1s.field2 = '1')")
        self.assertEqual(str(TestModel2.field3 == 3), "(test_model2s.field3_id = 3)")
