# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from time import sleep
import traceback

from config import selver_config as conf
import db_util


BASE_URL = "https://www.selver.ee"

PAGE_SWITCH_SLEEP = 1
NETWORK_ERROR_SLEEP = 60

params = {
    "limit": 96,
    "p": 1
}


def has_next_products_page(soup):
    return soup.find("a", {"class": "next"}) != None

def get_product_links(soup):
    return [link.get("href") for link in soup.find_all("a", {"class": "product-image"})]

def has_product_with_url(url):
    return db_util.get_product_by_url(url) != None

def get_product_title(soup):
    return soup.find("h1").text.strip()

def get_barcode(soup):
    attributes_table = soup.find("table", {"class": "product-attributes"})
    for row in attributes_table.find_all("tr"):
        if row.find("th").text.strip() == "Ribakood":
            return row.find("td").text.strip()

def get_contents(soup):
    for item in soup.find_all("div", {"class": "item"}):
        if item.find("h5").text.strip() == "Koostis":
            return item.find("div", {"class": "data"}).text.strip()

def get_page_soup(url, query_params=None):
    page = requests.get(url, params=query_params)
    sleep(PAGE_SWITCH_SLEEP)
    return BeautifulSoup(page.text, "html.parser")

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
        soup = get_page_soup(url)

        title = get_product_title(soup)
        barcode = get_barcode(soup)
        contents = get_contents(soup)

        insert_product_to_database(url, title, barcode, contents)

    except Exception as e:
        handle_error(e, url)

def handle_products_page(url):
    try:
        soup = get_page_soup(url, params)

        has_next_page = has_next_products_page(soup)
        links = get_product_links(soup)

        link_index = 0

        while link_index < len(links):
            print(f"Page {params['p']}: {link_index + 1}/{len(links)}", end="\r")
            product_url = links[link_index]

            if has_product_with_url(product_url):
                link_index += 1
                continue
            else:
                handle_product_page(product_url)
                link_index += 1

        if has_next_page:
            params["p"] += 1
            return True
    
    except Exception as e:
        handle_error(e, url)

def scrape():
    for category in conf.CATEGORIES:
        print(category)

        for subcategory in conf.CATEGORIES[category]:
            print(subcategory)
            params["p"] = 1
            has_next_page = True

            while has_next_page:
                print(f"Page {params['p']}", end="\r")
                url = f"{BASE_URL}/{category}/{subcategory}"
                
                has_next_page = handle_products_page(url)


if __name__ == "__main__":
    scrape()
