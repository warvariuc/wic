from urllib.parse import urlsplit
from decimal import Decimal

class DbConnection():
    def __init__(self, uri):
        r = urlsplit(uri) # database connection requisites
        userName = r.username
        password = r.password
        host = r.hostname
        port = r.port
        dbName = r.path[1:]
        print(userName, password, host, port, dbName)

class ValidationError(Exception):
    '''This type of exception is raised when a validation didn't pass.'''
    pass


class Field():
    def validate(self, x):
        '''This function is called just before writing the value to the DB.
        If validation if not passed it raises ValidationError.'''
        return True # dummy validator which is always passed 
    
    def encode(self, x):
        '''Function which processes the value before writing it to the DB'''
        return x
     
    def decode(self, x):
        '''Function which processes the value after reading it from the DB'''
        return x     
    

class IdField(Field):
    '''Built-in id type - for each table.'''
    autoincrement = True
    primary = True
    nativeType = 'INT' # 'CHAR', 'BLOB'
    

class Table():
    id = IdField()


class DecimalField(Field):
    nativeType = 'INT'
    
    def __init__(self, decimalPlaces):
        self.decimalPlaces = decimalPlaces

    def encode(self, x):
        '''Function which processes the value before writing it to the DB.'''
        return int(x * (10 ** self.decimalPlaces))
     
    def decode(self, x):
        '''Function which processes the value after reading it from the DB'''
        return Decimal(x / (10 ** self.decimalPlaces))     
    
    

class Books(Table):
    # id is already present 
    price = DecimalField(2) # 2 decimal places
    
    

