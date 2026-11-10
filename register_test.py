"""
Registration form tester (Selenium, Chrome incognito).
Install:  pip install selenium
(Selenium 4.6+ downloads the matching chromedriver automatically.)
"""
import random
import string
import time
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# ------------------- CONFIG: edit these -------------------
URL = "https://adselect.org/register"   # your registration page
SPONSOR = "trivo08"      # must be a real sponsor on your site
COUNTRY = "Zimbabwe"
PHONE_PREFIX_LEN = 0                     # the +263 is already shown by the page
EMAIL_DOMAIN = "example.com"             # use a domain you control if the server validates it
SUCCESS_TEXT = "success"                 # text that appears on success (case-insensitive)
SUCCESS_URL_PART = ""                    # or a URL fragment after redirect, e.g. "/dashboard"
BATCH_SIZE = 100                          # registrations per batch
DELAY_BETWEEN_RUNS = 1                   # seconds to wait between runs
# -----------------------------------------------------------

FIRST = ["Tendai", "Rudo", "Farai", "Chipo", "Tatenda", "Nyasha", "Kudzai", "Tino"]
LAST = ["Moyo", "Ncube", "Dube", "Sibanda", "Chikwanha", "Mutasa", "Zhou", "Gumbo"]


def make_user():
    tag = uuid.uuid4().hex[:8]
    first, last = random.choice(FIRST), random.choice(LAST)
    return {
        "full_name": f"{first} {last}",
        "username": f"{first.lower()}_{tag}",
        "email": f"{first.lower()}.{tag}@{EMAIL_DOMAIN}",
        # Zimbabwe mobile: 77/71/73/78 + 7 digits (no leading 0, +263 is pre-filled)
        "phone": random.choice(["77", "71", "73", "78"]) + "".join(random.choices(string.digits, k=7)),
        "password": "Pw" + uuid.uuid4().hex[:10] + "!",
    }


def field(driver, label):
    """Find the input that follows a label (case-insensitive)."""
    xp = (
        "//*[translate(normalize-space(text()),'abcdefghijklmnopqrstuvwxyz',"
        f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ')='{label.upper()}']"
        "/following::*[self::input or self::select][1]"
    )
    return WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xp)))


def type_into(el, text):
    el.clear()
    el.send_keys(text)


def register_once():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--incognito")
    driver = webdriver.Chrome(options=opts)
    driver.maximize_window()
    user = make_user()
    try:
        driver.get(URL)

        type_into(field(driver, "Full Name"), user["full_name"])
        type_into(field(driver, "Username"), user["username"])
        type_into(field(driver, "Email"), user["email"])

        country = field(driver, "Country")
        if country.tag_name == "select":
            Select(country).select_by_visible_text(COUNTRY)

        type_into(field(driver, "Mobile Number"), user["phone"])
        type_into(field(driver, "Sponsor"), SPONSOR)
        type_into(field(driver, "Password"), user["password"])
        type_into(field(driver, "Confirm Password"), user["password"])

        # Terms checkbox
        box = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
        if not box.is_selected():
            driver.execute_script("arguments[0].click();", box)

        # Submit
        btn = driver.find_element(
            By.XPATH, "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'create account')]"
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click()

        # Wait for result
        time.sleep(3)
        page = driver.page_source.lower()
        ok = (SUCCESS_URL_PART and SUCCESS_URL_PART in driver.current_url) or SUCCESS_TEXT.lower() in page
        print("\nSUCCESS" if ok else "\nFAILED / no success message found")
        print("Used:", user)
        return ok
    except Exception as e:
        print("ERROR:", e)
        return False
    finally:
        driver.quit()  # closes the incognito window


if __name__ == "__main__":
    while True:
        passed = 0
        for i in range(1, BATCH_SIZE + 1):
            print(f"\n=== Run {i}/{BATCH_SIZE} ===")
            if register_once():
                passed += 1
            time.sleep(DELAY_BETWEEN_RUNS)
        print(f"\nBatch done: {passed}/{BATCH_SIZE} succeeded.")
        again = input("Start another batch? (y/n): ").strip().lower()
        if again != "y":
            break