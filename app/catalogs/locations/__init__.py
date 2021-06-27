import peewee
from wic import forms

from ..regions import Region


class Location(forms.catalog.CatalogModel):
    location_name = peewee.CharField(max_length=50)
    location_type_name = peewee.CharField(max_length=50)
    region = peewee.ForeignKeyField(Region)

    class Meta:
        table_name = 'locations'

    def __str__(self):
        return self.location_name
