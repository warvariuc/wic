import peewee

from wic import forms
from ..locations import Location


class Street(forms.catalog.CatalogModel):
    street_name = peewee.CharField(max_length=50)
    street_old_name = peewee.CharField(max_length=50)
    street_type_name = peewee.CharField(max_length=20)
    location = peewee.ForeignKeyField(Location)

    class Meta:
        table_name = 'streets'

    def __str__(self):
        return self.street_name or ''
