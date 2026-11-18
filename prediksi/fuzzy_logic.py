import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


def klasifikasi_harga(jarak_km, rating, ac):
    # Variabel input
    jarak = ctrl.Antecedent(
    np.arange(0, 20.1, 0.1), 'jarak'
)
    kualitas = ctrl.Antecedent(
        np.arange(0, 5.1, 0.1), 'rating'
    )

    fasilitas = ctrl.Antecedent(
        np.arange(0, 2, 1), 'ac'
    )

    # Variabel output
    kategori = ctrl.Consequent(
        np.arange(0, 101, 1), 'kategori'
    )

    # Fungsi keanggotaan jarak
    # Fungsi keanggotaan jarak
    jarak['dekat'] = fuzz.trapmf(
    jarak.universe, [0, 0, 2, 5]
    )

    jarak['sedang'] = fuzz.trimf(
    jarak.universe, [3, 8, 13]
    )

    jarak['jauh'] = fuzz.trapmf(
    jarak.universe, [10, 15, 20, 20]
    )

    # Fungsi keanggotaan rating
    kualitas['rendah'] = fuzz.trapmf(
        kualitas.universe, [0, 0, 2, 3]
    )
    kualitas['sedang'] = fuzz.trimf(
        kualitas.universe, [2, 3.5, 5]
    )
    kualitas['tinggi'] = fuzz.trapmf(
        kualitas.universe, [3.5, 4.5, 5, 5]
    )

    # Fungsi keanggotaan fasilitas AC
    fasilitas['tidak_ada'] = fuzz.trimf(
        fasilitas.universe, [0, 0, 1]
    )
    fasilitas['ada'] = fuzz.trimf(
        fasilitas.universe, [0, 1, 1]
    )

    # Fungsi keanggotaan kategori harga
    kategori['murah'] = fuzz.trapmf(
        kategori.universe, [0, 0, 20, 40]
    )
    kategori['sedang'] = fuzz.trimf(
        kategori.universe, [30, 50, 70]
    )
    kategori['mahal'] = fuzz.trapmf(
        kategori.universe, [60, 80, 100, 100]
    )

    # Aturan fuzzy
    aturan = [
        ctrl.Rule(
            jarak['dekat'] & kualitas['tinggi'] & fasilitas['ada'],
            kategori['mahal']
        ),
        ctrl.Rule(
            jarak['dekat'] & kualitas['tinggi'] & fasilitas['tidak_ada'],
            kategori['sedang']
        ),
        ctrl.Rule(
            jarak['sedang'] & kualitas['sedang'],
            kategori['sedang']
        ),
        ctrl.Rule(
            jarak['jauh'] & kualitas['rendah'],
            kategori['murah']
        ),
        ctrl.Rule(
            jarak['jauh'] & fasilitas['tidak_ada'],
            kategori['murah']
        ),
        ctrl.Rule(
            kualitas['tinggi'] & fasilitas['ada'],
            kategori['mahal']
        ),
        ctrl.Rule(
            jarak['dekat'] & kualitas['rendah'],
            kategori['sedang']
        ),
        ctrl.Rule(
            jarak['sedang'] & kualitas['rendah'],
            kategori['murah']
        
        ),  
        ctrl.Rule(
            jarak['jauh'] & kualitas['sedang'],
            kategori['murah']
        ),
    ]

    # Sistem kontrol fuzzy
    sistem = ctrl.ControlSystem(aturan)
    simulasi = ctrl.ControlSystemSimulation(sistem)

    # Memasukkan nilai
    simulasi.input['jarak'] = jarak_km
    simulasi.input['rating'] = rating
    simulasi.input['ac'] = ac

    # Proses perhitungan
    simulasi.compute()
    print("Output fuzzy:", simulasi.output)

    hasil = simulasi.output['kategori']

    if hasil < 40:
        label = 'Murah'
    elif hasil < 70:
        label = 'Sedang'
    else:
        label = 'Mahal'

    return {
        'nilai_fuzzy': round(hasil, 2),
        'kategori_fuzzy': label
    }
