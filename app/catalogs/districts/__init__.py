import peewee
from wic import forms


class District(forms.catalog.CatalogModel):
    localitate = peewee.CharField(max_length=100)
    judet = peewee.CharField(max_length=50)
    raion = peewee.CharField(max_length=50)
    prefix = peewee.IntegerField()
    posta = peewee.CharField(max_length=20)
    comuna = peewee.CharField(max_length=50)

    class Meta:
        table_name = 'districts'

#    def __str__(self):
#        return self.judet + ' ' + self
