import os
import io
import base64
import joblib
import pandas as pd
import matplotlib

from dotenv import load_dotenv
from groq import Groq
import markdown
import bleach

from django.shortcuts import render

from .models import DataKos
from .fuzzy_logic import klasifikasi_harga
from django.utils.safestring import mark_safe

# Memuat konfigurasi dari file .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Konfigurasi grafik
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Memuat model Machine Learning
MODEL_PATH = os.path.join(BASE_DIR, 'model_kos.joblib')
model = joblib.load(MODEL_PATH)


def buat_grafik(data_kos):
    nama = [kos.nama_kos for kos in data_kos]
    harga = [kos.harga for kos in data_kos]

    if not nama:
        return None

    plt.figure(figsize=(12, 5))
    plt.bar(nama, harga, color='#D6A600')

    plt.title('Perbandingan Harga Kos di Madiun')
    plt.xlabel('Nama Kos')
    plt.ylabel('Harga Kos (ribuan rupiah)')
    plt.xticks(rotation=90, fontsize=7)
    plt.tight_layout()

    buffer = io.BytesIO()

    try:
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        grafik = base64.b64encode(
            buffer.getvalue()
        ).decode('utf-8')
    finally:
        plt.close()
        buffer.close()

    return grafik


def buat_penjelasan_groq(
    hasil_prediksi,
    hasil_fuzzy,
    jarak_km,
    rating,
    ac
):
    if client is None:
        raise RuntimeError("GROQ_API_KEY belum ditemukan.")

    prompt = f"""
Kamu adalah asisten analisis harga kos di Madiun.

Berikut hasil analisis:
- Prediksi Machine Learning: Rp {hasil_prediksi:,.0f}
- Kategori Fuzzy Logic: {hasil_fuzzy['kategori_fuzzy']}
- Nilai Fuzzy Logic: {hasil_fuzzy['nilai_fuzzy']}
- Jarak kos: {jarak_km} km
- Rating: {rating}
- Fasilitas AC: {'Ada' if ac == 1 else 'Tidak ada'}

Jelaskan hasil tersebut menggunakan bahasa Indonesia
yang sederhana, mudah dipahami, dan singkat.
Jangan mengubah angka hasil prediksi.
Berikan kesimpulan berdasarkan data tersebut.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=500
    )

    jawaban = response.choices[0].message.content

    if not jawaban:
        raise RuntimeError("Groq tidak memberikan jawaban.")

# Mengubah Markdown menjadi HTML
    jawaban_html = markdown.markdown(
    jawaban.strip(),
    extensions=['extra']
)

# Mengamankan HTML hasil konversi
    jawaban_aman = bleach.clean(
        jawaban_html,
    tags=[
        'p', 'strong', 'em', 'ul', 'ol',
        'li', 'br', 'h3', 'h4', 'blockquote'
    ],
    attributes={},
    strip=True
)

    return mark_safe(jawaban_aman)

def index(request):
    hasil_prediksi = None
    hasil_prediksi_tampil = None
    hasil_fuzzy = None
    hasil_groq = None
    pesan_error = None

    data_kos = list(DataKos.objects.all())

    for kos in data_kos:
        kos.harga_tampil = f"{kos.harga * 1000:,.0f}".replace(",", ".")

    grafik = buat_grafik(data_kos)

    if request.method == 'POST':
        try:
            jarak_input = request.POST.get('jarak_km', '').strip()
            rating_input = request.POST.get('rating', '').strip()
            ac_input = request.POST.get('ac', '').strip()

            if not jarak_input or not rating_input:
                raise ValueError("Jarak dan rating wajib diisi.")

            jarak_km = float(jarak_input)
            rating = float(rating_input)

            if not 0 <= jarak_km <= 20:
                raise ValueError("Jarak harus antara 0 sampai 20 km.")

            if not 0 <= rating <= 5:
                raise ValueError("Rating harus antara 0 sampai 5.")

            if ac_input not in ['0', '1']:
                raise ValueError("Pilihan fasilitas AC tidak valid.")

            ac = int(ac_input)

            data = pd.DataFrame(
                [[jarak_km, rating, ac]],
                columns=['jarak_km', 'rating', 'ac_num']
            )

            # Prediksi Machine Learning
            hasil_prediksi = model.predict(data)[0]
            hasil_prediksi = round(float(hasil_prediksi) * 1000)

            hasil_prediksi_tampil = (
                f"{hasil_prediksi:,}".replace(",", ".")
            )

            # Klasifikasi Fuzzy Logic
            hasil_fuzzy = klasifikasi_harga(
                jarak_km=jarak_km,
                rating=rating,
                ac=ac
            )

            # Penjelasan menggunakan Groq
            try:
                hasil_groq = buat_penjelasan_groq(
                    hasil_prediksi,
                    hasil_fuzzy,
                    jarak_km,
                    rating,
                    ac
                )

            except Exception as e:
                print("Error Groq:", str(e))

                hasil_groq = (
                    f"Berdasarkan Machine Learning, estimasi harga "
                    f"kos adalah Rp {hasil_prediksi_tampil}. "
                    f"Fuzzy Logic menghasilkan kategori "
                    f"{hasil_fuzzy['kategori_fuzzy']} dengan nilai "
                    f"{hasil_fuzzy['nilai_fuzzy']}. "
                    f"Jarak kos {jarak_km} km, rating {rating}, "
                    f"dan fasilitas AC "
                    f"{'tersedia' if ac == 1 else 'tidak tersedia'}. "
                    f"Penjelasan AI sedang tidak tersedia, "
                    f"tetapi hasil prediksi tetap berhasil."
                )

        except (ValueError, TypeError) as e:
            pesan_error = str(e)

        except Exception as e:
            print("Error proses prediksi:", str(e))
            pesan_error = (
                "Terjadi kesalahan saat memproses prediksi. "
                "Silakan periksa kembali input."
            )

    return render(
        request,
        'prediksi/index.html',
        {
            'hasil_prediksi_tampil': hasil_prediksi_tampil,
            'hasil_prediksi': hasil_prediksi,
            'hasil_fuzzy': hasil_fuzzy,
            'hasil_groq': hasil_groq,
            'pesan_error': pesan_error,
            'data_kos': data_kos,
            'grafik': grafik
        }
    )
