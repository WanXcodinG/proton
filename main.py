import os
import time
import re
import random
from faker import Faker
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from temp_gmail import GMail # <-- Import library baru

# --- KONFIGURASI ---
OTP_FETCH_TIMEOUT = 120

def generate_password():
    """Generates a random, strong-looking password."""
    first_letter = chr(random.randint(65, 90))
    other_letters = ''.join(chr(random.randint(97, 122)) for _ in range(7))
    numbers = ''.join(str(random.randint(0, 9)) for _ in range(3))
    return f"{first_letter}{other_letters}{numbers}!"

# --- FUNGSI BARU MENGGUNAKAN temp_gmail ---
def get_proton_otp_from_temp_gmail(gmail_instance, timeout=120, poll_interval=10):
    """
    Fetches Proton OTP using the temp-gmail library.
    """
    start_time = time.time()
    print(f"[INFO] Memulai pencarian OTP menggunakan temp-gmail...")
    
    while time.time() - start_time < timeout:
        try:
            # Cari email baru yang mengandung keyword "Proton"
            message_info = gmail_instance.check_new_item("Proton")
            
            # Cek apakah messageId ditemukan
            if message_info and (message_id := message_info.get('messageId')):
                print(f"[TEMP-GMAIL] Ditemukan email dari Proton. Message ID: {message_id}")
                
                # Ambil konten email menggunakan messageId
                email_body = gmail_instance.load_item(message_id)
                
                if not email_body:
                    print("[WARNING] Gagal memuat konten email, mencoba lagi...")
                    time.sleep(poll_interval)
                    continue

                # Ekstrak kode OTP 6 digit dari konten email
                if match := re.search(r'\b(\d{6})\b', str(email_body)):
                    code = match.group(1)
                    print(f"[SUCCESS] OTP ditemukan: {code}")
                    return code
                else:
                    print("[WARNING] Email Proton ditemukan, tapi OTP belum ada di konten. Mencoba lagi...")

            else:
                print(f"[INFO] OTP belum ditemukan, tunggu {poll_interval} detik...")

        except Exception as e:
            print(f"[TEMP-GMAIL ERROR] Terjadi kesalahan saat memeriksa email: {e}")

        time.sleep(poll_interval)
        
    print(f"[ERROR] OTP tidak ditemukan setelah menunggu.")
    return None

# --- DATA RANDOM ---
fake = Faker()
username = fake.user_name() + str(fake.random_number(digits=3))
password = generate_password()
proton_email = f"{username}@protonmail.com"

# Membuat instance temp-gmail dan email baru
print("[INFO] Membuat email sementara dengan temp-gmail...")
gmail = GMail()
email_verif = gmail.create_email()

if not email_verif:
    print("[CRITICAL] Gagal mendapatkan email verifikasi dari temp-gmail. Script dihentikan.")
    exit()
print(f"[TEMP-GMAIL] Email berhasil dibuat: {email_verif}")

if not os.path.exists("screenshoot"):
    os.makedirs("screenshoot")

# --- HELPER SELENIUM ---
def wait_xpath(driver, xpath, timeout=30, poll=0.5):
    try:
        return WebDriverWait(driver, timeout, poll_frequency=poll).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
    except TimeoutException:
        print(f"[WARNING] Timeout: Tidak menemukan elemen: {xpath}")
        return None

def safe_send_keys(el, text, sleep_time=0.6):
    if el:
        el.clear()
        ActionChains(el._parent).move_to_element(el).click().perform()
        el.send_keys(text)
        time.sleep(sleep_time)
    else:
        print(f"[WARNING] Elemen untuk send_keys '{text}' tidak ditemukan.")

def safe_click(el, sleep_time=0.6):
    if el:
        ActionChains(el._parent).move_to_element(el).click().perform()
        time.sleep(sleep_time)
    else:
        print("[WARNING] Elemen untuk di-klik tidak ditemukan.")

def switch_to_iframe_xpath(driver, xpath, timeout=25):
    try:
        WebDriverWait(driver, timeout).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, xpath))
        )
        time.sleep(0.6)
    except TimeoutException:
        print(f"[ERROR] Timeout: Tidak bisa switch ke iframe: {xpath}")
        raise

def switch_to_default(driver):
    driver.switch_to.default_content()
    time.sleep(0.6)

# --- PROSES SIGNUP PROTONMAIL ---
options = uc.ChromeOptions()
driver = uc.Chrome(options=options, use_subprocess=True)

try:
    driver.get("https://account.proton.me/signup?plan=free")
    time.sleep(2)
    
    # 1. Masuk ke iframe signup
    signup_iframe_xpath = "//iframe[@title='Email address']"
    switch_to_iframe_xpath(driver, signup_iframe_xpath)

    # 2. Isi username faker
    username_input = wait_xpath(driver, "//input[@id='username']")
    safe_send_keys(username_input, username)

    # 3. Keluar iframe untuk pilih domain
    domain_btn = wait_xpath(driver, "//button[@id='select-domain']")
    safe_click(domain_btn)

    # 4. Pilih @protonmail.com
    switch_to_default(driver)
    domain_opt = wait_xpath(driver, "//button[@title='protonmail.com']")
    safe_click(domain_opt)

    # 5. Masuk lagi ke iframe signup
    signup_iframe_xpath = "//iframe[@title='Email address']"

    # 6. Isi password dan konfirmasi password
    password_input = wait_xpath(driver, "//input[@id='password']")
    safe_send_keys(password_input, password)
    password_confirm = wait_xpath(driver, "//input[@id='password-confirm']")
    safe_send_keys(password_confirm, password)

    # 7. Klik signup
    signup_btn = wait_xpath(driver, "//button[contains(text(),'Start using Proton Mail now')]")
    safe_click(signup_btn, sleep_time=2.5)

    # 8. Tunggu iframe challenge muncul (No thanks recovery)
    signup_iframe_xpath = "//iframe[@title='Email address']"
    nothanks_btn = wait_xpath(driver, "//button[contains(text(),'No, thanks')]")
    safe_click(nothanks_btn)
    switch_to_default(driver)

    # 9. Masuk lagi iframe challenge (tab Email)
    email_tab = wait_xpath(driver, "//button[@data-testid='tab-header-email-button']")
    safe_click(email_tab)

    # 10. Masukkan email verifikasi
    email_input = wait_xpath(driver, "//input[@id='email']")
    safe_send_keys(email_input, email_verif)

    # 11. Klik "Get verification code"
    getcode_btn = wait_xpath(driver, "//button[contains(text(),'Get verification code')]")
    safe_click(getcode_btn)
    
    # 12. Ambil kode OTP dari temp-gmail
    verif_code = get_proton_otp_from_temp_gmail(gmail, timeout=OTP_FETCH_TIMEOUT)
    if not verif_code:
        raise Exception(f"Gagal mendapatkan OTP dari temp-gmail untuk {email_verif}")
    code_input = wait_xpath(driver, "//input[@id='verification']")
    safe_send_keys(code_input, verif_code)

    # 13. Klik 'Verify'
    signup_iframe_xpath = "//iframe[@title='Email address']"
    verify_btn = wait_xpath(driver, "//button[contains(text(),'Verify')]")
    safe_click(verify_btn)
    switch_to_default(driver)

    # 14. Continue (iframe unauth)
    unauth_iframe_xpath = "//iframe[contains(@src,'Name=unauth')]"
    cont_btn = wait_xpath(driver, "//button[contains(text(),'Continue')]")
    safe_click(cont_btn)
    switch_to_default(driver)

    # 15. Maybe later
    unauth_iframe_xpath = "//iframe[contains(@src,'Name=unauth')]"
    later_btn = wait_xpath(driver, "//button[contains(text(),'Maybe later')]")
    safe_click(later_btn)
    switch_to_default(driver)

    # 16. Confirm
    unauth_iframe_xpath = "//iframe[contains(@src,'Name=unauth')]"
    conf_btn = wait_xpath(driver, "//button[contains(text(),'Confirm')]")
    safe_click(conf_btn)
    switch_to_default(driver)

    # 17. Klik Proton Mail (masih di iframe unauth)
    unauth_iframe_xpath = "//iframe[contains(@src,'Name=unauth')]"
    pmail_btn = wait_xpath(driver, "//div[contains(text(),'Proton Mail')]")
    safe_click(pmail_btn)
    switch_to_default(driver)

    # 18. Tunggu inbox load & screenshot
    print("[INFO] Tunggu inbox terbuka dan screenshot (20 detik)...")
    time.sleep(20)
    ss_path = f"screenshoot/{username}_protonmail.png"
    driver.save_screenshot(ss_path)
    print(f"[SUCCESS] Akun berhasil dibuat, screenshot: {ss_path}")

    # 19. Simpan email & password ke file
    with open("sukses_email.txt", "a") as f:
        f.write(f"{proton_email},{password}\n")
    print(f"[SUCCESS] Email dan password berhasil disimpan di sukses_email.txt")

except Exception as e:
    print(f"[CRITICAL ERROR] Terjadi kesalahan fatal: {e}")
    driver.save_screenshot(f"screenshoot/error_{username}_{int(time.time())}.png")

finally:
    print("[INFO] Proses selesai, menutup browser.")
    driver.quit()
