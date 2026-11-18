
import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from prediksi.models import DataKos

# Membaca dataset CSV
df = pd.read_csv('kos_madiun.csv')

# Memasukkan data ke database
for _, row in df.iterrows():
    DataKos.objects.update_or_create(
        nama_kos=row['nama'],
        defaults={
            'harga': int(row['harga']),
            'jarak_km': float(row['jarak_km']),
            'rating': float(row['rating']),
            'ac': str(row['ac']).strip().lower() == 'ya'
        }
    )

print('Data kos berhasil dimasukkan ke database!')
print('Jumlah data:', DataKos.objects.count())
