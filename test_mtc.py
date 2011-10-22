from pprint import pprint

import orm


class Regions(orm.Table):
    region_name = orm.StringField(maxLength=60)
    region_type_name = orm.StringField(maxLength=20)

class Locations(orm.Table):
    region_id = orm.RecordIdField(Regions)
    location_name = orm.StringField(maxLength=100)
    location_type_name = orm.StringField(maxLength=20)

class Streets(orm.Table):
    location_id = orm.RecordIdField(Locations)
    street_name = orm.StringField(maxLength=100)
    street_old_name = orm.StringField(maxLength=100)
    street_type_name = orm.StringField(maxLength=20)

class Persons(orm.Table):
    last_name = orm.StringField(maxLength=100)
    first_name = orm.StringField(maxLength=100)
    middle_name = orm.StringField(maxLength=100)
    #phone_prefix = " INTEGER NOT NULL ,"
    #phone_number = " INTEGER NOT NULL ,"
    location_id = orm.RecordIdField(Locations)
    street_id = orm.RecordIdField(Streets)


ADAPTERS = dict(sqlite=orm.SqliteAdapter, mysql=orm.MysqlAdapter) # available adapters


dbAdapter = orm.connect('sqlite://../mtc.sqlite', ADAPTERS)

#print('\nRegions table fields:')
#for field in Regions:
#    print(' ', field)

# implicit join
#pprint(dbAdapter.select((Regions.id != Locations.region_id), orderBy=[Regions.region_type_name, -Regions.region_name], limitBy=(0, 10)))

# explicit join
#pprint(dbAdapter.select(None, Regions, join=Locations(Locations.region_id != Regions.id), limitBy=(0, 10)))

