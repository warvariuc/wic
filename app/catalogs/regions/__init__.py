from wic import forms
import peewee


class Region(forms.catalog.CatalogModel):
    region_name = peewee.CharField(max_length= 50)
    region_type_name = peewee.CharField(max_length= 20)

    class Meta:
        table_name = 'regions'

    def __str__(self):
        return self.region_name
