# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from time import sleep
import traceback

from config import selver_config as conf
import db_util


BASE_URL = "https://www.selver.ee"

PAGE_LOAD_DELAY = 10
PAGE_SWITCH_SLEEP = 1
NETWORK_ERROR_SLEEP = 60

params = {
    "limit": 96,
    "page": 1
}
driver = None


def has_next_products_page(soup):
    return soup.select_one("div.sf-pagination__item--next a") is not None

def get_product_links(soup):
    return [link.get("href") for link in soup.select("h3.ProductCard__title a.ProductCard__link")]

def has_product_with_url(url):
    return db_util.get_product_by_url(url) is not None

def get_product_title(soup):
    return soup.find("h1").text.strip()

def get_barcode(soup):
    attributes_table = soup.find("table", {"class": "ProductAttributes__table"})
    for row in attributes_table.find_all("tr"):
        if row.find("th").text.strip() == "Ribakood":
            return row.find("td").text.strip() 

def get_contents(soup):
    for item in soup.select("div.ProductInfoBox div.AttributeAccordion"):
        if item.find("div", {"class": "AttributeAccordion__heading"}).text.strip() == "Koostisosad":
            content = item.find("div", {"class": "AttributeAccordion__content"}).text
            return content.replace("* Toote koostisosade loetelu võib muutuda. Kontrollige enne toote tarbimist pakendil esitatud koostisosi.", "").strip()

def get_page_soup(url, wait_for_selector, query_params=None):
    full_url = None

    if query_params:
        param_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
        full_url = f"{url}?{param_string}"
    else:
        full_url = url

    driver.get(full_url)

    try:
        element = EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
        WebDriverWait(driver, PAGE_LOAD_DELAY).until(element)
        sleep(PAGE_SWITCH_SLEEP)
        return BeautifulSoup(driver.page_source, "html.parser")
    except TimeoutException as e:
        raise e

def insert_product_to_database(url, title, barcode, contents):
    db_util.insert_product(url, title, barcode, contents, "SELVER")

def handle_error(error, url):
    # network errors
    if isinstance(error, requests.exceptions.ConnectionError):
        print("NETWORK ERROR")
        sleep(NETWORK_ERROR_SLEEP)

    # page parsing errors
    elif isinstance(error, TypeError):
        print(f"TYPE ERROR: {url}")
        traceback.print_exc()

    # page parsing errors
    elif isinstance(error, AttributeError):
        print(f"ATTRIBUTE ERROR: {url}")
        traceback.print_exc()

    # other errors
    elif isinstance(error, Exception):
        print(f"OTHER ERROR: {url}")
        traceback.print_exc()

def handle_product_page(url):
    try:
        soup = get_page_soup(url, "h1")

        title = get_product_title(soup)
        barcode = get_barcode(soup)
        contents = get_contents(soup)

        insert_product_to_database(url, title, barcode, contents)

    except Exception as e:
        handle_error(e, url)

def handle_products_page(url):
    try:
        soup = get_page_soup(url, ".ProductCard", params)

        has_next_page = has_next_products_page(soup)
        links = get_product_links(soup)

        link_index = 0

        while link_index < len(links):
            print(f"Page {params['page']}: {link_index + 1}/{len(links)}", end="\r")
            product_url = f"{BASE_URL}{links[link_index]}"

            if has_product_with_url(product_url):
                link_index += 1
                continue
            else:
                handle_product_page(product_url)
                link_index += 1

        if has_next_page:
            params["page"] += 1
            return True

    except Exception as e:
        handle_error(e, url)

def open_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--log-level=OFF")

    service = Service(ChromeDriverManager().install())

    global driver
    driver = webdriver.Chrome(service=service, options=options)

def close_browser():
    driver.quit()

def scrape():
    open_browser()

    for category in conf.CATEGORIES:
        print(category, end="\t\t\t\t\n")

        for subcategory in conf.CATEGORIES[category]:
            print(subcategory, end="\t\t\t\t\n")
            params["page"] = 1
            has_next_page = True

            while has_next_page:
                print(f"Page {params['page']}", end="\t\t\t\t\r")
                url = f"{BASE_URL}/{category}/{subcategory}"
                
                has_next_page = handle_products_page(url)

    close_browser()


if __name__ == "__main__":
    scrape()
