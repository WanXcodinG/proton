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

# --- KONFIGURASI 2CAPTCHA ---
TWOCAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY_HERE"  # Ganti dengan API key 2captcha Anda
CAPTCHA_SOLVE_TIMEOUT = 300  # 5 menit timeout untuk solve captcha

def solve_puzzle_captcha_with_2captcha(puzzle_image_base64, page_url):
    """Solve puzzle captcha menggunakan 2captcha"""
    print(f"[2CAPTCHA] Memulai solve puzzle captcha...")
    
    submit_url = "http://2captcha.com/in.php"
    
    # Submit captcha ke 2captcha
    submit_data = {
        "key": TWOCAPTCHA_API_KEY,
        "method": "base64",
        "body": puzzle_image_base64,
        "textinstructions": "Complete the puzzle by dragging the puzzle piece to the correct position. Look at the image and determine where the missing puzzle piece should be placed to complete the picture. Return coordinates in format: x,y where x and y are the pixel coordinates where the piece should be placed.",
        "json": 1
    }
    
    try:
        response = requests.post(submit_url, data=submit_data, timeout=30)
        result = response.json()
        
        if result.get('status') != 1:
            print(f"[2CAPTCHA] Error submit: {result.get('error_text', 'Unknown error')}")
            return None
            
        captcha_id = result['request']
        print(f"[2CAPTCHA] Captcha ID: {captcha_id}")
        
        # Tunggu hasil solve
        result_url = "http://2captcha.com/res.php"
        start_time = time.time()
        
        while time.time() - start_time < CAPTCHA_SOLVE_TIMEOUT:
            time.sleep(15)
            
            result_params = {
                "key": TWOCAPTCHA_API_KEY,
                "action": "get",
                "id": captcha_id,
                "json": 1
            }
            
            response = requests.get(result_url, params=result_params, timeout=30)
            result = response.json()
            
            if result.get('status') == 1:
                solution = result['request']
                print(f"[2CAPTCHA SUCCESS] Solution: {solution}")
                return solution
            elif result.get('error_text') == 'CAPCHA_NOT_READY':
                print(f"[2CAPTCHA] Masih diproses...")
                continue
            else:
                print(f"[2CAPTCHA ERROR] {result}")
                return None
                
        print(f"[2CAPTCHA TIMEOUT] Timeout setelah {CAPTCHA_SOLVE_TIMEOUT} detik")
        return None
        
    except Exception as e:
        print(f"[2CAPTCHA ERROR] {e}")
        return None

def parse_coordinates(solution):
    """Parse koordinat dari berbagai format solution"""
    if not solution:
        return None, None
        
    try:
        # Format: "x,y" atau "x:y" atau "x y"
        coords = re.findall(r'(\d+)[,:\s]+(\d+)', solution)
        if coords:
            x, y = coords[0]
            return int(x), int(y)
        
        # Format: hanya angka "123 456"
        numbers = re.findall(r'\d+', solution)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
            
        print(f"[WARNING] Tidak bisa parse koordinat: {solution}")
        return None, None
        
    except Exception as e:
        print(f"[ERROR] Parse koordinat gagal: {e}")
        return None, None

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
    print("[INFO] Menunggu CAPTCHA muncul...")
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
        
        # Tunggu puzzle muncul
        time.sleep(3)
        
        # Cari iframe captcha terlebih dahulu
        captcha_iframe = None
        iframe_selectors = [
            "//iframe[contains(@src, 'captcha')]",
            "//iframe[contains(@title, 'captcha')]",
            "//iframe[contains(@name, 'captcha')]",
            "//iframe[@id='captcha']",
            "//iframe[contains(@src, 'proton')]"
        ]
        
        for iframe_selector in iframe_selectors:
            captcha_iframe = wait_xpath(driver, iframe_selector, timeout=3)
            if captcha_iframe:
                print(f"[INFO] CAPTCHA iframe ditemukan: {iframe_selector}")
                try:
                    driver.switch_to.frame(captcha_iframe)
                    print("[INFO] Berhasil switch ke iframe captcha")
                    time.sleep(2)
                    break
                except Exception as e:
                    print(f"[WARNING] Gagal switch ke iframe: {e}")
                    driver.switch_to.default_content()
        
        # Cari canvas puzzle dengan selector yang tepat
        canvas_selectors = [
            "//canvas[@width='370' and @height='400']",
            "//canvas[@width='370']",
            "//canvas[contains(@style, 'width: 370px')]",
            "//canvas[contains(@style, 'height: 400px')]",
            "//canvas[contains(@style, 'touch-action: none')]",
        ]
        
        puzzle_canvas = None
        for selector in canvas_selectors:
            puzzle_canvas = wait_xpath(driver, selector, timeout=5)
            if puzzle_canvas:
                print(f"[INFO] Canvas puzzle ditemukan dengan selector: {selector}")
                
                # Debug canvas attributes
                try:
                    canvas_width = puzzle_canvas.get_attribute("width")
                    canvas_height = puzzle_canvas.get_attribute("height")
                    canvas_style = puzzle_canvas.get_attribute("style")
                    canvas_class = puzzle_canvas.get_attribute("class")
                    print(f"[DEBUG] Canvas found - width: {canvas_width}, height: {canvas_height}")
                    print(f"[DEBUG] Canvas style: {canvas_style}")
                    print(f"[DEBUG] Canvas class: {canvas_class}")
                except Exception as e:
                    print(f"[DEBUG] Error getting canvas attributes: {e}")
                
                
                # Debug: Print iframe content
                print("[DEBUG] Iframe page source (first 1000 chars):")
                iframe_source = driver.page_source[:1000]
                print(iframe_source)
                
                # Debug: Find all elements in iframe
                all_elements = driver.find_elements(By.XPATH, "//*")
                print(f"[DEBUG] Total elements in iframe: {len(all_elements)}")
                
                # Debug: Find all canvas elements
                all_canvas = driver.find_elements(By.TAG_NAME, "canvas")
                print(f"[DEBUG] Canvas elements found: {len(all_canvas)}")
                for i, canvas in enumerate(all_canvas):
                    try:
                        width = canvas.get_attribute("width")
                        height = canvas.get_attribute("height")
                        style = canvas.get_attribute("style")
                        print(f"[DEBUG] Canvas {i}: width={width}, height={height}, style={style}")
                    except Exception as e:
                        print(f"[DEBUG] Canvas {i}: Error getting attributes - {e}")
                
                break
            else:
                print(f"[DEBUG] Canvas not found with selector: {selector}")
        
        if puzzle_canvas:
            print("[INFO] Canvas puzzle ditemukan untuk 2captcha")
            "//canvas",  # Coba selector paling sederhana dulu
            
            # Screenshot canvas puzzle
            puzzle_screenshot = puzzle_canvas.screenshot_as_base64
            current_url = driver.current_url
            
            # Solve puzzle captcha dengan 2captcha
            captcha_solution = solve_puzzle_captcha_with_2captcha(puzzle_screenshot, current_url)
            
            if captcha_solution:
                print(f"[INFO] Menerapkan solusi 2captcha: {captcha_solution}")
                
                # Parse koordinat dari solusi
                x, y = parse_coordinates(captcha_solution)
                
                if x is not None and y is not None:
                    print(f"[INFO] Koordinat parsed: x={x}, y={y}")
                    
                    try:
                        # Method 1: Click at specific coordinates
                        ActionChains(driver).move_to_element_with_offset(puzzle_canvas, x, y).click().perform()
                        time.sleep(2)
                        print("[INFO] Method 1: Click at coordinates executed")
                        
                    except Exception as e1:
                        print(f"[WARNING] Method 1 gagal: {e1}")
                        try:
                            # Method 2: Drag and drop simulation
                            # Asumsi puzzle piece di tengah canvas, drag ke koordinat target
                            center_x = 185  # 370/2
                            center_y = 200  # 400/2
                            ActionChains(driver).move_to_element_with_offset(puzzle_canvas, center_x, center_y).click_and_hold().move_to_element_with_offset(puzzle_canvas, x, y).release().perform()
                            time.sleep(2)
                            print("[INFO] Method 2: Drag from center to target executed")
                            
                        except Exception as e2:
                            print(f"[WARNING] Method 2 gagal: {e2}")
                            try:
                                # Method 3: Multiple clicks at target area
                                for offset in [(0, 0), (-5, -5), (5, 5), (-5, 5), (5, -5)]:
                                    target_x = x + offset[0]
                                    target_y = y + offset[1]
                                    ActionChains(driver).move_to_element_with_offset(puzzle_canvas, target_x, target_y).click().perform()
                                    time.sleep(0.5)
                                print("[INFO] Method 3: Multiple clicks executed")
                                
                            except Exception as e3:
                                print(f"[ERROR] Semua method drag gagal: {e3}")
                    
                    print("[SUCCESS] CAPTCHA solution applied!")
                    
                    # Switch back to default content jika ada iframe
                    if captcha_iframe:
                        driver.switch_to.default_content()
                        print("[INFO] Switch back to default content")
                    
                else:
                    print("[ERROR] Gagal parse koordinat dari solution")
            else:
                print("[ERROR] 2captcha gagal solve puzzle")
                raise Exception("2captcha solve failed")
        else:
            print("[ERROR] Canvas puzzle captcha tidak ditemukan")
            
            # Debug: Print page source untuk analisis
            print("[DEBUG] Current page title:", driver.title)
            print("[DEBUG] Current URL:", driver.current_url)
            
            # Coba screenshot untuk debug
            debug_screenshot = f"screenshoot/debug_captcha_{username}_{int(time.time())}.png"
            driver.save_screenshot(debug_screenshot)
            print(f"[DEBUG] Debug screenshot saved: {debug_screenshot}")
            
            raise Exception("Canvas puzzle not found")
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