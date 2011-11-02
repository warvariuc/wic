from wic import orm
from conf.catalogs.Справочник2.models import Locations

class Persons(orm.Model):
    last_name = orm.StringField(maxLength= 100)
    first_name = orm.StringField(maxLength= 100)
    middle_name = orm.StringField(maxLength= 100)
    phone_prefix = orm.IntegerField(bytesCount= 2) # phone prefix code of the location
    phone_number = orm.IntegerField(bytesCount= 4)
    location_id = orm.RecordIdField(Locations)
    street_id = orm.RecordIdField(Streets)
    
    def checkNames(self):
        '''An item function, like in Django'''
        pass
