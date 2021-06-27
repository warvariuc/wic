import peewee

import wic

from ..locations import Location
from ..streets import Street


class Person(wic.forms.catalog.CatalogModel):
    last_name = peewee.CharField(max_length=50)
    first_name = peewee.CharField(max_length=50)
    middle_name = peewee.CharField(max_length=50)
    phone_prefix = peewee.IntegerField()
    phone_number = peewee.IntegerField()
    location = peewee.ForeignKeyField(Location)
    street = peewee.ForeignKeyField(Street)

    class Meta:
        table_name = 'persons'

    def __str__(self):
        return f'{self.last_name} {self.middle_name} {self.first_name}'
