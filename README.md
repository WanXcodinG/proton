# Proton Mail Auto Signup dengan CapSolver (Capy Puzzle)

Script otomatis untuk membuat akun Proton Mail menggunakan layanan CapSolver untuk menyelesaikan Capy puzzle CAPTCHA.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Dapatkan API key dari CapSolver:
   - Daftar di https://capsolver.com
   - Dapatkan API key dari dashboard
   - Ganti `YOUR_CAPSOLVER_API_KEY_HERE` di file `main.py` dengan API key Anda

3. Jalankan script:
```bash
python main.py
```

## Fitur

- ✅ Otomatis generate username dan password random
- ✅ Menggunakan CapSolver untuk solve Capy puzzle CAPTCHA
- ✅ Screenshot hasil sukses/error
- ✅ Menyimpan email dan password yang berhasil ke file `sukses_email.txt`
- ✅ Auto detect Capy site key dari berbagai sumber
- ✅ Support untuk Capy API server custom
- ✅ Multiple method untuk submit Capy response
- ✅ Enhanced error handling dan debug

## Keunggulan CapSolver untuk Capy Puzzle

- 🎯 **Spesialis Capy** - task type `CapyTaskProxyless` khusus untuk Capy puzzle
- ⚡ **Response cepat** - biasanya 15-45 detik
- 💰 **Harga kompetitif** - sekitar $0.003-0.006 per solve
- 🔧 **API modern** - support penuh untuk Capy puzzle captcha
- 📊 **Success rate tinggi** - 90%+ untuk Capy puzzle
- 🛡️ **Proxy support** - bisa pakai proxy jika diperlukan

## Cara Kerja Capy Puzzle

1. **Site Key Detection** - Script otomatis cari site key dari:
   - Script tags di HTML
   - Data attributes pada elements
   - Page source dengan regex patterns

2. **API Server Detection** - Cari API server custom jika ada

3. **CapSolver Integration** - Submit ke CapSolver dengan:
   - Task type: `CapyTaskProxyless`
   - Website URL dan site key
   - API server (jika ada)

4. **Response Handling** - Submit response ke form dengan:
   - Hidden input fields
   - JavaScript variables
   - Window objects

## Catatan

- Pastikan Anda memiliki saldo di akun CapSolver
- Script akan menunggu maksimal 5 menit untuk solve Capy puzzle
- Capy puzzle sekitar $0.003-0.006 per solve
- Jika CAPTCHA gagal diselesaikan, script akan berhenti dengan error
- CapSolver adalah pilihan terbaik untuk Capy puzzle captcha

## File Output

- `sukses_email.txt` - Berisi email dan password yang berhasil dibuat
- `screenshoot/` - Folder berisi screenshot hasil sukses dan error

## Troubleshooting

Jika script gagal:
1. Pastikan API key CapSolver benar
2. Pastikan saldo CapSolver cukup
3. Cek screenshot error di folder `screenshoot/`
4. Pastikan Chrome browser terinstall dengan benar
5. Periksa apakah site key berhasil ditemukan

## API CapSolver untuk Capy

CapSolver menggunakan task type `CapyTaskProxyless` yang khusus untuk:
- Capy puzzle captcha
- Jigsaw puzzle dari Capy
- Drag & drop puzzle Capy
- Image recognition Capy

Format response: `{"captchakey": "CAPY_RESPONSE_TOKEN"}`

## Supported Capy Versions

- ✅ Capy Puzzle v1
- ✅ Capy Puzzle v2  
- ✅ Capy Jigsaw
- ✅ Capy Drag & Drop
- ✅ Custom Capy implementations