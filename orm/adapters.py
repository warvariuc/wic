import time
import orm


drivers = []

try:
    from sqlite3 import dbapi2 as sqlite3
    drivers.append('SQLite3')
except ImportError:
    orm.logger.debug('no sqlite3.dbapi2 driver')


class DbAdapter():
    '''Generic DB adapter.'''
    protocol = 'base'
    
    def __init__(self, uri=''):
        '''URI is already without protocol.'''
        print(uri)

    def logExecute(self, *a, **b):
        self.db._lastsql = a[0]
        t0 = time.time()
        ret = self.cursor.execute(*a, **b)
        self.db._timings.append((a[0], time.time() - t0))
        return ret

    def execute(self, *a, **b):
        return self.log_execute(*a, **b)

    def AND(self, left, right):
        '''Render the AND clause.'''
        return '(%s AND %s)' % (self.render(left), self.render(right, left))

    def OR(self, left, right):
        '''Render the OR clause.'''
        return '(%s OR %s)' % (self.render(left), self.render(right, left))
    
    def EQ(self, left, right):
        if right is None:
            return '(%s IS NULL)' % self.render(left)
        return '(%s = %s)' % (self.render(left), self.render(right, left))

    def NE(self, left, right):
        if right is None:
            return '(%s IS NOT NULL)' % self.render(left)
        return '(%s <> %s)' % (self.render(left), self.render(right, left))

    def GT(self, left, right):
        return '(%s > %s)' % (self.render(left), self.render(right, left))

    def GE(self, left, right):
        return '(%s >= %s)' % (self.render(left), self.render(right, left))

    def LT(self, left, right):
        return '(%s < %s)' % (self.render(left), self.render(right, left))

    def LE(self, left, right):
        return '(%s <= %s)' % (self.render(left), self.render(right, left))

    def ADD(self, left, right):
        return '(%s + %s)' % (self.render(left), self.render(right, left))
    
    def BELONGS(self, first, second):
        if isinstance(second, str):
            return '(%s IN (%s))' % (self.render(first), second[:-1])
        items = ','.join(self.render(item, first) for item in second)
        return '(%s IN (%s))' % (self.render(first), items)
    
    def render(self, value, castField=None):
        ''''''
        if isinstance(value, orm.Expression): # it's an expression
            return value._render(self) # render sub-expression
        else: # it's a value for a DbField
            if value is None:
                return 'NULL'
            if castField is not None:
#                print(castField, value)
                assert isinstance(castField, orm.Expression)
                if isinstance(castField, orm.Field):
                    pass
                elif isinstance(castField, orm.Expression):
                    castField = castField.type
                value = castField._cast(value) 
                dbField = castField.dbtype
                renderFunc = getattr(dbField, self.protocol + 'Render')
                return renderFunc(value, self)
            return str(value)
             
#    def __call__(self, expression=None):
#        if isinstance(expression, Table):
#            expression = expression._id > 0
#        elif isinstance(expression, Field):
#            expression = expression != None
#        return Set(self, expression)

    def integrity_error(self):
        return self.driver.IntegrityError

    def operational_error(self):
        return self.driver.OperationalError


class SqliteAdapter(DbAdapter):
    protocol = 'sqlite'
    driver = globals().get('sqlite3', None)
