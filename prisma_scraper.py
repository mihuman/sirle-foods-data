# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from time import sleep
import traceback

from config import prisma_config as conf
import db_util


BASE_URL = "https://www.prismamarket.ee"

PAGE_SWITCH_SLEEP = 1
NETWORK_ERROR_SLEEP = 60

params = {
    "page": 1
}


def has_next_products_page(soup):
    return soup.find("a", string="Järgmine leht") is not None

def get_product_links_with_prices(soup):
    result = {}

    for item in soup.select("div[data-test-id='product-list-item']"):
        link = item.find("a").get("href")
        price = item.find("span", {"data-test-id": "display-price"}).text.strip()
        result[link] = float(price.replace("€", "").replace(",", ".").strip())

    return result

def has_product_with_url(url):
    return db_util.get_product_by_url(url) is not None

def get_product_title(soup):
    return soup.find("h1").text.strip()

def get_barcode(soup):
    ean_element = soup.find("h3", string="EAN")
    return ean_element.find_next("div").find("span").text.strip()

def get_contents(soup):
    contents_element = soup.find("h3", string="Koostisosad")
    if contents_element:
        return contents_element.find_next("div").text.strip()

def get_page_soup(url, query_params=None):
    page = requests.get(url, params=query_params)
    sleep(PAGE_SWITCH_SLEEP)
    return BeautifulSoup(page.text, "html.parser")

def insert_product_to_database(url, title, barcode, contents, price):
    db_util.insert_product(url, title, barcode, contents, price, "PRISMA")

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

def handle_product_page(url, price):
    try:
        soup = get_page_soup(url)

        title = get_product_title(soup)
        barcode = get_barcode(soup)
        contents = get_contents(soup)

        insert_product_to_database(url, title, barcode, contents, price)

    except Exception as e:
        handle_error(e, url)

def handle_products_page(url):
    try:
        soup = get_page_soup(url, params)

        has_next_page = has_next_products_page(soup)
        links_with_prices = get_product_links_with_prices(soup)

        link_index = 0

        for product_url, price in links_with_prices.items():
            print(f"Page {params['page']}: {link_index + 1}/{len(links_with_prices)}", end="\r")
            full_url = f"{BASE_URL}{product_url}"

            if has_product_with_url(full_url):
                if price is not None:
                    db_util.update_product_price(full_url, price)
            else:
                handle_product_page(full_url, price)

            link_index += 1

        if has_next_page:
            params["page"] += 1
            return True
    
    except Exception as e:
        handle_error(e, url)

def scrape():
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
