# Proton Mail Auto Signup dengan 2captcha

Script otomatis untuk membuat akun Proton Mail menggunakan layanan 2captcha untuk menyelesaikan puzzle CAPTCHA.

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
- ✅ Menggunakan 2captcha untuk solve puzzle CAPTCHA
- ✅ Screenshot hasil sukses/error
- ✅ Menyimpan email dan password yang berhasil ke file `sukses_email.txt`
- ✅ Support untuk puzzle captcha dengan drag & drop
- ✅ Multiple drag methods untuk reliability
- ✅ Iframe detection dan handling
- ✅ Enhanced coordinate parsing

## Catatan

- Pastikan Anda memiliki saldo di akun 2captcha
- Script akan menunggu maksimal 5 menit untuk solve puzzle CAPTCHA
- Puzzle captcha sekitar $0.003-0.005 per solve
- Jika CAPTCHA gagal diselesaikan, script akan berhenti dengan error
- 2captcha lebih baik untuk puzzle/jigsaw captcha dibanding service lain

## File Output

- `sukses_email.txt` - Berisi email dan password yang berhasil dibuat
- `screenshoot/` - Folder berisi screenshot hasil sukses dan error

## Troubleshooting

Jika script gagal:
1. Pastikan API key 2captcha benar
2. Pastikan saldo 2captcha cukup
3. Cek screenshot error di folder `screenshoot/`
4. Pastikan Chrome browser terinstall dengan benar