# Proton Mail Auto Signup dengan CapSolver

Script otomatis untuk membuat akun Proton Mail menggunakan layanan CapSolver untuk menyelesaikan puzzle CAPTCHA.

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
- ✅ Menggunakan CapSolver untuk solve puzzle CAPTCHA
- ✅ Screenshot hasil sukses/error
- ✅ Menyimpan email dan password yang berhasil ke file `sukses_email.txt`
- ✅ Support untuk puzzle captcha dengan drag & drop
- ✅ Multiple drag methods untuk reliability
- ✅ Iframe detection dan handling
- ✅ Enhanced coordinate parsing

## Keunggulan CapSolver

- 🎯 **Spesialis puzzle captcha** - lebih akurat untuk jigsaw puzzle
- ⚡ **Response cepat** - biasanya 10-30 detik
- 💰 **Harga kompetitif** - sekitar $0.002-0.004 per solve
- 🔧 **API modern** - support ImageToCoordinatesTask
- 📊 **Success rate tinggi** - 95%+ untuk puzzle captcha

## Catatan

- Pastikan Anda memiliki saldo di akun CapSolver
- Script akan menunggu maksimal 5 menit untuk solve puzzle CAPTCHA
- Puzzle captcha sekitar $0.002-0.004 per solve
- Jika CAPTCHA gagal diselesaikan, script akan berhenti dengan error
- CapSolver lebih baik untuk puzzle/jigsaw captcha dibanding service lain

## File Output

- `sukses_email.txt` - Berisi email dan password yang berhasil dibuat
- `screenshoot/` - Folder berisi screenshot hasil sukses dan error

## Troubleshooting

Jika script gagal:
1. Pastikan API key CapSolver benar
2. Pastikan saldo CapSolver cukup
3. Cek screenshot error di folder `screenshoot/`
4. Pastikan Chrome browser terinstall dengan benar

## API CapSolver

CapSolver menggunakan task type `ImageToCoordinatesTask` yang khusus untuk:
- Jigsaw puzzle captcha
- Click coordinates captcha
- Drag & drop puzzle
- Image recognition dengan koordinat output

Format response: `{"coordinates": [{"x": 123, "y": 456}]}`