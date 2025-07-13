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

from config import coop_config as conf
import db_util


BASE_URL = "https://ecoop.ee"
PRODUCTS_ON_PAGE = 24

PAGE_LOAD_DELAY = 10
PAGE_SWITCH_SLEEP = 1
NETWORK_ERROR_SLEEP = 60

params = {
    "page": 1
}
driver = None


def has_next_products_page(soup):
    for link in soup.find_all("a", {"class": "page-navigation"}):
        if link.text.strip() == "Järgmine ›":
            return "disabled" not in link.get("class")

def get_product_links(soup):
    return [link.get("href") for link in soup.find_all("a", {"class": "product-content"})]

def get_total_product_count(soup):
    return int(soup.find("span", {"class": "count"}).text.replace(" toodet", ""))

def has_product_with_url(url):
    return db_util.get_product_by_url(url) is not None

def get_product_title(soup):
    return soup.find("h1").text.strip()

def get_contents(soup):
    list_index = -1
    has_contents = False

    product_info = soup.find("section", {"class": "info"})
    for heading in product_info.find_all("h6"):
        list_index += 1
        if heading.text.strip() == "Koostisosad":
            has_contents = True
            break
        
    if has_contents:
        return product_info.find_all("p")[list_index].text.strip()

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

def insert_product_to_database(url, title, contents):
    db_util.insert_product(url, title, None, contents, "COOP")

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
        contents = get_contents(soup)

        insert_product_to_database(url, title, contents)

    except Exception as e:
        handle_error(e, url)

def handle_products_page(url):
    try:
        soup = get_page_soup(url, "span.count", params)

        has_next_page = has_next_products_page(soup)
        links = get_product_links(soup)
        product_count = get_total_product_count(soup)

        link_index = 0

        while link_index < len(links):
            product_number = (params['page'] - 1) * PRODUCTS_ON_PAGE + (link_index + 1)
            page_counter = f"{link_index + 1}/{len(links)}"
            category_counter = f"{product_number}/{product_count}"
            print(f"Page {params['page']}: {page_counter} - {category_counter} ", end="\r")

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
        path = conf.CATEGORIES[category]

        params["page"] = 1
        has_next_page = True

        while has_next_page:
            print(f"Page {params['page']}", end="\t\t\t\t\r")
            url = f"{BASE_URL}{path}"
            
            has_next_page = handle_products_page(url)
    
    close_browser()


if __name__ == "__main__":
    scrape()
