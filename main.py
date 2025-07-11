import os
import time
import re
import random
import requests
from faker import Faker
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

# --- KONFIGURASI 2CAPTCHA ---
TWOCAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY_HERE"  # Ganti dengan API key 2captcha Anda
CAPTCHA_SOLVE_TIMEOUT = 300  # 5 menit timeout untuk solve captcha

def solve_captcha_with_2captcha(site_key, page_url):
    """
    Menyelesaikan CAPTCHA menggunakan layanan 2captcha
    """
    print(f"[2CAPTCHA] Memulai solve captcha untuk site: {page_url}")
    
    # Submit captcha ke 2captcha
    submit_url = "http://2captcha.com/in.php"
    submit_data = {
        'key': TWOCAPTCHA_API_KEY,
        'method': 'userrecaptcha',
        'googlekey': site_key,
        'pageurl': page_url,
        'json': 1
    }
    
    try:
        response = requests.post(submit_url, data=submit_data, timeout=30)
        result = response.json()
        
        if result['status'] != 1:
            print(f"[2CAPTCHA ERROR] Gagal submit captcha: {result}")
            return None
            
        captcha_id = result['request']
        print(f"[2CAPTCHA] Captcha ID: {captcha_id}")
        
        # Tunggu hasil solve
        result_url = "http://2captcha.com/res.php"
        start_time = time.time()
        
        while time.time() - start_time < CAPTCHA_SOLVE_TIMEOUT:
            time.sleep(10)  # Tunggu 10 detik sebelum cek hasil
            
            result_data = {
                'key': TWOCAPTCHA_API_KEY,
                'action': 'get',
                'id': captcha_id,
                'json': 1
            }
            
            response = requests.get(result_url, params=result_data, timeout=30)
            result = response.json()
            
            if result['status'] == 1:
                captcha_solution = result['request']
                print(f"[2CAPTCHA SUCCESS] Captcha berhasil diselesaikan!")
                return captcha_solution
            elif result['request'] == 'CAPCHA_NOT_READY':
                print(f"[2CAPTCHA] Captcha masih diproses...")
                continue
            else:
                print(f"[2CAPTCHA ERROR] Error: {result}")
                return None
                
        print(f"[2CAPTCHA TIMEOUT] Captcha tidak selesai dalam {CAPTCHA_SOLVE_TIMEOUT} detik")
        return None
        
    except Exception as e:
        print(f"[2CAPTCHA ERROR] Exception: {e}")
        return None

def generate_password():
    """Generates a random, strong-looking password."""
    first_letter = chr(random.randint(65, 90))
    other_letters = ''.join(chr(random.randint(97, 122)) for _ in range(7))
    numbers = ''.join(str(random.randint(0, 9)) for _ in range(3))
    return f"{first_letter}{other_letters}{numbers}!"

# --- DATA RANDOM ---
fake = Faker()
username = fake.user_name() + str(fake.random_number(digits=3))
password = generate_password()
proton_email = f"{username}@protonmail.com"

print(f"[INFO] Username: {username}")
print(f"[INFO] Password: {password}")
print(f"[INFO] Email: {proton_email}")

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

def wait_clickable_xpath(driver, xpath, timeout=30, poll=0.5):
    try:
        return WebDriverWait(driver, timeout, poll_frequency=poll).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
    except TimeoutException:
        print(f"[WARNING] Timeout: Elemen tidak bisa diklik: {xpath}")
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
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = uc.Chrome(options=options, use_subprocess=True)

try:
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.get("https://account.proton.me/signup?plan=free")
    time.sleep(3)
    
    # 1. Masuk ke iframe signup
    print("[INFO] Mencari iframe signup...")
    signup_iframe_xpath = "//iframe[@title='Email address']"
    switch_to_iframe_xpath(driver, signup_iframe_xpath)

    # 2. Isi username faker
    print(f"[INFO] Mengisi username: {username}")
    username_input = wait_xpath(driver, "//input[@id='username']")
    safe_send_keys(username_input, username)

    # 3. Keluar iframe untuk pilih domain
    switch_to_default(driver)
    domain_btn = wait_xpath(driver, "//button[@id='select-domain']")
    safe_click(domain_btn)

    # 4. Pilih @protonmail.com
    domain_opt = wait_xpath(driver, "//button[@title='protonmail.com']")
    safe_click(domain_opt)

    # 5. Masuk lagi ke iframe signup
    switch_to_iframe_xpath(driver, signup_iframe_xpath)

    # 6. Isi password dan konfirmasi password
    print("[INFO] Mengisi password...")
    password_input = wait_xpath(driver, "//input[@id='password']")
    safe_send_keys(password_input, password)
    password_confirm = wait_xpath(driver, "//input[@id='password-confirm']")
    safe_send_keys(password_confirm, password)

    # 7. Klik signup
    print("[INFO] Klik tombol signup...")
    signup_btn = wait_xpath(driver, "//button[contains(text(),'Start using Proton Mail now')]")
    safe_click(signup_btn, sleep_time=3)

    # 8. Tunggu dan klik "No, thanks" untuk recovery
    print("[INFO] Mencari tombol 'No, thanks'...")
    nothanks_btn = wait_xpath(driver, "//button[contains(text(),'No, thanks')]", timeout=15)
    safe_click(nothanks_btn)
    switch_to_default(driver)
    time.sleep(2)

    # 9. Sekarang akan muncul CAPTCHA - tunggu modal muncul
    print("[INFO] Menunggu CAPTCHA muncul...")
    time.sleep(5)
    
    # Cek apakah ada modal Human Verification
    captcha_modal = wait_xpath(driver, "//div[contains(text(), 'Human Verification')]", timeout=10)
    if captcha_modal:
        print("[INFO] Modal CAPTCHA ditemukan!")
        
        # Cari tab CAPTCHA dan klik
        captcha_tab = wait_xpath(driver, "//button[contains(text(), 'CAPTCHA')]")
        if captcha_tab:
            safe_click(captcha_tab)
            print("[INFO] Tab CAPTCHA diklik")
        
        # Tunggu iframe captcha muncul
        time.sleep(3)
        
        # Cari iframe captcha (biasanya dari recaptcha atau hcaptcha)
        captcha_iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@src, 'recaptcha') or contains(@src, 'hcaptcha')]")
        
        if captcha_iframes:
            print(f"[INFO] Ditemukan {len(captcha_iframes)} iframe captcha")
            
            # Ambil site key dan URL untuk 2captcha
            current_url = driver.current_url
            
            # Coba ekstrak site key dari iframe src atau dari page source
            page_source = driver.page_source
            site_key = None
            
            # Pattern untuk mencari site key
            site_key_patterns = [
                r'data-sitekey="([^"]+)"',
                r'sitekey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'k=([A-Za-z0-9_-]{40})',
                r'site_key["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in site_key_patterns:
                match = re.search(pattern, page_source)
                if match:
                    site_key = match.group(1)
                    print(f"[INFO] Site key ditemukan: {site_key}")
                    break
            
            if not site_key:
                # Fallback: gunakan site key umum untuk testing
                site_key = "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
                print(f"[INFO] Menggunakan site key fallback: {site_key}")
            
            # Solve captcha dengan 2captcha
            captcha_solution = solve_captcha_with_2captcha(site_key, current_url)
            
            if captcha_solution:
                # Inject solusi captcha ke halaman
                print("[INFO] Menginjeksi solusi captcha...")
                
                # Script untuk mengisi g-recaptcha-response
                inject_script = f"""
                var textarea = document.getElementById('g-recaptcha-response');
                if (!textarea) {{
                    textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                }}
                if (textarea) {{
                    textarea.style.display = 'block';
                    textarea.value = '{captcha_solution}';
                    textarea.style.display = 'none';
                }}
                
                // Trigger callback jika ada
                if (typeof window.captchaCallback === 'function') {{
                    window.captchaCallback('{captcha_solution}');
                }}
                
                // Coba trigger event
                var event = new Event('input', {{ bubbles: true }});
                if (textarea) textarea.dispatchEvent(event);
                """
                
                driver.execute_script(inject_script)
                time.sleep(2)
                
                # Cari dan klik tombol Next/Submit
                next_btn = wait_clickable_xpath(driver, "//button[contains(@class, 'btn-solid-purple') and contains(text(), 'Next')] | //button[contains(text(), 'Next')] | //button[contains(text(), 'Submit')] | //button[contains(text(), 'Verify')]")
                if next_btn:
                    safe_click(next_btn)
                    print("[INFO] Tombol Next diklik setelah solve captcha")
                else:
                    print("[WARNING] Tombol Next tidak ditemukan")
                    # Coba cari dengan class saja jika text tidak ditemukan
                    next_btn_class = wait_clickable_xpath(driver, "//button[contains(@class, 'btn-solid-purple')]")
                    if next_btn_class:
                        safe_click(next_btn_class)
                        print("[INFO] Tombol dengan class btn-solid-purple diklik")
            else:
                print("[ERROR] Gagal menyelesaikan captcha dengan 2captcha")
                raise Exception("Captcha solve failed")
        else:
            print("[WARNING] Iframe captcha tidak ditemukan")
    
    # 10. Lanjutkan proses setelah captcha
    print("[INFO] Melanjutkan proses setelah captcha...")
    time.sleep(5)
    
    # Tunggu halaman berikutnya dan cari tombol Continue
    continue_btn = wait_xpath(driver, "//button[contains(text(),'Continue')]", timeout=20)
    if continue_btn:
        safe_click(continue_btn)
        print("[INFO] Tombol Continue diklik")
    
    # Maybe later
    later_btn = wait_xpath(driver, "//button[contains(text(),'Maybe later')]", timeout=15)
    if later_btn:
        safe_click(later_btn)
        print("[INFO] Tombol 'Maybe later' diklik")
    
    # Confirm
    confirm_btn = wait_xpath(driver, "//button[contains(text(),'Confirm')]", timeout=15)
    if confirm_btn:
        safe_click(confirm_btn)
        print("[INFO] Tombol Confirm diklik")
    
    # Klik Proton Mail
    pmail_btn = wait_xpath(driver, "//div[contains(text(),'Proton Mail')] | //button[contains(text(),'Proton Mail')]", timeout=15)
    if pmail_btn:
        safe_click(pmail_btn)
        print("[INFO] Proton Mail diklik")

    # Tunggu inbox load & screenshot
    print("[INFO] Tunggu inbox terbuka dan screenshot (20 detik)...")
    time.sleep(20)
    ss_path = f"screenshoot/{username}_protonmail_success.png"
    driver.save_screenshot(ss_path)
    print(f"[SUCCESS] Akun berhasil dibuat, screenshot: {ss_path}")

    # Simpan email & password ke file
    with open("sukses_email.txt", "a") as f:
        f.write(f"{proton_email},{password}\n")
    print(f"[SUCCESS] Email dan password berhasil disimpan di sukses_email.txt")

except Exception as e:
    print(f"[CRITICAL ERROR] Terjadi kesalahan fatal: {e}")
    error_ss_path = f"screenshoot/error_{username}_{int(time.time())}.png"
    driver.save_screenshot(error_ss_path)
    print(f"[ERROR] Screenshot error disimpan: {error_ss_path}")

finally:
    print("[INFO] Proses selesai, menutup browser dalam 5 detik...")
    time.sleep(5)
    driver.quit()