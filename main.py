import os
import time
import re
import random
import requests
import base64
import json
from faker import Faker
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

# --- KONFIGURASI CAPSOLVER ---
CAPSOLVER_API_KEY = "YOUR_CAPSOLVER_API_KEY_HERE"  # Ganti dengan API key CapSolver Anda
CAPTCHA_SOLVE_TIMEOUT = 300  # 5 menit timeout untuk solve captcha

def solve_capy_puzzle_with_capsolver(site_key, page_url, api_server=None):
    """Solve Capy puzzle captcha menggunakan CapSolver"""
    print(f"[CAPSOLVER] Memulai solve Capy puzzle captcha...")
    print(f"[CAPSOLVER] Site key: {site_key}")
    print(f"[CAPSOLVER] Page URL: {page_url}")
    
    submit_url = "https://api.capsolver.com/createTask"
    
    # Task data untuk Capy puzzle
    task_data = {
        "type": "CapyTaskProxyless",
        "websiteURL": page_url,
        "websiteKey": site_key
    }
    
    # Tambahkan API server jika ada
    if api_server:
        task_data["apiServer"] = api_server
        print(f"[CAPSOLVER] API Server: {api_server}")
    
    # Submit captcha ke CapSolver
    submit_data = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": task_data
    }
    
    try:
        response = requests.post(submit_url, json=submit_data, timeout=30)
        result = response.json()
        
        if result.get('errorId') != 0:
            print(f"[CAPSOLVER] Error submit: {result.get('errorDescription', 'Unknown error')}")
            return None
            
        task_id = result['taskId']
        print(f"[CAPSOLVER] Task ID: {task_id}")
        
        # Tunggu hasil solve
        result_url = "https://api.capsolver.com/getTaskResult"
        start_time = time.time()
        
        while time.time() - start_time < CAPTCHA_SOLVE_TIMEOUT:
            time.sleep(10)
            
            result_params = {
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id
            }
            
            response = requests.post(result_url, json=result_params, timeout=30)
            result = response.json()
            
            if result.get('status') == 'ready':
                solution = result['solution']
                capy_response = solution.get('captchakey', '')
                if capy_response:
                    print(f"[CAPSOLVER SUCCESS] Capy response: {capy_response[:50]}...")
                    return capy_response
                else:
                    print(f"[CAPSOLVER SUCCESS] Solution: {solution}")
                    return solution
            elif result.get('status') == 'processing':
                print(f"[CAPSOLVER] Masih diproses...")
                continue
            else:
                print(f"[CAPSOLVER ERROR] {result}")
                return None
                
        print(f"[CAPSOLVER TIMEOUT] Timeout setelah {CAPTCHA_SOLVE_TIMEOUT} detik")
        return None
        
    except Exception as e:
        print(f"[CAPSOLVER ERROR] {e}")
        return None

def find_capy_site_key(driver):
    """Cari site key Capy dari berbagai sumber"""
    print("[INFO] Mencari Capy site key...")
    
    # Method 1: Dari script tag
    try:
        scripts = driver.find_elements(By.TAG_NAME, "script")
        for script in scripts:
            script_content = script.get_attribute("innerHTML") or ""
            
            # Pattern untuk Capy site key
            patterns = [
                r'sitekey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'site_key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'SITE_KEY["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'capy_site_key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'data-sitekey["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, script_content, re.IGNORECASE)
                if matches:
                    site_key = matches[0]
                    print(f"[INFO] Site key ditemukan dari script: {site_key}")
                    return site_key
    except Exception as e:
        print(f"[WARNING] Error mencari di script: {e}")
    
    # Method 2: Dari data attributes
    try:
        capy_elements = driver.find_elements(By.XPATH, "//*[@data-sitekey or @data-site-key or contains(@class, 'capy')]")
        for element in capy_elements:
            site_key = element.get_attribute("data-sitekey") or element.get_attribute("data-site-key")
            if site_key:
                print(f"[INFO] Site key ditemukan dari element: {site_key}")
                return site_key
    except Exception as e:
        print(f"[WARNING] Error mencari di elements: {e}")
    
    # Method 3: Dari page source
    try:
        page_source = driver.page_source
        patterns = [
            r'sitekey["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]{20,})["\']',
            r'site_key["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]{20,})["\']',
            r'data-sitekey["\']?\s*=\s*["\']([a-zA-Z0-9_-]{20,})["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                site_key = matches[0]
                print(f"[INFO] Site key ditemukan dari page source: {site_key}")
                return site_key
    except Exception as e:
        print(f"[WARNING] Error mencari di page source: {e}")
    
    print("[WARNING] Site key tidak ditemukan")
    return None

def find_capy_api_server(driver):
    """Cari API server Capy jika ada"""
    try:
        page_source = driver.page_source
        patterns = [
            r'api[_-]?server["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'apiServer["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'server["\']?\s*[:=]\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                api_server = matches[0]
                if 'capy' in api_server.lower() or 'puzzle' in api_server.lower():
                    print(f"[INFO] API server ditemukan: {api_server}")
                    return api_server
    except Exception as e:
        print(f"[WARNING] Error mencari API server: {e}")
    
    return None

def submit_capy_response(driver, capy_response):
    """Submit response Capy ke form"""
    print(f"[INFO] Submitting Capy response...")
    
    # Method 1: Cari input hidden untuk capy response
    capy_inputs = [
        "//input[@name='capy_captchakey']",
        "//input[@name='captchakey']", 
        "//input[@name='capy-response']",
        "//input[@name='capy_response']",
        "//input[contains(@name, 'capy')]",
        "//input[@id='capy_captchakey']",
        "//input[@id='captchakey']"
    ]
    
    for input_xpath in capy_inputs:
        try:
            capy_input = driver.find_element(By.XPATH, input_xpath)
            if capy_input:
                driver.execute_script("arguments[0].value = arguments[1];", capy_input, capy_response)
                print(f"[SUCCESS] Capy response diset ke input: {input_xpath}")
                return True
        except:
            continue
    
    # Method 2: Execute JavaScript untuk set response
    js_methods = [
        f"window.capy_captchakey = '{capy_response}';",
        f"window.captchakey = '{capy_response}';",
        f"window.capy_response = '{capy_response}';",
        f"if(window.capy) {{ window.capy.response = '{capy_response}'; }}",
        f"if(window.Capy) {{ window.Capy.response = '{capy_response}'; }}"
    ]
    
    for js_method in js_methods:
        try:
            driver.execute_script(js_method)
            print(f"[INFO] Executed JS: {js_method}")
        except Exception as e:
            print(f"[WARNING] JS execution failed: {e}")
    
    return False

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
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_argument("--disable-plugins")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")

try:
    driver = uc.Chrome(options=options, version_main=None)
except Exception as e:
    print(f"[ERROR] Gagal membuat driver dengan options, coba tanpa options: {e}")
    driver = uc.Chrome()

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
    switch_to_iframe_xpath(driver, signup_iframe_xpath)

    # 6. Isi password dan konfirmasi password
    password_input = wait_xpath(driver, "//input[@id='password']")
    safe_send_keys(password_input, password)
    password_confirm = wait_xpath(driver, "//input[@id='password-confirm']")
    safe_send_keys(password_confirm, password)

    # 7. Klik signup
    signup_btn = wait_xpath(driver, "//button[contains(text(),'Start using Proton Mail now')]")
    safe_click(signup_btn, sleep_time=2.5)

    # 8. Tunggu iframe challenge muncul (No thanks recovery)
    nothanks_btn = wait_xpath(driver, "//button[contains(text(),'No, thanks')]")
    safe_click(nothanks_btn)
    switch_to_default(driver)

    # 9. Sekarang akan muncul CAPTCHA - tunggu modal muncul
    print("[INFO] Menunggu Capy CAPTCHA muncul...")
    time.sleep(5)
    
    # Cek apakah ada modal Human Verification
    captcha_modal = wait_xpath(driver, "//div[contains(text(), 'Human Verification')] | //h1[contains(text(), 'Human Verification')] | //h2[contains(text(), 'Human Verification')]", timeout=10)
    if captcha_modal:
        print("[INFO] Modal CAPTCHA ditemukan!")
        
        # Pastikan tab CAPTCHA aktif
        captcha_tab = driver.find_elements(By.XPATH, "//button[contains(text(), 'CAPTCHA')]")
        if captcha_tab:
            safe_click(captcha_tab[0])
            print("[INFO] Tab CAPTCHA diklik")
        
        # Tunggu Capy widget load
        time.sleep(5)
        
        # Cari site key dan API server
        site_key = find_capy_site_key(driver)
        if not site_key:
            print("[ERROR] Site key tidak ditemukan")
            raise Exception("Capy site key not found")
        
        api_server = find_capy_api_server(driver)
        current_url = driver.current_url
        
        # Solve Capy puzzle dengan CapSolver
        capy_response = solve_capy_puzzle_with_capsolver(site_key, current_url, api_server)
        
        if capy_response:
            print(f"[INFO] Menerapkan solusi Capy...")
            
            # Submit response ke form
            submit_success = submit_capy_response(driver, capy_response)
            
            if submit_success:
                print("[SUCCESS] Capy response berhasil disubmit!")
            else:
                print("[WARNING] Capy response mungkin tidak tersubmit dengan benar")
            
            # Tunggu sebentar lalu cari tombol Next/Submit
            time.sleep(3)
            
        else:
            print("[ERROR] CapSolver gagal solve Capy puzzle")
            raise Exception("CapSolver solve failed")
    else:
        print("[INFO] Modal CAPTCHA tidak muncul, mungkin tidak diperlukan")
    
    # 10. Lanjutkan proses setelah captcha
    print("[INFO] Melanjutkan proses setelah captcha...")
    time.sleep(5)
    
    # Cari dan klik tombol Next/Submit
    next_selectors = [
        "//button[contains(text(), 'Next')]",
        "//button[contains(@class, 'btn-solid-purple')]", 
        "//button[contains(text(), 'Submit')]",
        "//button[contains(text(), 'Verify')]",
        "//button[@type='submit']",
        "//input[@type='submit']"
    ]
    
    next_btn = None
    for selector in next_selectors:
        next_btn = wait_clickable_xpath(driver, selector, timeout=5)
        if next_btn:
            print(f"[INFO] Tombol Next ditemukan dengan selector: {selector}")
            break
    
    if next_btn:
        safe_click(next_btn)
        print("[INFO] Tombol Next diklik setelah solve captcha")
    
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