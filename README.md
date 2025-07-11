# Proton Mail Auto Signup dengan AntiCaptcha

Script otomatis untuk membuat akun Proton Mail menggunakan layanan AntiCaptcha untuk menyelesaikan puzzle CAPTCHA.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Dapatkan API key dari AntiCaptcha:
   - Daftar di https://anti-captcha.com
   - Dapatkan API key dari dashboard
   - Ganti `YOUR_ANTICAPTCHA_API_KEY_HERE` di file `main.py` dengan API key Anda

3. Jalankan script:
```bash
python main.py
```

## Fitur

- Otomatis generate username dan password random
- Menggunakan AntiCaptcha untuk solve puzzle CAPTCHA
- Screenshot hasil sukses/error
- Menyimpan email dan password yang berhasil ke file `sukses_email.txt`
- Support untuk custom puzzle captcha dengan drag & drop
- Fallback method jika custom captcha gagal

## Catatan

- Pastikan Anda memiliki saldo di akun AntiCaptcha
- Script akan menunggu maksimal 5 menit untuk solve puzzle CAPTCHA
- Puzzle captcha lebih mahal daripada text captcha (~$2-5 per 1000)
- Jika CAPTCHA gagal diselesaikan, script akan berhenti dengan error
- AntiCaptcha lebih baik untuk puzzle/jigsaw captcha dibanding 2captcha

## File Output

- `sukses_email.txt` - Berisi email dan password yang berhasil dibuat
- `screenshoot/` - Folder berisi screenshot hasil sukses dan error