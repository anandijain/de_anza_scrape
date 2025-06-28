#!/usr/bin/env python3
"""
grab.py — improved pagination robustness, uniform parsing for online/offline, incremental CSV saves, and better debugging

Usage:
  # Offline mode: parse a saved HTML page using the same parser as online
  python grab.py offline test.html fall2025.csv

  # Online mode: run Selenium for a term
  python grab.py online --term "2025 Fall De Anza" --output fall2025.csv [--save-html sample.html] [--debug]

  # Debug tip:
  #  If pagination stalls, run with --debug to save HTML snapshots of each page for inspection.
"""

import argparse
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


def parse_meeting_cell(cell_html: str) -> str:
    soup = BeautifulSoup(cell_html, "html.parser")
    day_map = {"Sunday":"Su","Monday":"M","Tuesday":"Tu","Wednesday":"W","Thursday":"Th","Friday":"F","Saturday":"Sa"}
    meetings = []
    for meeting_div in soup.select("div.meeting"):
        sched = meeting_div.find("div", class_="meeting-schedule")
        days = sched.find("div", class_="ui-pillbox-summary").get_text(strip=True)
        times = sched.find_all("span")[1].get_text(strip=True)
        if days == "None":
            meetings.append("TBA")
        else:
            abbr = "".join(day_map[d] for d in days.split(","))
            meetings.append(f"{abbr} {times}")
    return "; ".join(meetings)


def parse_html(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    headers = [th.get_text(strip=True) for th in soup.select("#searchResults thead th")]
    data = []
    for tr in soup.select("#searchResults tbody tr"):
        row = []
        for td in tr.find_all("td"):
            if td.get("data-property") == "meetingTime":
                row.append(parse_meeting_cell(str(td)))
            else:
                row.append(td.get_text(strip=True))
        data.append(row)
    return pd.DataFrame(data, columns=headers)


def parse_offline(html_path: str, output_csv: str):
    html = open(html_path, encoding="utf-8").read()
    df = parse_html(html)
    df.to_csv(output_csv, index=False)
    print(f"✅ Parsed offline HTML and wrote {len(df)} rows to {output_csv}")


def scrape_online(term: str, output_csv: str, save_html: str = None, debug: bool = False):
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://reg.oci.fhda.edu/StudentRegistrationSsb/ssb/classSearch/classSearch")
        wait.until(EC.element_to_be_clickable((By.ID, "classSearchLink"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "s2id_txt_term")))
        driver.find_element(By.CSS_SELECTOR, "#s2id_txt_term .select2-choice").click()
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class,'select2-result-label') and normalize-space()='{term}']"))).click()
        wait.until(EC.element_to_be_clickable((By.ID, "term-go"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "search-go"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "searchResults")))
        Select(wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "select.page-size-select")))).select_by_visible_text("50")
        time.sleep(2)

        if save_html:
            open(save_html, "w", encoding="utf-8").write(driver.page_source)
            print(f"✅ Saved start page HTML to {save_html}")

        all_rows = []
        page = 1
        while True:
            html = driver.page_source
            df_page = parse_html(html)
            all_rows.extend(df_page.values.tolist())

            pd.DataFrame(all_rows, columns=df_page.columns).to_csv(output_csv, index=False)
            print(f"✅ Page {page} parsed, rows so far: {len(all_rows)} → {output_csv}")

            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, ".paging-container .next")
                if not next_btn.is_enabled() or "disabled" in next_btn.get_attribute("class"):
                    break
                table = driver.find_element(By.ID, "searchResults")
                next_btn.click()
                # wait for old table to go stale or timeout
                wait.until(EC.staleness_of(table))
            except TimeoutException:
                print(f"⚠️ Timeout waiting for page change at page {page}")
                if debug:
                    debug_file = f"debug_page_{page}.html"
                    open(debug_file, "w", encoding="utf-8").write(driver.page_source)
                    print(f"🔍 Saved debug HTML to {debug_file}")
                else:
                    time.sleep(3)
            page += 1

        print(f"🎉 Completed scraping {len(all_rows)} rows across {page} pages.")

    except WebDriverException as e:
        print(f"❌ WebDriver error: {e}")
    finally:
        # driver.quit()  # uncomment to close browser
        pass


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode")

    p_off = sub.add_parser("offline", help="Parse saved HTML page offline")
    p_off.add_argument("html")
    p_off.add_argument("output")

    p_on = sub.add_parser("online", help="Run Selenium for a term")
    p_on.add_argument("--term", default="2025 Fall De Anza")
    p_on.add_argument("--output", required=True)
    p_on.add_argument("--save-html")
    p_on.add_argument("--debug", action="store_true", help="Save page snapshots on pagination errors")

    args = parser.parse_args()
    if args.mode == "offline":
        parse_offline(args.html, args.output)
    else:
        scrape_online(args.term, args.output, args.save_html, args.debug)


if __name__ == "__main__":
    main()
