"""
Unit tests for ORM
"""

import sys
import os
import unittest
import logging

import orm


orm.logger.setLevel(logging.WARNING)

def setUpModule():
    pass


def tearDownModule():
    pass


#class TestModelAttr(unittest.TestCase):
#    def testModelAttr(self):
#        class ModelAttribute(orm.ModelAttr):
#            def __init__(self):
##                print('ModelAttribute.__init__ real')
##                import ipdb; from pprint import pprint; ipdb.set_trace()
#                pass
#        class ModelAttributeSubclass(ModelAttribute):
#            def __init__(self):
##                print('ModelAttributeSubclass.__init__ real')
##                import ipdb; from pprint import pprint; ipdb.set_trace()
#                assert ModelAttribute is not super(ModelAttributeSubclass)
##                assert ModelAttributeSubclass.__dict__['__init__'] is not ModelAttribute.__dict__['__init__']
##                assert ModelAttributeSubclass.__init__ is not ModelAttribute.__init__
#                super().__init__()
#        class TestModel(orm.Model):
#            attr1 = ModelAttribute()
#            attr2 = ModelAttributeSubclass()


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
#        query = self.db.getCreateTableQuery(TestModel)
#        for _query in query.split('\n\n'):
#            self.db.execute(_query)


#class TestModelsPostgresql(unittest.TestCase):
#
#    @classmethod
#    def setUpClass(cls):
##        CREATE USER test WITH PASSWORD 'test';
##        CREATE DATABASE test;
##        GRANT ALL PRIVILEGES ON DATABASE test TO test;
#        cls.db = orm.connect('postgresql://test:test@localhost/test')
#
#    @classmethod
#    def tearDownClass(cls):
#        cls.db.disconnect()
#
#    def testCreateTableFromModel(self):
#
#        class Author(orm.Model):
#            """Authors catalog
#            """
#            # id field already present 
#            last_name = orm.CharField(maxLength = 100, comment = 'Author\'s last name')
#            first_name = orm.CharField(maxLength = 100, comment = 'Author\'s first name')
#            created_at = orm.DateTimeField()
#
#            _meta = orm.ModelOptions(
#                db_name = 'authors',
#                indexes = orm.Unique('last_name', 'first_name'),
#            )
#
#        class Book(orm.Model):
#            """Books catalog
#            """
#            # id field already present 
#            name = orm.CharField(maxLength = 100, default = 'A very good book!!!')
#            price = orm.DecimalField(maxDigits = 10, fractionDigits = 2, default = '0.00',
#                                            index = True)  # 2 decimal places
#            author = orm.RecordField('Authors', index = True)
#            publication_date = orm.DateField()
#
#        db = self.db
#        for model in (Author, Book):
#            db.execute(db._dropTable(model))
#            for query in db.getCreateTableQuery(model):
#                db.execute(query)


class TestModels(unittest.TestCase):

    def testModelOptions(self):

#        try:
#            class TestModel(orm.Model):
#                _meta = object()
#        except orm.ModelError:
#            pass
#        else:
#            self.fail('`_meta` should be only instance of ModelOptions.')
#
#        class TestModel1(orm.Model):
#            field1 = orm.IntegerField()
#            _meta = orm.ModelOptions(
#                db_name = 'test1234',
#            )
#
#        self.assertIsInstance(TestModel1._meta, orm.ModelOptions)
#        self.assertEqual(TestModel1._meta.db_name, 'test1234')
#        # Model._meta.fields should be a {fieldName: Field, ...}
#        self.assertIsInstance(TestModel1._meta.fields, dict)
#        for fieldName, field in TestModel1._meta.fields.items():
#            self.assertIsInstance(fieldName, str)
#            self.assertIsInstance(field, orm.ModelField)
#
#        class TestModel2(TestModel1):
#            pass
#
#        # _meta should be per Model, as each model contains its own fields, name, etc.
#        self.assertIsNot(TestModel1._meta, TestModel2._meta)
#        self.assertEqual(TestModel2._meta.db_name, 'test_model2s')


        # you can specify name of the fields in indexes
        class Author(orm.Model):
            last_name = orm.CharField(maxLength = 100)
            first_name = orm.CharField(maxLength = 100)
            _meta = orm.ModelOptions(
                indexes = orm.Unique('last_name', 'first_name'),
            )
            
        # test indexes in _meta
        self.assertIsInstance(Author._meta.indexes, list)
        # rimary index for id and our compound index
        self.assertEqual(len(Author._meta.indexes), 2)
        for index in Author._meta.indexes:
            self.assertIsInstance(index, orm.Index)

        # you can specify fields in indexes
        class Author1(orm.Model):
            last_name = orm.CharField(maxLength = 100)
            first_name = orm.CharField(maxLength = 100)
            _meta = orm.ModelOptions(
                indexes = orm.Unique(last_name, first_name)
            )

        # you can specify more sophisticated indexes
        class Author2(orm.Model):
            name = orm.CharField(maxLength = 100)
            description = orm.TextField()
            birth_date = orm.DateField()
            _meta = orm.ModelOptions(
                indexes = (orm.Index(orm.IndexField(name, 'desc'),
                                    orm.IndexField(description, prefixLength = 30)),
                           orm.Index(birth_date))
            )

#    def testModelField(self):
#
#        try:
#            class TestModel1(orm.Model):
#                _field = orm.IntegerField()
#        except orm.ModelError:
#            pass
#        else:
#            self.fail('Models should not accept fields with names starting with `_`')
#
#        class TestModel2(orm.Model):
#            field1 = orm.IntegerField()
#
#        self.assertIsInstance(TestModel2.field1, orm.FieldExpression)
#        self.assertEqual(TestModel2.field1.left.name, 'field1')
#        # Model.field returns Expression, not Field
#        self.assertIsInstance(TestModel2.field1, orm.FieldExpression)

#    def testModelInheritance(self):
#
#        class TestModel1(orm.Model):
#            field1 = orm.CharField(maxLength = 100)
#
#        class TestModel2(TestModel1):
#            field1 = orm.IntegerField()
#            field2 = orm.CharField(maxLength = 100)
#
#        self.assertIsNot(TestModel2.field1, TestModel1.field1)
#        self.assertIsInstance(TestModel1.field1.left, orm.CharField)
#        self.assertIsInstance(TestModel2.field1.left, orm.IntegerField)
#        self.assertIs(TestModel1.field1.left.model, TestModel1)
#        self.assertIs(TestModel2.field1.left.model, TestModel2)
