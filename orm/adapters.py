'''This module contains database adapters, which incapsulate all operations specific to a certain database.
All other ORM modules should be database agnostic.'''

import base64
import time, inspect
import orm


drivers = []

try:
    from sqlite3 import dbapi2 as sqlite3
    drivers.append('SQLite3')
except ImportError:
    orm.logger.debug('no sqlite3.dbapi2 driver')



class Adapter():
    '''Generic DB adapter.'''
    def __init__(self, uri='', connect=True):
        '''URI is already without protocol.'''
        print(uri)
        if connect:
            self.connection = self.connect()
        else:
            self.connection = None
    
    def connect(self):
        '''Connect to the DB and return the connection'''
        return None # DB connection

    def logExecute(self, *a, **b):
        lastsql = a[0]
        t0 = time.time()
        ret = self.cursor.execute(*a, **b)
        self.db._timings.append((lastsql, time.time() - t0))
        return ret
    
    def getLastSql(self):
        return self.db._timings[-1][0]

    def execute(self, *a, **b):
        return self.logExecute(*a, **b)

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
    
    def IN(self, first, second):
        if isinstance(second, str):
            return '(%s IN (%s))' % (self.render(first), second[:-1])
        items = ', '.join(self.render(item, first) for item in second)
        return '(%s IN (%s))' % (self.render(first), items)
    
    def render(self, value, castField=None):
        '''Render of a value in a format suitable for operations with this DB field'''
        if isinstance(value, orm.fields.Expression): # it's an expression
            return value._render(self) # render sub-expression
        else: # it's a value for a DB column
            if value is not None and castField is not None:
                assert isinstance(castField, orm.fields.Expression)
                if isinstance(castField, orm.fields.Field): # Field - subclass of Expression
                    pass # TODO: JOIN
                else: # is the Expression itself
                    castField = castField.type # expression right operand type
                value = castField._cast(value)
                try:
                    return self._render(value, castField.column)
                except:
                    print('Check %r._cast().' % castField)
                    raise
            return self._render(value, None)
        
    def _render(self, value, column):
        if value is None:
            return self.NULL()
        renderFunc = getattr(self, 'render' + column.type.capitalize(), None)
        if hasattr(renderFunc, '__call__'): 
            return renderFunc(value)
        return str(value)  

#            elif isinstance(dbType, DbIntegerField):
#                if isinstance(obj, (datetime.date, datetime.datetime)):
#                    obj = obj.isoformat()[:10]
#                else:
#                    obj = str(obj)
#            elif fieldtype == 'datetime':
#                if isinstance(obj, datetime.datetime):
#                    obj = obj.isoformat()[:19].replace('T', ' ')
#                elif isinstance(obj, datetime.date):
#                    obj = obj.isoformat()[:10] + ' 00:00:00'
#                else:
#                    obj = str(obj)
#            elif fieldtype == 'time':
#                if isinstance(obj, datetime.time):
#                    obj = obj.isoformat()[:10]
#                else:
#                    obj = str(obj)
#            if not isinstance(obj, str):
#                obj = str(obj)
        
             
    def IntegrityError(self): 
        return self.driver.IntegrityError
    
    def OperationalError(self): 
        return self.driver.OperationalError

    def _getCreateTableColumns(self, table):
        columns = []
        for field in table:
            column = field.column
            if column is not None:
                colFunc = getattr(self, 'type' + column.type.capitalize())
                columnType = colFunc(**column.props)
                columns.append('%s %s' % (column.name, columnType))
        return columns
    
    def _getCreateTableIndexes(self, table):
        indexes = []
        for index in table._indexes:
            if index.type == 'primary':
                indexType = 'PRIMARY KEY'
            elif index.type == 'unique':
                indexType = 'UNIQUE KEY'
            else:
                indexType = 'KEY'
            columns = []
            for i, field in enumerate(index.fields):
                column = field.column.name
                prefixLength = index.prefixLengths[i] 
                if prefixLength:
                    column += '(%i)' % prefixLength
                sortOrder = index.sortOrders[i]
                column += ' %s' % sortOrder.upper()
                columns.append(column)
                
            indexes.append('%s %s (%s)' % (indexType, index.name, ', '.join(columns)))
            
        return indexes

    def _getCreateTableOther(self, table):
        return ''

    def getCreateTableQuery(self, table):
        '''Get CREATE TABLE statement for this database'''
        assert inspect.isclass(table) and issubclass(table, orm.Table)
        
        columns = self._getCreateTableColumns(table)
        indexes = self._getCreateTableIndexes(table)
        other = self._getCreateTableOther(table)
        query = 'CREATE TABLE %s (' % str(table)
        query += '\n  ' + ',\n  '.join(columns)
        query += ',\n  ' + ',\n  '.join(indexes)
        query += '\n) ' + other + ';'
        return query

    def NULL(self):   
        return 'NULL'
        
    def typeInt(self, bytesCount=4, intMap = [(1, 'TINYINT'), (2, 'SMALLINT'), 
                    (3, 'MEDIUMINT'), (4, 'INT'), (8, 'BIGINT')], autoincrement=False, **kwargs):
        '''INT column type.'''
        for _bytesCount, _columnType in intMap:
            if bytesCount <= _bytesCount:
                break
        else:
            raise Exception('Too many bytes specified.')
        if autoincrement:
            _columnType += ' AUTO_INCREMENT'
        return _columnType
    
    def renderInt(self, value):
        return str(int(value))

    def renderBlob(self, value):
        return base64.b64encode(str(value))
    
    def typeDecimal(self, maxDigits, decimalPlaces=0, **kwargs):
        '''The declaration syntax for a DECIMAL column is DECIMAL(M,D). The ranges of values for the arguments in MySQL 5.1 are as follows:
        M is the maximum number of digits (the precision). It has a range of 1 to 65. (Older versions of MySQL permitted a range of 1 to 254.)
        D is the number of digits to the right of the decimal point (the scale). It has a range of 0 to 30 and must be no larger than M.'''
        return 'DECIMAL (%s, %s)' % (maxDigits, decimalPlaces)
    
    def typeChar(self, maxLength, lengthFixed=False, **kwargs):
        '''CHAR, VARCHAR'''
        if lengthFixed:
            return 'CHAR(%i)' % maxLength
        else:
            return 'VARCHAR(%i)' % maxLength
            


class SqliteAdapter(Adapter):
    driver = globals().get('sqlite3')

    def _getCreateTableIndexes(self, table):
        indexes = []
        for index in table._indexes:
            if index.type != 'primary': # Sqlite has only primary indexes in the CREATE TABLE query
                continue
            indexType = 'PRIMARY KEY'
            columns = []
            for i, field in enumerate(index.fields):
                column = field.column.name
                prefixLength = index.prefixLengths[i] 
                if prefixLength:
                    column += '(%i)' % prefixLength
                sortOrder = index.sortOrders[i]
                column += ' %s' % sortOrder.upper()
                columns.append(column)
                
            indexes.append('%s (%s)' % (indexType, ', '.join(columns)))
            
        return indexes

    def _getCreateTableOther(self, table):
        indexes = []
        for index in table._indexes:
            if index.type == 'primary': # Sqlite has only primary indexes in the CREATE TABLE query
                continue
            elif index.type == 'unique':
                indexType = 'UNIQUE INDEX'
            else:
                indexType = 'INDEX'
            columns = []
            for i, field in enumerate(index.fields):
                column = field.column.name
#                prefixLength = index.prefixLengths[i] 
#                if prefixLength:
#                    column += '(%i)' % prefixLength
                sortOrder = index.sortOrders[i]
                column += ' %s' % sortOrder.upper()
                columns.append(column)
            table = index.fields[0].table
            indexes.append('CREATE %s "%s" ON "%s" (%s)' % (indexType, index.name, str(table), ', '.join(columns)))
            
        return (';\n' + ';\n'.join(indexes)) if indexes else ''

    def columnInt(self, **kwargs):
        return 'INTEGER'


class MysqlAdapter(Adapter):
    driver = globals().get('mysqldb')
    
    def _getCreateTableOther(self, table):
        return "ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='%s'" % table.__doc__
    
    

class Column():
    '''Abstract DB column, supported natively by the DB.'''
    def __init__(self, name, type, field, **kwargs):
        self.name = name
        self.type = type
        self.field = field
        self.props = kwargs # properties 
        

#class BaseAdapter(ConnectionPool):
#
#    driver = None
#    maxcharlength = MAXCHARLENGTH
#    commit_on_alter_table = False
#    support_distributed_transaction = False
#    uploads_in_blob = False
#    types = {
#        'boolean': 'CHAR(1)',
#        'string': 'CHAR(%(length)s)',
#        'text': 'TEXT',
#        'password': 'CHAR(%(length)s)',
#        'blob': 'BLOB',
#        'upload': 'CHAR(%(length)s)',
#        'integer': 'INTEGER',
#        'double': 'DOUBLE',
#        'decimal': 'DOUBLE',
#        'date': 'DATE',
#        'time': 'TIME',
#        'datetime': 'TIMESTAMP',
#        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
#        'reference': 'INTEGER REFERENCES %(foreign_key)s ON DELETE %(on_delete_action)s',
#        'list:integer': 'TEXT',
#        'list:string': 'TEXT',
#        'list:reference': 'TEXT',
#        }
#
#    def adapt(self, obj):
#        return "'%s'" % obj.replace("'", "''")
#
#    def integrity_error(self):
#        return self.driver.IntegrityError
#
#    def operational_error(self):
#        return self.driver.OperationalError
#
#    def __init__(self, db, uri, pool_size=0, folder=None, db_codec='UTF-8',
#                 credential_decoder=lambda x:x, driver_args={},
#                 adapter_args={}):
#        self.db = db
#        self.dbengine = "None"
#        self.uri = uri
#        self.pool_size = pool_size
#        self.folder = folder
#        self.db_codec = db_codec
#        class Dummy(object):
#            lastrowid = 1
#            def __getattr__(self, value):
#                return lambda * a, **b: []
#        self.connection = Dummy()
#        self.cursor = Dummy()
#
#    def sequence_name(self, tablename):
#        return '%s_sequence' % tablename
#
#    def trigger_name(self, tablename):
#        return '%s_sequence' % tablename
#
#
#    def migrate_table(
#        self,
#        table,
#        sql_fields,
#        sql_fields_old,
#        sql_fields_aux,
#        logfile,
#        fake_migrate=False,
#        ):
#        tablename = table._tablename
#        def fix(item):
#            k, v = item
#            if not isinstance(v, dict):
#                v = dict(type='unkown', sql=v)
#            return k.lower(), v
#        ### make sure all field names are lower case to avoid conflicts
#        sql_fields = dict(map(fix, sql_fields.items()))
#        sql_fields_old = dict(map(fix, sql_fields_old.items()))
#        sql_fields_aux = dict(map(fix, sql_fields_aux.items()))
#
#        keys = sql_fields.keys()
#        for key in sql_fields_old:
#            if not key in keys:
#                keys.append(key)
#        if self.dbengine == 'mssql':
#            new_add = '; ALTER TABLE %s ADD ' % tablename
#        else:
#            new_add = ', ADD '
#
#        metadata_change = False
#        sql_fields_current = copy.copy(sql_fields_old)
#        for key in keys:
#            query = None
#            if not key in sql_fields_old:
#                sql_fields_current[key] = sql_fields[key]
#                query = ['ALTER TABLE %s ADD %s %s;' % \
#                         (tablename, key,
#                          sql_fields_aux[key]['sql'].replace(', ', new_add))]
#                metadata_change = True
#            elif self.dbengine == 'sqlite':
#                if key in sql_fields:
#                    sql_fields_current[key] = sql_fields[key]
#                metadata_change = True
#            elif not key in sql_fields:
#                del sql_fields_current[key]
#                if not self.dbengine in ('firebird',):
#                    query = ['ALTER TABLE %s DROP COLUMN %s;' % (tablename, key)]
#                else:
#                    query = ['ALTER TABLE %s DROP %s;' % (tablename, key)]
#                metadata_change = True
#            elif sql_fields[key]['sql'] != sql_fields_old[key]['sql'] \
#                  and not isinstance(table[key].type, SQLCustomType) \
#                  and not (table[key].type.startswith('reference') and \
#                      sql_fields[key]['sql'].startswith('INT,') and \
#                      sql_fields_old[key]['sql'].startswith('INT NOT NULL,')):
#                sql_fields_current[key] = sql_fields[key]
#                t = tablename
#                tt = sql_fields_aux[key]['sql'].replace(', ', new_add)
#                if not self.dbengine in ('firebird',):
#                    query = ['ALTER TABLE %s ADD %s__tmp %s;' % (t, key, tt),
#                             'UPDATE %s SET %s__tmp=%s;' % (t, key, key),
#                             'ALTER TABLE %s DROP COLUMN %s;' % (t, key),
#                             'ALTER TABLE %s ADD %s %s;' % (t, key, tt),
#                             'UPDATE %s SET %s=%s__tmp;' % (t, key, key),
#                             'ALTER TABLE %s DROP COLUMN %s__tmp;' % (t, key)]
#                else:
#                    query = ['ALTER TABLE %s ADD %s__tmp %s;' % (t, key, tt),
#                             'UPDATE %s SET %s__tmp=%s;' % (t, key, key),
#                             'ALTER TABLE %s DROP %s;' % (t, key),
#                             'ALTER TABLE %s ADD %s %s;' % (t, key, tt),
#                             'UPDATE %s SET %s=%s__tmp;' % (t, key, key),
#                             'ALTER TABLE %s DROP %s__tmp;' % (t, key)]
#                metadata_change = True
#            elif sql_fields[key]['type'] != sql_fields_old[key]['type']:
#                sql_fields_current[key] = sql_fields[key]
#                metadata_change = True
#
#            if query:
#                logfile.write('timestamp: %s\n'
#                              % datetime.datetime.today().isoformat())
#                table._db['_lastsql'] = '\n'.join(query)
#                for sub_query in query:
#                    logfile.write(sub_query + '\n')
#                    if not fake_migrate:
#                        self.execute(sub_query)
#                        # caveat. mysql, oracle and firebird do not allow multiple alter table
#                        # in one transaction so we must commit partial transactions and
#                        # update table._dbt after alter table.
#                        if table._db._adapter.commit_on_alter_table:
#                            table._db.commit()
#                            tfile = self.file_open(table._dbt, 'w')
#                            cPickle.dump(sql_fields_current, tfile)
#                            self.file_close(tfile)
#                            logfile.write('success!\n')
#                    else:
#                        logfile.write('faked!\n')
#            elif metadata_change:
#                tfile = self.file_open(table._dbt, 'w')
#                cPickle.dump(sql_fields_current, tfile)
#                self.file_close(tfile)
#
#        if metadata_change and \
#                not (query and self.dbengine in ('mysql', 'oracle', 'firebird')):
#            table._db.commit()
#            tfile = self.file_open(table._dbt, 'w')
#            cPickle.dump(sql_fields_current, tfile)
#            self.file_close(tfile)
#
#
#    def _drop(self, table, mode):
#        return ['DROP TABLE %s;' % table]
#
#    def drop(self, table, mode=''):
#        if table._dbt:
#            logfile = self.file_open(table._loggername, 'a')
#        queries = self._drop(table, mode)
#        for query in queries:
#            if table._dbt:
#                logfile.write(query + '\n')
#            self.execute(query)
#        table._db.commit()
#        del table._db[table._tablename]
#        del table._db.tables[table._db.tables.index(table._tablename)]
#        table._db._update_referenced_by(table._tablename)
#        if table._dbt:
#            self.file_delete(table._dbt)
#            logfile.write('success!\n')
#
#    def _insert(self, table, fields):
#        keys = ','.join(f.name for f, v in fields)
#        values = ','.join(self.render(v, f.type) for f, v in fields)
#        return 'INSERT INTO %s(%s) VALUES (%s);' % (table, keys, values)
#
#    def insert(self, table, fields):
#        query = self._insert(table, fields)
#        try:
#            self.execute(query)
#        except Exception as e:
#            if isinstance(e, self.integrity_error_class()):
#                return None
#            raise e
#        if hasattr(table, '_primarykey'):
#            return dict([(k[0].name, k[1]) for k in fields \
#                             if k[0].name in table._primarykey])
#        id = self.lastrowid(table)
#        if not isinstance(id, int):
#            return id
#        rid = Reference(id)
#        (rid._table, rid._record) = (table, None)
#        return rid
#
#    def bulk_insert(self, table, items):
#        return [self.insert(table, item) for item in items]
#
#    def render(self, expression, field_type=None):
#        if isinstance(expression, Field):
#            return str(expression)
#        elif isinstance(expression, (Expression, Query)):
#            if not expression.second is None:
#                return expression.op(expression.first, expression.second)
#            elif not expression.first is None:
#                return expression.op(expression.first)
#            elif not isinstance(expression.op, str):
#                return expression.op()
#            else:
#                return '(%s)' % expression.op
#        elif field_type:
#            return self.represent(expression, field_type)
#        elif isinstance(expression, (list, tuple)):
#            return ','.join([self.represent(item, field_type) for item in expression])
#        else:
#            return str(expression)
#
#    def alias(self, table, alias):
#        """
#        given a table object, makes a new table object
#        with alias name.
#        """
#        other = copy.copy(table)
#        other['_ot'] = other._tablename
#        other['ALL'] = SQLALL(other)
#        other['_tablename'] = alias
#        for fieldname in other.fields:
#            other[fieldname] = copy.copy(other[fieldname])
#            other[fieldname]._tablename = alias
#            other[fieldname].tablename = alias
#            other[fieldname].table = other
#        table._db[alias] = other
#        return other
#
#    def _truncate(self, table, mode=''):
#        tablename = table._tablename
#        return ['TRUNCATE TABLE %s %s;' % (tablename, mode or '')]
#
#    def truncate(self, table, mode=' '):
#        # Prepare functions "write_to_logfile" and "close_logfile"
#        if table._dbt:
#            logfile = self.file_open(table._loggername, 'a')
#        else:
#            class Logfile(object):
#                def write(self, value):
#                    pass
#                def close(self):
#                    pass
#            logfile = Logfile()
#
#        try:
#            queries = table._db._adapter._truncate(table, mode)
#            for query in queries:
#                logfile.write(query + '\n')
#                self.execute(query)
#            table._db.commit()
#            logfile.write('success!\n')
#        finally:
#            logfile.close()
#
#    def _update(self, tablename, query, fields):
#        if query:
#            sql_w = ' WHERE ' + self.render(query)
#        else:
#            sql_w = ''
#        sql_v = ','.join(['%s=%s' % (field.name, self.render(value, field.type)) for (field, value) in fields])
#        return 'UPDATE %s SET %s%s;' % (tablename, sql_v, sql_w)
#
#    def update(self, tablename, query, fields):
#        sql = self._update(tablename, query, fields)
#        self.execute(sql)
#        try:
#            return self.cursor.rowcount
#        except:
#            return None
#
#    def _delete(self, tablename, query):
#        if query:
#            sql_w = ' WHERE ' + self.render(query)
#        else:
#            sql_w = ''
#        return 'DELETE FROM %s%s;' % (tablename, sql_w)
#
#    def delete(self, tablename, query):
#        sql = self._delete(tablename, query)
#        ### special code to handle CASCADE in SQLite
#        db = self.db
#        table = db[tablename]
#        if self.dbengine == 'sqlite' and table._referenced_by:
#            deleted = [x[table._id.name] for x in db(query).select(table._id)]
#        ### end special code to handle CASCADE in SQLite
#        self.execute(sql)
#        try:
#            counter = self.cursor.rowcount
#        except:
#            counter = None
#        ### special code to handle CASCADE in SQLite
#        if self.dbengine == 'sqlite' and counter:
#            for tablename, fieldname in table._referenced_by:
#                f = db[tablename][fieldname]
#                if f.type == 'reference ' + table._tablename and f.ondelete == 'CASCADE':
#                    db(db[tablename][fieldname].belongs(deleted)).delete()
#        ### end special code to handle CASCADE in SQLite
#        return counter
#
#    def get_table(self, query):
#        tablenames = self.tables(query)
#        if len(tablenames) == 1:
#            return tablenames[0]
#        elif len(tablenames) < 1:
#            raise RuntimeError("No table selected")
#        else:
#            raise RuntimeError("Too many tables selected")
#
    def _select(self, query, fields, attributes):
        for key in set(attributes.keys()) - set(('orderby', 'groupby', 'limitby',
                                               'required', 'cache', 'left',
                                               'distinct', 'having', 'join')):
            raise SyntaxError('invalid select attribute: %s' % key)
        # ## if not fields specified take them all from the requested tables
        new_fields = []
        for item in fields:
            if isinstance(item, SQLALL):
                new_fields += item.table
            else:
                new_fields.append(item)
        fields = new_fields
        tablenames = self.tables(query) # get tables involved in the query
        query = self.filter_tenant(query, tablenames) # process the query ???
        if not fields:
            for table in tablenames:
                for field in self.db[table]:
                    fields.append(field)
        else:
            for field in fields:
                if isinstance(field, basestring) and table_field.match(field):
                    tn, fn = field.split('.')
                    field = self.db[tn][fn]
                for tablename in self.tables(field):
                    if not tablename in tablenames:
                        tablenames.append(tablename)
        if not tablenames:
            raise SyntaxError('Set: no tables selected')
        sql_f = ', '.join(map(self.render, fields))
        self._colnames = [c.strip() for c in sql_f.split(', ')]
        if query:
            sql_w = ' WHERE ' + self.render(query)
        else:
            sql_w = ''
        sql_o = ''
        sql_s = ''
        left = attributes.get('left', False)
        inner_join = attributes.get('join', False)
        distinct = attributes.get('distinct', False)
        groupby = attributes.get('groupby', False)
        orderby = attributes.get('orderby', False)
        having = attributes.get('having', False)
        limitby = attributes.get('limitby', False)
        if distinct is True:
            sql_s += 'DISTINCT'
        elif distinct:
            sql_s += 'DISTINCT ON (%s)' % distinct
        if inner_join:
            icommand = self.JOIN()
            if not isinstance(inner_join, (tuple, list)):
                inner_join = [inner_join]
            ijoint = [t._tablename for t in inner_join if not isinstance(t, Expression)]
            ijoinon = [t for t in inner_join if isinstance(t, Expression)]
            ijoinont = [t.first._tablename for t in ijoinon]
            iexcluded = [t for t in tablenames if not t in ijoint + ijoinont]
        if left:
            join = attributes['left']
            command = self.LEFT_JOIN()
            if not isinstance(join, (tuple, list)):
                join = [join]
            joint = [t._tablename for t in join if not isinstance(t, Expression)]
            joinon = [t for t in join if isinstance(t, Expression)]
            #patch join+left patch (solves problem with ordering in left joins)
            tables_to_merge = {}
            [tables_to_merge.update(dict.fromkeys(self.tables(t))) for t in joinon]
            joinont = [t.first._tablename for t in joinon]
            [tables_to_merge.pop(t) for t in joinont if t in tables_to_merge]
            important_tablenames = joint + joinont + tables_to_merge.keys()
            excluded = [t for t in tablenames if not t in important_tablenames ]
        def alias(t):
            return str(self.db[t])
        if inner_join and not left:
            sql_t = ', '.join(alias(t) for t in iexcluded)
            for t in ijoinon:
                sql_t += ' %s %s' % (icommand, str(t))
        elif not inner_join and left:
            sql_t = ', '.join([alias(t) for t in excluded + tables_to_merge.keys()])
            if joint:
                sql_t += ' %s %s' % (command, ','.join([t for t in joint]))
            for t in joinon:
                sql_t += ' %s %s' % (command, str(t))
        elif inner_join and left:
            sql_t = ','.join([alias(t) for t in excluded + \
                                  tables_to_merge.keys() if t in iexcluded ])
            for t in ijoinon:
                sql_t += ' %s %s' % (icommand, str(t))
            if joint:
                sql_t += ' %s %s' % (command, ','.join([t for t in joint]))
            for t in joinon:
                sql_t += ' %s %s' % (command, str(t))
        else:
            sql_t = ', '.join(alias(t) for t in tablenames)
        if groupby:
            if isinstance(groupby, (list, tuple)):
                groupby = xorify(groupby)
            sql_o += ' GROUP BY %s' % self.render(groupby)
            if having:
                sql_o += ' HAVING %s' % attributes['having']
        if orderby:
            if isinstance(orderby, (list, tuple)):
                orderby = xorify(orderby)
            if str(orderby) == '<random>':
                sql_o += ' ORDER BY %s' % self.RANDOM()
            else:
                sql_o += ' ORDER BY %s' % self.render(orderby)
        if limitby:
            if not orderby and tablenames:
                sql_o += ' ORDER BY %s' % ', '.join(['%s.%s' % (t, x) for t in tablenames for x in ((hasattr(self.db[t], '_primarykey') and self.db[t]._primarykey) or [self.db[t]._id.name])])
            # oracle does not support limitby
        return self.select_limitby(sql_s, sql_f, sql_t, sql_w, sql_o, limitby)

    def select_limitby(self, sql_s, sql_f, sql_t, sql_w, sql_o, limitby):
        if limitby:
            (lmin, lmax) = limitby
            sql_o += ' LIMIT %i OFFSET %i' % (lmax - lmin, lmin)
        return 'SELECT %s %s FROM %s%s%s;' % (sql_s, sql_f, sql_t, sql_w, sql_o)

    def select(self, query, fields, attributes):
        """
        Always returns a Rows object, even if it may be empty
        """
        def response(sql):
            self.execute(sql)
            return self.cursor.fetchall()
        sql = self._select(query, fields, attributes)
        if attributes.get('cache', None):
            (cache_model, time_expire) = attributes['cache']
            del attributes['cache']
            key = self.uri + '/' + sql
            key = (key <= 200) and key or hashlib.md5(key).hexdigest()
            rows = cache_model(key, lambda: response(sql), time_expire)
        else:
            rows = response(sql)
        if isinstance(rows, tuple):
            rows = list(rows)
        limitby = attributes.get('limitby', None) or (0,)
        rows = self.rowslice(rows, limitby[0], None)
        return self.parse(rows, self._colnames)

#    def _count(self, query, distinct=None):
#        tablenames = self.tables(query)
#        if query:
#            sql_w = ' WHERE ' + self.render(query)
#        else:
#            sql_w = ''
#        sql_t = ','.join(tablenames)
#        if distinct:
#            if isinstance(distinct, (list, tuple)):
#                distinct = xorify(distinct)
#            sql_d = self.render(distinct)
#            return 'SELECT count(DISTINCT %s) FROM %s%s;' % (sql_d, sql_t, sql_w)
#        return 'SELECT count(*) FROM %s%s;' % (sql_t, sql_w)
#
#    def count(self, query, distinct=None):
#        self.execute(self._count(query, distinct))
#        return self.cursor.fetchone()[0]
#
#
    def tables(self, query):
        tables = set()
        if isinstance(query, Field):
            tables.add(query.tablename)
        elif isinstance(query, (Expression, Query)):
            if not query.first is None:
                tables = tables.union(self.tables(query.first))
            if not query.second is None:
                tables = tables.union(self.tables(query.second))
        return list(tables)
#
#    def commit(self):
#        return self.connection.commit()
#
#    def rollback(self):
#        return self.connection.rollback()
#
#    def close(self):
#        return self.connection.close()
#
#    def distributed_transaction_begin(self, key):
#        return
#
#    def prepare(self, key):
#        self.connection.prepare()
#
#    def commit_prepared(self, key):
#        self.connection.commit()
#
#    def rollback_prepared(self, key):
#        self.connection.rollback()
#
#    def concat_add(self, table):
#        return ', ADD '
#
#    def constraint_name(self, table, fieldname):
#        return '%s_%s__constraint' % (table, fieldname)
#
#    def create_sequence_and_triggers(self, query, table, **args):
#        self.execute(query)
#
#    def log_execute(self, *a, **b):
#        self.db._lastsql = a[0]
#        t0 = time.time()
#        ret = self.cursor.execute(*a, **b)
#        self.db._timings.append((a[0], time.time() - t0))
#        return ret
#
#    def execute(self, *a, **b):
#        return self.log_execute(*a, **b)
#
#    def represent(self, obj, fieldtype):
#        if isinstance(obj, CALLABLETYPES):
#            obj = obj()
#        if isinstance(fieldtype, SQLCustomType):
#            return fieldtype.encoder(obj)
#        if isinstance(obj, (Expression, Field)):
#            return str(obj)
#        if fieldtype.startswith('list:'):
#            if not obj:
#                obj = []
#            if not isinstance(obj, (list, tuple)):
#                obj = [obj]
#        if isinstance(obj, (list, tuple)):
#            obj = bar_encode(obj)
#        if obj is None:
#            return 'NULL'
#        if obj == '' and not fieldtype[:2] in ['st', 'te', 'pa', 'up']:
#            return 'NULL'
#        r = self.represent_exceptions(obj, fieldtype)
#        if not r is None:
#            return r
#        if fieldtype == 'boolean':
#            if obj and not str(obj)[:1].upper() in ['F', '0']:
#                return "'T'"
#            else:
#                return "'F'"
#        if fieldtype == 'id' or fieldtype == 'integer':
#            return str(int(obj))
#        if fieldtype.startswith('decimal'):
#            return str(obj)
#        elif fieldtype.startswith('reference'): # reference
#            if fieldtype.find('.') > 0:
#                return repr(obj)
#            elif isinstance(obj, (Row, Reference)):
#                return str(obj['id'])
#            return str(int(obj))
#        elif fieldtype == 'double':
#            return repr(float(obj))
#        if isinstance(obj, unicode):
#            obj = obj.encode(self.db_codec)
#        if fieldtype == 'blob':
#            obj = base64.b64encode(str(obj))
#        elif fieldtype == 'date':
#            if isinstance(obj, (datetime.date, datetime.datetime)):
#                obj = obj.isoformat()[:10]
#            else:
#                obj = str(obj)
#        elif fieldtype == 'datetime':
#            if isinstance(obj, datetime.datetime):
#                obj = obj.isoformat()[:19].replace('T', ' ')
#            elif isinstance(obj, datetime.date):
#                obj = obj.isoformat()[:10] + ' 00:00:00'
#            else:
#                obj = str(obj)
#        elif fieldtype == 'time':
#            if isinstance(obj, datetime.time):
#                obj = obj.isoformat()[:10]
#            else:
#                obj = str(obj)
#        if not isinstance(obj, str):
#            obj = str(obj)
#        try:
#            obj.decode(self.db_codec)
#        except:
#            obj = obj.decode('latin1').encode(self.db_codec)
#        return self.adapt(obj)
#
#    def represent_exceptions(self, obj, fieldtype):
#        return None
#
#    def lastrowid(self, table):
#        return None
#
#    def integrity_error_class(self):
#        return type(None)
#
#    def rowslice(self, rows, minimum=0, maximum=None):
#        """ by default this function does nothing, overload when db does not do slicing """
#        return rows
#
    def parse(self, rows, colnames, blob_decode=True):
        db = self.db
        virtualtables = []
        new_rows = []
        for (i, row) in enumerate(rows):
            new_row = Row()
            for j, colname in enumerate(colnames):
                value = row[j]
                if not table_field.match(colnames[j]):
                    if not '_extra' in new_row:
                        new_row['_extra'] = Row()
                    new_row['_extra'][colnames[j]] = value
                    select_as_parser = re.compile("\s+AS\s+(\S+)")
                    new_column_name = select_as_parser.search(colnames[j])
                    if not new_column_name is None:
                        column_name = new_column_name.groups(0)
                        setattr(new_row, column_name[0], value)
                    continue
                (tablename, fieldname) = colname.split('.')
                table = db[tablename]
                field = table[fieldname]
                field_type = field.type
                if field.type != 'blob' and isinstance(value, str):
                    try:
                        value = value.decode(db._db_codec)
                    except Exception:
                        pass
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
                if not tablename in new_row:
                    colset = new_row[tablename] = Row()
                    if tablename not in virtualtables:
                        virtualtables.append(tablename)
                else:
                    colset = new_row[tablename]

                if isinstance(field_type, SQLCustomType):
                    colset[fieldname] = field_type.decoder(value)
                    # field_type = field_type.type
                elif not isinstance(field_type, str) or value is None:
                    colset[fieldname] = value
                elif isinstance(field_type, str) and \
                        field_type.startswith('reference'):
                    referee = field_type[10:].strip()
                    if not '.' in referee:
                        colset[fieldname] = rid = Reference(value)
                        (rid._table, rid._record) = (db[referee], None)
                    else: ### reference not by id
                        colset[fieldname] = value
                elif field_type == 'boolean':
                    if value == True or str(value)[:1].lower() == 't':
                        colset[fieldname] = True
                    else:
                        colset[fieldname] = False
                elif field_type == 'date' \
                        and (not isinstance(value, datetime.date)\
                                 or isinstance(value, datetime.datetime)):
                    (y, m, d) = map(int, str(value)[:10].strip().split('-'))
                    colset[fieldname] = datetime.date(y, m, d)
                elif field_type == 'time' \
                        and not isinstance(value, datetime.time):
                    time_items = map(int, str(value)[:8].strip().split(':')[:3])
                    if len(time_items) == 3:
                        (h, mi, s) = time_items
                    else:
                        (h, mi, s) = time_items + [0]
                    colset[fieldname] = datetime.time(h, mi, s)
                elif field_type == 'datetime'\
                        and not isinstance(value, datetime.datetime):
                    (y, m, d) = map(int, str(value)[:10].strip().split('-'))
                    time_items = map(int, str(value)[11:19].strip().split(':')[:3])
                    if len(time_items) == 3:
                        (h, mi, s) = time_items
                    else:
                        (h, mi, s) = time_items + [0]
                    colset[fieldname] = datetime.datetime(y, m, d, h, mi, s)
                elif field_type == 'blob' and blob_decode:
                    colset[fieldname] = base64.b64decode(str(value))
                elif field_type.startswith('decimal'):
                    decimals = int(field_type[8:-1].split(',')[-1])
                    if self.dbengine == 'sqlite':
                        value = ('%.' + str(decimals) + 'f') % value
                    if not isinstance(value, decimal.Decimal):
                        value = decimal.Decimal(str(value))
                    colset[fieldname] = value
                elif field_type.startswith('list:integer'):
                    if not self.dbengine == 'google:datastore':
                        colset[fieldname] = bar_decode_integer(value)
                    else:
                        colset[fieldname] = value
                elif field_type.startswith('list:reference'):
                    if not self.dbengine == 'google:datastore':
                        colset[fieldname] = bar_decode_integer(value)
                    else:
                        colset[fieldname] = value
                elif field_type.startswith('list:string'):
                    if not self.dbengine == 'google:datastore':
                        colset[fieldname] = bar_decode_string(value)
                    else:
                        colset[fieldname] = value
                else:
                    colset[fieldname] = value
                if field_type == 'id':
                    id = colset[field.name]
                    colset.update_record = lambda _ = (colset, table, id), **a: update_record(_, a)
                    colset.delete_record = lambda t = table, i = id: t._db(t._id == i).delete()
                    for (referee_table, referee_name) in \
                            table._referenced_by:
                        s = db[referee_table][referee_name]
                        referee_link = db._referee_name and \
                            db._referee_name % dict(table=referee_table, field=referee_name)
                        if referee_link and not referee_link in colset:
                            colset[referee_link] = Set(db, s == id)
                    colset['id'] = id
            new_rows.append(new_row)

        rowsobj = Rows(db, new_rows, colnames, rawrows=rows)

        for tablename in virtualtables:
            ### new style virtual fields
            table = db[tablename]
            fields_virtual = [(f, v) for (f, v) in table.items() if isinstance(v, FieldVirtual)]
            fields_lazy = [(f, v) for (f, v) in table.items() if isinstance(v, FieldLazy)]
            if fields_virtual or fields_lazy:
                for row in rowsobj.records:
                    box = row[tablename]
                    for f, v in fields_virtual:
                        box[f] = v.f(row)
                    for f, v in fields_lazy:
                        box[f] = (v.handler or VirtualCommand)(v.f, row)

            ### old style virtual fields
            for item in table.virtualfields:
                try:
                    rowsobj = rowsobj.setvirtualfields(**{tablename:item})
                except KeyError:
                    # to avoid breaking virtualfields when partial select
                    pass
        return rowsobj

    def filter_tenant(self, query, tablenames):
        fieldname = self.db._request_tenant
        for tablename in tablenames:
            table = self.db[tablename]
            if fieldname in table:
                default = table[fieldname].default
                if not default is None:
                    query = query & (table[fieldname] == default)
        return query


#class SQLiteAdapter(BaseAdapter):
#
#    driver = globals().get('sqlite3', None)
#
#    def EXTRACT(self, field, what):
#        return "web2py_extract('%s',%s)" % (what, self.render(field))
#
#    @staticmethod
#    def web2py_extract(lookup, s):
#        table = {
#            'year': (0, 4),
#            'month': (5, 7),
#            'day': (8, 10),
#            'hour': (11, 13),
#            'minute': (14, 16),
#            'second': (17, 19),
#            }
#        try:
#            (i, j) = table[lookup]
#            return int(s[i:j])
#        except:
#            return None
#
#    def __init__(self, db, uri, pool_size=0, folder=None, db_codec='UTF-8',
#                 credential_decoder=lambda x:x, driver_args={}, adapter_args={}):
#        self.db = db
#        self.dbengine = "sqlite"
#        self.uri = uri
#        self.pool_size = pool_size
#        self.folder = folder
#        self.db_codec = db_codec
#        self.find_or_make_work_folder()
#        path_encoding = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf8'
#        if uri.startswith('sqlite:memory'):
#            dbpath = ':memory:'
#        else:
#            dbpath = uri.split('://')[1]
#            if dbpath[0] != '/':
#                dbpath = os.path.join(self.folder.decode(path_encoding).encode('utf8'), dbpath)
#        if not 'check_same_thread' in driver_args:
#            driver_args['check_same_thread'] = False
#        if not 'detect_types' in driver_args:
#            driver_args['detect_types'] = self.driver.PARSE_DECLTYPES
#        def connect(dbpath=dbpath, driver_args=driver_args):
#            return self.driver.Connection(dbpath, **driver_args)
#        self.pool_connection(connect)
#        self.connection.create_function('web2py_extract', 2, SQLiteAdapter.web2py_extract)
#
#    def _truncate(self, table, mode=''):
#        tablename = table._tablename
#        return ['DELETE FROM %s;' % tablename,
#                "DELETE FROM sqlite_sequence WHERE name='%s';" % tablename]
#
#    def lastrowid(self, table):
#        return self.cursor.lastrowid
