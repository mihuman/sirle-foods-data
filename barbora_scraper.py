# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import traceback

from config import barbora_config as conf
import db_util


BASE_URL = "https://barbora.ee"

PAGE_SWITCH_SLEEP = 1
NETWORK_ERROR_SLEEP = 60

params = {
    "page": 1
}
driver = None
cookies = None


def has_next_products_page(soup):
    pagination = soup.find("ul", {"class": "pagination"})
    active_link = pagination.find("li", {"class": "active"}).find("a").get("href")
    last_link = pagination.find_all("li")[-1].find("a").get("href")
    return active_link != last_link

def get_product_links(soup):
    return [link.get("href") for link in soup.find_all("a", {"class": "b-product--imagelink"})]

def has_product_with_url(url):
    return db_util.get_product_by_url(url) != None

def get_product_title(soup):
    return soup.find("h1").text.strip()

def get_contents(soup):
    list_index = -1
    has_contents = False

    product_info = soup.find("dl", {"class": "b-product-info--info-2"})
    for term in product_info.find_all("dt"):
        list_index += 1
        if term.text.strip() == "Koostisosad":
            has_contents = True
            break
        
    if has_contents:
        return product_info.find_all("dd")[list_index].text.strip()

def get_page_soup(url, query_params=None):
    page = requests.get(url, params=query_params, cookies=cookies)
    sleep(PAGE_SWITCH_SLEEP)
    return BeautifulSoup(page.text, "html.parser")

def insert_product_to_database(url, title, contents):
    db_util.insert_product(url, title, None, contents, "BARBORA")

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
        soup = get_page_soup(url)

        title = get_product_title(soup)
        contents = get_contents(soup)

        insert_product_to_database(url, title, contents)

    except Exception as e:
        handle_error(e, url)

def handle_products_page(url):
    try:
        soup = get_page_soup(url, params)

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

    global driver
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

def select_region():
    driver.get(BASE_URL)
    driver.find_element_by_xpath("//*[@id='counties-data']/div[1]/div/button").click()
    sleep(1)
    driver.find_element_by_xpath("//*[@id='counties-data']/div[1]/div/button").click()
    sleep(1)

def save_cookies():
    global cookies
    cookies = {}

    for cookie in driver.get_cookies():
        cookies[cookie["name"]] = cookie["value"]

def close_browser():
    driver.quit()

def setup_cookies():
    open_browser()
    select_region()
    save_cookies()
    close_browser()

def scrape():
    setup_cookies()
    
    for category in conf.CATEGORIES:
        print(category)
        path = conf.CATEGORIES[category]

        params["page"] = 1
        has_next_page = True

        while has_next_page:
            print(f"Page {params['page']}", end="\r")
            url = f"{BASE_URL}{path}"
            
            has_next_page = handle_products_page(url)


if __name__ == "__main__":
    scrape()
