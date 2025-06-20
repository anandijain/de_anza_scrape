#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# ─── SETTINGS ────────────────────────────────────────────────────────────────
OUTPUT_CSV = "summer_courses.csv"
TERM_NAME = "2025 Summer De Anza"

# ─── SELENIUM SETUP ──────────────────────────────────────────────────────────
options = Options()
# Comment out headless if you want to watch it:
# options.add_argument("--headless")
options.add_argument("--start-maximized")
# keep browser open after script ends
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

try:
    # 1) Go to the initial class-search landing page
    driver.get(
        "https://reg.oci.fhda.edu/StudentRegistrationSsb/ssb/classSearch/classSearch"
    )

    # 2) Click the "Browse Classes" link to pick a term
    wait.until(EC.element_to_be_clickable((By.ID, "classSearchLink"))).click()

    # 3) Wait for the term-combobox (Select2) to appear
    wait.until(EC.presence_of_element_located((By.ID, "s2id_txt_term")))
    # Open the dropdown
    driver.find_element(By.CSS_SELECTOR, "#s2id_txt_term .select2-choice").click()
    # Click the desired term
    term_option = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        f"//div[contains(@class,'select2-result-label') and normalize-space()='{TERM_NAME}']"
    )))
    term_option.click()

    # 4) Click Continue to confirm term
    wait.until(EC.element_to_be_clickable((By.ID, "term-go"))).click()

    # 5) Now click Search on the class-search page
    search_btn = wait.until(EC.element_to_be_clickable((By.ID, "search-go")))
    search_btn.click()

    # 6) Wait for the results table
    wait.until(EC.presence_of_element_located((By.ID, "searchResults")))

    # 7) Set "Per Page" to 50
    perpage = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "select.page-size-select"))
    )
    Select(perpage).select_by_visible_text("50")
    time.sleep(2)  # let table redraw

    # 8) Scrape headers
    headers = [th.text for th in driver.find_elements(
        By.CSS_SELECTOR, "#searchResults thead th"
    )]

    # 9) Paginate through all pages, collecting rows
    all_rows = []
    while True:
        for tr in driver.find_elements(By.CSS_SELECTOR, "#searchResults tbody tr"):
            row = [td.text.strip() for td in tr.find_elements(By.TAG_NAME, "td")]
            all_rows.append(row)

        # try clicking "Next" (arrow icon)
        next_btn = driver.find_element(By.CSS_SELECTOR, ".paging-container .next")
        if not next_btn.is_enabled() or "disabled" in next_btn.get_attribute("class"):
            # no more pages
            break
        next_btn.click()
        # wait for the page number input to update to the next value
        # grab the page-number input, read its value, and wait until it matches the incremented page
        try:
            # find the page number input
            page_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".page-number"))
            )
            # after click, wait until its value increments
            current = int(page_input.get_attribute("value"))
            wait.until(lambda d: int(d.find_element(By.CSS_SELECTOR, ".page-number").get_attribute("value")) == current + 1)
        except Exception:
            # fallback brief sleep
            time.sleep(1)

    # 10) Export to CSV) Export to CSV
    df = pd.DataFrame(all_rows, columns=headers)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Wrote {len(df)} rows to {OUTPUT_CSV}")

finally:
    # Keeps the browser open for inspection
    pass
