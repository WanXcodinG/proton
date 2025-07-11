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
from PIL import Image
import io
import cv2
import numpy as np

# --- KONFIGURASI ANTICAPTCHA (BACKUP) ---
ANTICAPTCHA_API_KEY = "YOUR_ANTICAPTCHA_API_KEY_HERE"  # Backup jika native solver gagal
CAPTCHA_SOLVE_TIMEOUT = 300  # 5 menit timeout untuk solve captcha

class ProtonCaptchaSolver:
    def __init__(self, session_cookies=None):
        self.session = requests.Session()
        self.session_cookies = session_cookies
        self.token = None
        self.contest_id = None
        self.bg_image = None
        self.puzzle_piece = None
        
        # Headers default
        self.headers = {
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
            'accept-language': "en-US,en;q=0.9",
            'priority': "u=1, i"
        }
        
        if session_cookies:
            self.headers['Cookie'] = session_cookies

    def init_captcha(self, token):
        """Initialize captcha dan dapatkan contest_id"""
        self.token = token
        url = f"https://account-api.proton.me/captcha/v1/api/init?challengeType=2D&parentURL=https%3A%2F%2Faccount-api.proton.me%2Fcore%2Fv4%2Fcaptcha%3FToken%3D{token}%26ForceWebMessaging%3D1&displayedLang=en&supportedLangs=en-US%2Cen-US%2Cen%2Cen-US%2Cen&purpose=signup&token={token}"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            print(f"[PROTON INIT] Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[PROTON INIT] Response: {data}")
                
                # Extract contest_id dan token baru
                if 'contestId' in data:
                    self.contest_id = data['contestId']
                if 'token' in data:
                    self.token = data['token']
                    
                print(f"[PROTON INIT] Contest ID: {self.contest_id}")
                print(f"[PROTON INIT] Token: {self.token}")
                return True
            return False
            
        except Exception as e:
            print(f"[PROTON INIT ERROR] {e}")
            return False

    def get_background_image(self):
        """Download background image"""
        if not self.token:
            return False
            
        url = f"https://account-api.proton.me/captcha/v1/api/bg?token={self.token}"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            print(f"[PROTON BG] Status: {response.status_code}")
            
            if response.status_code == 200:
                self.bg_image = response.content
                print(f"[PROTON BG] Background image downloaded: {len(self.bg_image)} bytes")
                return True
            return False
            
        except Exception as e:
            print(f"[PROTON BG ERROR] {e}")
            return False

    def get_puzzle_piece(self):
        """Download puzzle piece"""
        if not self.token:
            return False
            
        url = f"https://account-api.proton.me/captcha/v1/api/puzzle?token={self.token}"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            print(f"[PROTON PUZZLE] Status: {response.status_code}")
            
            if response.status_code == 200:
                self.puzzle_piece = response.content
                print(f"[PROTON PUZZLE] Puzzle piece downloaded: {len(self.puzzle_piece)} bytes")
                return True
            return False
            
        except Exception as e:
            print(f"[PROTON PUZZLE ERROR] {e}")
            return False

    def solve_puzzle_opencv(self):
        """Solve puzzle menggunakan OpenCV template matching"""
        if not self.bg_image or not self.puzzle_piece:
            print("[OPENCV] Background atau puzzle piece tidak tersedia")
            return None
            
        try:
            # Convert images
            bg_array = np.frombuffer(self.bg_image, np.uint8)
            puzzle_array = np.frombuffer(self.puzzle_piece, np.uint8)
            
            bg_img = cv2.imdecode(bg_array, cv2.IMREAD_COLOR)
            puzzle_img = cv2.imdecode(puzzle_array, cv2.IMREAD_COLOR)
            
            if bg_img is None or puzzle_img is None:
                print("[OPENCV] Gagal decode images")
                return None
            
            print(f"[OPENCV] Background size: {bg_img.shape}")
            print(f"[OPENCV] Puzzle size: {puzzle_img.shape}")
            
            # Template matching
            result = cv2.matchTemplate(bg_img, puzzle_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            print(f"[OPENCV] Match confidence: {max_val}")
            print(f"[OPENCV] Best match location: {max_loc}")
            
            if max_val > 0.3:  # Threshold confidence
                x, y = max_loc
                print(f"[OPENCV SUCCESS] Puzzle solution: x={x}, y={y}")
                return f"{x},{y}"
            else:
                print(f"[OPENCV] Confidence terlalu rendah: {max_val}")
                return None
                
        except Exception as e:
            print(f"[OPENCV ERROR] {e}")
            return None

    def validate_solution(self, x, y):
        """Validate solution ke Proton API"""
        if not self.token or not self.contest_id:
            return False
            
        url = f"https://account-api.proton.me/captcha/v1/api/validate?token={self.token}&contestId={self.contest_id}&purpose=signup&x={int(x)}&y={int(y)}"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            print(f"[PROTON VALIDATE] Status: {response.status_code}")
            print(f"[PROTON VALIDATE] Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') or data.get('valid') or data.get('status') == 'success':
                    print("[PROTON VALIDATE SUCCESS] Solution valid!")
                    return True
            return False
            
        except Exception as e:
            print(f"[PROTON VALIDATE ERROR] {e}")
            return False

    def finalize_captcha(self):
        """Finalize captcha setelah validation"""
        if not self.contest_id:
            return False
            
        url = f"https://account-api.proton.me/captcha/v1/api/finalize?contestId={self.contest_id}&purpose=signup"
        
        try:
            response = self.session.post(url, headers=self.headers, timeout=30)
            print(f"[PROTON FINALIZE] Status: {response.status_code}")
            print(f"[PROTON FINALIZE] Response: {response.text}")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"[PROTON FINALIZE ERROR] {e}")
            return False

def solve_captcha_native(token, session_cookies=None):
    """Main function untuk solve captcha menggunakan native API"""
    print(f"[NATIVE SOLVER] Memulai solve captcha untuk token: {token}")
    
    solver = ProtonCaptchaSolver(session_cookies)
    
    # Step 1: Initialize
    if not solver.init_captcha(token):
        print("[NATIVE SOLVER] Gagal initialize captcha")
        return False
    
    # Step 2: Download images
    if not solver.get_background_image():
        print("[NATIVE SOLVER] Gagal download background")
        return False
        
    if not solver.get_puzzle_piece():
        print("[NATIVE SOLVER] Gagal download puzzle piece")
        return False
    
    # Step 3: Solve puzzle
    solution = solver.solve_puzzle_opencv()
    if not solution:
        print("[NATIVE SOLVER] Gagal solve puzzle dengan OpenCV")
        return False
    
    # Step 4: Validate solution
    x, y = solution.split(',')
    if not solver.validate_solution(x, y):
        print("[NATIVE SOLVER] Solution tidak valid")
        return False
    
    # Step 5: Finalize
    if not solver.finalize_captcha():
        print("[NATIVE SOLVER] Gagal finalize captcha")
        return False
    
    print("[NATIVE SOLVER SUCCESS] Captcha berhasil diselesaikan!")
    return True

def solve_puzzle_captcha_with_anticaptcha(puzzle_image_base64, page_url, captcha_data=None):
    """Backup solver menggunakan AntiCaptcha jika native gagal"""
    print(f"[ANTICAPTCHA BACKUP] Menggunakan AntiCaptcha sebagai backup...")
    
    submit_url = "https://api.anti-captcha.com/createTask"
    
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
            print(f"[ANTICAPTCHA] Error: {result.get('errorDescription', 'Unknown error')}")
            return None
            
        task_id = result['taskId']
        print(f"[ANTICAPTCHA] Task ID: {task_id}")
        
        # Tunggu hasil solve
        result_url = "https://api.anti-captcha.com/getTaskResult"
        start_time = time.time()
        
        while time.time() - start_time < CAPTCHA_SOLVE_TIMEOUT:
            time.sleep(15)
            
            result_data = {
                "clientKey": ANTICAPTCHA_API_KEY,
                "taskId": task_id
            }
            
            response = requests.post(result_url, json=result_data, timeout=30)
            result = response.json()
            
            if result.get('status') == 'ready':
                solution = result['solution']['answers']['coordinates']
                print(f"[ANTICAPTCHA SUCCESS] Solution: {solution}")
                return solution
            elif result.get('status') == 'processing':
                print(f"[ANTICAPTCHA] Masih diproses...")
                continue
            else:
                print(f"[ANTICAPTCHA ERROR] {result}")
                return None
                
        print(f"[ANTICAPTCHA TIMEOUT] Timeout")
        return None
        
    except Exception as e:
        print(f"[ANTICAPTCHA ERROR] {e}")
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
    """Extract token dari URL atau page source"""
    try:
        current_url = driver.current_url
        print(f"[INFO] Current URL: {current_url}")
        
        # Cari token di URL
        token_match = re.search(r'[Tt]oken[=%]([A-Za-z0-9_-]+)', current_url)
        if token_match:
            token = token_match.group(1)
            print(f"[INFO] Token ditemukan di URL: {token}")
            return token
        
        # Cari token di page source
        page_source = driver.page_source
        token_matches = re.findall(r'[Tt]oken["\':=\s]+([A-Za-z0-9_-]{20,})', page_source)
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
    """Ambil cookies dari browser untuk API request"""
    try:
        cookies = driver.get_cookies()
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        print(f"[INFO] Cookies: {cookie_string[:100]}...")
        return cookie_string
    except Exception as e:
        print(f"[ERROR] Gagal ambil cookies: {e}")
        return None

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
    print("[INFO] Menunggu CAPTCHA muncul...")
    time.sleep(5)
    
    # Extract token dan cookies untuk API
    token = extract_token_from_url(driver)
    session_cookies = get_session_cookies(driver)
    
    # Cek apakah ada modal Human Verification
    captcha_modal = wait_xpath(driver, "//div[contains(text(), 'Human Verification')] | //h1[contains(text(), 'Human Verification')] | //h2[contains(text(), 'Human Verification')]", timeout=10)
    if captcha_modal:
        print("[INFO] Modal CAPTCHA ditemukan!")
        
        # Coba solve dengan native API dulu
        captcha_solved = False
        if token:
            print("[INFO] Mencoba solve captcha dengan native API...")
            captcha_solved = solve_captcha_native(token, session_cookies)
        
        # Jika native gagal, gunakan AntiCaptcha sebagai backup
        if not captcha_solved:
            print("[INFO] Native solver gagal, menggunakan AntiCaptcha backup...")
            
            # Pastikan tab CAPTCHA aktif
            captcha_tab = driver.find_elements(By.XPATH, "//button[contains(text(), 'CAPTCHA')]")
            if captcha_tab:
                safe_click(captcha_tab[0])
                print("[INFO] Tab CAPTCHA diklik")
            
            # Tunggu puzzle muncul
            time.sleep(3)
            
            # Cari area puzzle captcha
            puzzle_container = wait_xpath(driver, "//canvas[@width='370'] | //div[contains(@class, 'protonCaptchaContainer')] | //div[contains(@class, 'challenge-canvas')] | //canvas | //div[contains(text(), 'Complete the puzzle')]", timeout=10)
            
            if puzzle_container:
                print("[INFO] Container puzzle ditemukan untuk backup solver")
                
                # Screenshot area puzzle
                puzzle_screenshot = puzzle_container.screenshot_as_base64
                current_url = driver.current_url
                
                # Solve puzzle captcha dengan AntiCaptcha
                captcha_solution = solve_puzzle_captcha_with_anticaptcha(puzzle_screenshot, current_url)
                
                if captcha_solution:
                    print(f"[INFO] Menerapkan solusi backup: {captcha_solution}")
                    
                    # Parse koordinat dari solusi
                    try:
                        if ',' in captcha_solution:
                            coords = captcha_solution.split(',')
                            x = int(coords[0].strip())
                            y = int(coords[1].strip())
                        else:
                            x, y = 300, 200
                        
                        print(f"[INFO] Koordinat backup: x={x}, y={y}")
                        
                        # Drag puzzle piece
                        ActionChains(driver).drag_and_drop_by_offset(puzzle_container, x, y).perform()
                        time.sleep(2)
                        
                        captcha_solved = True
                        
                    except Exception as e:
                        print(f"[WARNING] Gagal apply backup solution: {e}")
                else:
                    print("[ERROR] Backup solver juga gagal")
        
        if captcha_solved:
            print("[SUCCESS] CAPTCHA berhasil diselesaikan!")
            
            # Cari dan klik tombol Next/Submit
            next_btn = wait_clickable_xpath(driver, "//button[contains(text(), 'Next')] | //button[contains(@class, 'btn-solid-purple')] | //button[contains(text(), 'Submit')] | //button[contains(text(), 'Verify')]", timeout=10)
            if next_btn:
                safe_click(next_btn)
                print("[INFO] Tombol Next diklik setelah solve captcha")
        else:
            print("[ERROR] Semua metode solve captcha gagal")
            raise Exception("Captcha solve failed")
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