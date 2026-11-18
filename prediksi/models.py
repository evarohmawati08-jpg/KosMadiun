
from django.db import models


class DataKos(models.Model):
    nama_kos = models.CharField(max_length=100)
    harga = models.IntegerField()
    jarak_km = models.FloatField()
    rating = models.FloatField()
    ac = models.BooleanField(default=False)

    def __str__(self):
        return self.nama_kos
