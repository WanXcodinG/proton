# Proton Mail Auto Signup dengan 2captcha (Capy Puzzle)

Script otomatis untuk membuat akun Proton Mail menggunakan layanan 2captcha untuk menyelesaikan Capy puzzle CAPTCHA.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Dapatkan API key dari 2captcha:
   - Daftar di https://2captcha.com
   - Dapatkan API key dari dashboard
   - Ganti `YOUR_2CAPTCHA_API_KEY_HERE` di file `main.py` dengan API key Anda

3. Jalankan script:
```bash
python main.py
```

## Fitur

- ✅ Otomatis generate username dan password random
- ✅ Menggunakan 2captcha untuk solve Capy puzzle CAPTCHA
- ✅ Screenshot hasil sukses/error
- ✅ Menyimpan email dan password yang berhasil ke file `sukses_email.txt`
- ✅ Auto detect Capy site key dari berbagai sumber
- ✅ Support untuk Capy API server custom
- ✅ Multiple method untuk submit Capy response
- ✅ Enhanced error handling dan debug

## Keunggulan 2captcha untuk Capy Puzzle

- 🎯 **Method "capy"** - task type khusus untuk Capy puzzle
- ⚡ **Response cepat** - biasanya 30-60 detik
- 💰 **Harga kompetitif** - sekitar $0.002-0.004 per solve
- 🔧 **API stabil** - support penuh untuk Capy puzzle captcha
- 📊 **Success rate tinggi** - 85%+ untuk Capy puzzle
- 🛡️ **Proxy support** - bisa pakai proxy jika diperlukan

## Cara Kerja Capy Puzzle

1. **Site Key Detection** - Script otomatis cari site key dari:
   - Script tags di HTML
   - Data attributes pada elements
   - Page source dengan regex patterns

2. **API Server Detection** - Cari API server custom jika ada

3. **2captcha Integration** - Submit ke 2captcha dengan:
   - Method: `capy`
   - Captchakey: site key yang ditemukan
   - Pageurl: URL halaman saat ini
   - API server (jika ada)

4. **Response Handling** - Submit response ke form dengan:
   - Hidden input fields
   - JavaScript variables
   - Window objects
   - Callback functions

## Catatan

- Pastikan Anda memiliki saldo di akun 2captcha
- Script akan menunggu maksimal 5 menit untuk solve Capy puzzle
- Capy puzzle sekitar $0.002-0.004 per solve
- Jika CAPTCHA gagal diselesaikan, script akan berhenti dengan error
- 2captcha adalah pilihan yang baik untuk Capy puzzle captcha

## File Output

- `sukses_email.txt` - Berisi email dan password yang berhasil dibuat
- `screenshoot/` - Folder berisi screenshot hasil sukses dan error

## Troubleshooting

Jika script gagal:
1. Pastikan API key 2captcha benar
2. Pastikan saldo 2captcha cukup
3. Cek screenshot error di folder `screenshoot/`
4. Pastikan Chrome browser terinstall dengan benar
5. Periksa apakah site key berhasil ditemukan

## API 2captcha untuk Capy

2captcha menggunakan method `capy` yang khusus untuk:
- Capy puzzle captcha
- Jigsaw puzzle dari Capy
- Drag & drop puzzle Capy
- Image recognition Capy

Format response: String token yang harus disubmit ke form

## Supported Capy Versions

- ✅ Capy Puzzle v1
- ✅ Capy Puzzle v2  
- ✅ Capy Jigsaw
- ✅ Capy Drag & Drop
- ✅ Custom Capy implementations

## Harga 2captcha

- **Capy puzzle**: $0.002-0.004 per solve
- **Minimum deposit**: $1
- **Payment methods**: PayPal, Bitcoin, WebMoney, dll
- **Refund policy**: Jika solve gagal, saldo dikembalikan