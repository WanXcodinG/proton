# Proton Mail Auto Signup dengan 2captcha

Script otomatis untuk membuat akun Proton Mail menggunakan layanan 2captcha untuk menyelesaikan CAPTCHA.

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

- Otomatis generate username dan password random
- Menggunakan 2captcha untuk solve CAPTCHA
- Screenshot hasil sukses/error
- Menyimpan email dan password yang berhasil ke file `sukses_email.txt`

## Catatan

- Pastikan Anda memiliki saldo di akun 2captcha
- Script akan menunggu maksimal 5 menit untuk solve CAPTCHA
- Jika CAPTCHA gagal diselesaikan, script akan berhenti dengan error

## File Output

- `sukses_email.txt` - Berisi email dan password yang berhasil dibuat
- `screenshoot/` - Folder berisi screenshot hasil sukses dan error