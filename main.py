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

# --- KONFIGURASI ANTICAPTCHA ---
ANTICAPTCHA_API_KEY = "YOUR_ANTICAPTCHA_API_KEY_HERE"  # Ganti dengan API key AntiCaptcha Anda
CAPTCHA_SOLVE_TIMEOUT = 300  # 5 menit timeout untuk solve captcha

def get_proton_captcha_data(token, session_cookies=None):
    """
    Mengambil data captcha dari API Proton
    """
    url = f"https://account-api.proton.me/captcha/v1/api/init?challengeType=2D&parentURL=https%3A%2F%2Faccount-api.proton.me%2Fcore%2Fv4%2Fcaptcha%3FToken%3D{token}%26ForceWebMessaging%3D1&displayedLang=en&supportedLangs=en-US%2Cen-US%2Cen%2Cen-US%2Cen&purpose=signup&token={token}"
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'cache-control': "max-age=0",
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'content-type': "application/json",
        'sec-ch-ua-mobile': "?0",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"https://account-api.proton.me/captcha/v1/assets/?purpose=signup&token={token}",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i"
    }
    
    if session_cookies:
        headers['Cookie'] = session_cookies
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"[PROTON API] Response status: {response.status_code}")
        print(f"[PROTON API] Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[PROTON API ERROR] Status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[PROTON API ERROR] Exception: {e}")
        return None

def solve_puzzle_captcha_with_anticaptcha(puzzle_image_base64, page_url, captcha_data=None):
    """
    Menyelesaikan puzzle CAPTCHA menggunakan layanan AntiCaptcha
    """
    print(f"[ANTICAPTCHA] Memulai solve puzzle captcha untuk site: {page_url}")
    
    # Coba method CustomCaptchaTask dulu untuk puzzle
    submit_url = "https://api.anti-captcha.com/createTask"
    
    # Method 1: CustomCaptchaTask untuk puzzle yang kompleks
    submit_data = {
        "clientKey": ANTICAPTCHA_API_KEY,
        "task": {
            "type": "CustomCaptchaTask",
            "imageUrl": f"data:image/png;base64,{puzzle_image_base64}",
            "assignment": "Complete the puzzle by dragging the puzzle piece to the correct position. Look at the image and determine where the missing puzzle piece should be placed to complete the picture.",
            "forms": [
                {
                    "label": "Puzzle solution coordinates",
                    "labelHint": "Enter the x,y coordinates where the puzzle piece should be placed (format: x,y)",
                    "contentType": "text",
                    "name": "coordinates"
                }
            ]
        }
    }
    
    try:
        response = requests.post(submit_url, json=submit_data, timeout=30)
        result = response.json()
        
        if result.get('errorId') != 0:
            print(f"[ANTICAPTCHA] CustomCaptchaTask gagal: {result.get('errorDescription', 'Unknown error')}")
            # Fallback ke ImageToTextTask
            return solve_puzzle_fallback(puzzle_image_base64, page_url)
            
        task_id = result['taskId']
        print(f"[ANTICAPTCHA] Custom Task ID: {task_id}")
        
        # Tunggu hasil solve
        result_url = "https://api.anti-captcha.com/getTaskResult"
        start_time = time.time()
        
        while time.time() - start_time < CAPTCHA_SOLVE_TIMEOUT:
            time.sleep(15)  # Custom captcha butuh waktu lebih lama
            
            result_data = {
                "clientKey": ANTICAPTCHA_API_KEY,
                "taskId": task_id
            }
            
            response = requests.post(result_url, json=result_data, timeout=30)
            result = response.json()
            
            if result.get('status') == 'ready':
                solution = result['solution']['answers']['coordinates']
                print(f"[ANTICAPTCHA SUCCESS] Custom captcha berhasil diselesaikan: {solution}")
                return solution
            elif result.get('status') == 'processing':
                print(f"[ANTICAPTCHA] Custom captcha masih diproses...")
                continue
            else:
                print(f"[ANTICAPTCHA ERROR] Custom captcha error: {result}")
                # Fallback ke method biasa
                return solve_puzzle_fallback(puzzle_image_base64, page_url)
                
        print(f"[ANTICAPTCHA TIMEOUT] Custom captcha tidak selesai dalam {CAPTCHA_SOLVE_TIMEOUT} detik")
        return solve_puzzle_fallback(puzzle_image_base64, page_url)
        
    except Exception as e:
        print(f"[ANTICAPTCHA ERROR] Custom captcha exception: {e}")
        # Fallback ke method biasa
        return solve_puzzle_fallback(puzzle_image_base64, page_url)

def solve_puzzle_fallback(puzzle_image_base64, page_url):
    """
    Fallback method menggunakan ImageToTextTask
    """
    print(f"[ANTICAPTCHA] Menggunakan fallback ImageToTextTask...")
    
    submit_url = "https://api.anti-captcha.com/createTask"
    submit_data = {
        "clientKey": ANTICAPTCHA_API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": puzzle_image_base64,
            "phrase": False,
            "case": False,
            "numeric": 0,
            "math": False,
            "minLength": 0,
            "maxLength": 0,
            "comment": "Drag puzzle piece to correct position. Return coordinates as x,y where the puzzle piece should be placed."
        }
    }
    
    try:
        response = requests.post(submit_url, json=submit_data, timeout=30)
        result = response.json()
        
        if result.get('errorId') != 0:
            print(f"[ANTICAPTCHA ERROR] Fallback gagal: {result}")
            return None
            
        task_id = result['taskId']
        print(f"[ANTICAPTCHA] Fallback Task ID: {task_id}")
        
        # Tunggu hasil solve
        result_url = "https://api.anti-captcha.com/getTaskResult"
        start_time = time.time()
        
        while time.time() - start_time < CAPTCHA_SOLVE_TIMEOUT:
            time.sleep(10)
            
            result_data = {
                "clientKey": ANTICAPTCHA_API_KEY,
                "taskId": task_id
            }
            
            response = requests.post(result_url, json=result_data, timeout=30)
            result = response.json()
            
            if result.get('status') == 'ready':
                captcha_solution = result['solution']['text']
                print(f"[ANTICAPTCHA SUCCESS] Fallback berhasil: {captcha_solution}")
                return captcha_solution
            elif result.get('status') == 'processing':
                print(f"[ANTICAPTCHA] Fallback masih diproses...")
                continue
            else:
                print(f"[ANTICAPTCHA ERROR] Fallback error: {result}")
                return None
                
        print(f"[ANTICAPTCHA TIMEOUT] Fallback timeout")
        return None
        
    except Exception as e:
        print(f"[ANTICAPTCHA ERROR] Fallback exception: {e}")
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

def extract_token_from_url(driver):
    """
    Extract token dari URL atau page source
    """
    try:
        current_url = driver.current_url
        print(f"[INFO] Current URL: {current_url}")
        
        # Cari token di URL
        token_match = re.search(r'[Tt]oken[=%]([A-Za-z0-9]+)', current_url)
        if token_match:
            token = token_match.group(1)
            print(f"[INFO] Token ditemukan di URL: {token}")
            return token
        
        # Cari token di page source
        page_source = driver.page_source
        token_matches = re.findall(r'[Tt]oken["\':=\s]+([A-Za-z0-9]{20,})', page_source)
        if token_matches:
            token = token_matches[0]
            print(f"[INFO] Token ditemukan di page source: {token}")
            return token
            
        print("[WARNING] Token tidak ditemukan")
        return None
        
    except Exception as e:
        print(f"[ERROR] Gagal extract token: {e}")
        return None

def get_session_cookies(driver):
    """
    Ambil cookies dari browser untuk API request
    """
    try:
        cookies = driver.get_cookies()
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        print(f"[INFO] Cookies: {cookie_string[:100]}...")
        return cookie_string
    except Exception as e:
        print(f"[ERROR] Gagal ambil cookies: {e}")
        return None

# --- PROSES SIGNUP PROTONMAIL ---
# Konfigurasi Chrome options yang lebih kompatibel
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
    # Fallback tanpa options
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
    print("[INFO] Menunggu CAPTCHA muncul...")
    time.sleep(5)
    
    # Extract token dan cookies untuk API
    token = extract_token_from_url(driver)
    session_cookies = get_session_cookies(driver)
    
    # Cek apakah ada modal Human Verification
    captcha_modal = wait_xpath(driver, "//div[contains(text(), 'Human Verification')] | //h1[contains(text(), 'Human Verification')] | //h2[contains(text(), 'Human Verification')]", timeout=10)
    if captcha_modal:
        print("[INFO] Modal CAPTCHA ditemukan!")
        
        # Ambil data captcha dari API jika token tersedia
        captcha_api_data = None
        if token:
            captcha_api_data = get_proton_captcha_data(token, session_cookies)
        
        # Pastikan tab CAPTCHA aktif (biasanya sudah default)
        captcha_tab = driver.find_elements(By.XPATH, "//button[contains(text(), 'CAPTCHA')]")
        if captcha_tab:
            safe_click(captcha_tab[0])
            print("[INFO] Tab CAPTCHA diklik")
        
        # Tunggu puzzle muncul
        time.sleep(3)
        
        # Cari area puzzle captcha dengan selector yang lebih spesifik
        puzzle_container = wait_xpath(driver, "//canvas[@width='370'] | //div[contains(@class, 'protonCaptchaContainer')] | //div[contains(@class, 'challenge-canvas')] | //canvas | //div[contains(text(), 'Complete the puzzle')]", timeout=10)
        
        if puzzle_container:
            print("[INFO] Container puzzle ditemukan")
            
            # Screenshot area puzzle
            print("[INFO] Mengambil screenshot puzzle captcha...")
            puzzle_screenshot = puzzle_container.screenshot_as_base64
            
            current_url = driver.current_url
            
            # Solve puzzle captcha dengan AntiCaptcha
            captcha_solution = solve_puzzle_captcha_with_anticaptcha(puzzle_screenshot, current_url, captcha_api_data)
            
            if captcha_solution:
                print(f"[INFO] Menerapkan solusi puzzle captcha: {captcha_solution}")
                
                # Parse koordinat dari solusi
                try:
                    # Coba berbagai format koordinat
                    if ',' in captcha_solution:
                        coords = captcha_solution.split(',')
                        x = int(coords[0].strip())
                        y = int(coords[1].strip())
                    elif ':' in captcha_solution:
                        coords = captcha_solution.split(':')
                        x = int(coords[0].strip())
                        y = int(coords[1].strip())
                    elif ' ' in captcha_solution:
                        coords = captcha_solution.split()
                        x = int(coords[0])
                        y = int(coords[1])
                    else:
                        # Jika format tidak dikenali, gunakan koordinat tengah
                        x, y = 300, 200
                    
                    print(f"[INFO] Koordinat puzzle: x={x}, y={y}")
                    
                    # Cari puzzle piece yang bisa di-drag
                    puzzle_pieces = driver.find_elements(By.XPATH, "//canvas[@width='370'] | //div[contains(@class, 'challenge-canvas')] | //*[@draggable='true'] | //div[contains(@class, 'piece')] | //canvas")
                    
                    if puzzle_pieces:
                        puzzle_piece = puzzle_pieces[0]
                        print("[INFO] Puzzle piece ditemukan, melakukan drag...")
                        
                        # Drag puzzle piece ke koordinat yang diberikan
                        ActionChains(driver).drag_and_drop_by_offset(puzzle_piece, x, y).perform()
                        time.sleep(2)
                        
                        print("[INFO] Puzzle piece berhasil di-drag")
                    else:
                        print("[WARNING] Puzzle piece tidak ditemukan, coba klik koordinat langsung")
                        # Fallback: klik langsung di koordinat
                        ActionChains(driver).move_to_element(puzzle_container).move_by_offset(x, y).click().perform()
                        
                except ValueError as e:
                    print(f"[WARNING] Gagal parse koordinat: {e}, menggunakan koordinat default")
                    # Gunakan koordinat tengah sebagai fallback
                    ActionChains(driver).move_to_element(puzzle_container).move_by_offset(300, 200).click().perform()
                
                # Tunggu sebentar setelah solve
                time.sleep(3)
                
                # Cari dan klik tombol Next/Submit
                next_btn = wait_clickable_xpath(driver, "//button[contains(text(), 'Next')] | //button[contains(@class, 'btn-solid-purple')] | //button[contains(text(), 'Submit')] | //button[contains(text(), 'Verify')]", timeout=10)
                if next_btn:
                    safe_click(next_btn)
                    print("[INFO] Tombol Next diklik setelah solve captcha")
                else:
                    print("[WARNING] Tombol Next tidak ditemukan, mencoba selector lain...")
                    # Coba cari button dengan warna purple atau yang terlihat di modal
                    purple_btn = driver.find_elements(By.XPATH, "//button[contains(@class, 'purple')] | //button[@type='submit'] | //div[@class='modal']//button")
                    if purple_btn:
                        safe_click(purple_btn[0])
                        print("[INFO] Button purple diklik")
            else:
                print("[ERROR] Gagal menyelesaikan captcha dengan AntiCaptcha")
                raise Exception("Captcha solve failed")
        else:
            print("[WARNING] Container puzzle captcha tidak ditemukan")
    else:
        print("[INFO] Modal CAPTCHA tidak muncul, mungkin tidak diperlukan")
    
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