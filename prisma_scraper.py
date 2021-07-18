# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from time import sleep
import traceback

from config import prisma_config as conf
import db_util


BASE_URL = "https://www.prismamarket.ee"
PRODUCTS_ON_PAGE = 48

PAGE_SWITCH_SLEEP = 1
NETWORK_ERROR_SLEEP = 60

params = {
    "main_view": 1
}
page = {
    "products": 1
}

# Disable warnings for SSL certificate problems
requests.packages.urllib3.disable_warnings()


def get_subcategory_link_objects(soup):
    return [link for link in soup.find_all("a", {"class": "name"})]

def get_product_links(soup):
    return [link.get("href") for link in soup.find_all("a", {"class": "js-link-item"})]

def get_products_total(soup):
    return int(soup.find("div", {"class": "category-items"}).find("b").text)

def has_next_products_page(products_total):
    return page["products"] * PRODUCTS_ON_PAGE < products_total

def get_normalized_product_url(url):
    # PRISMA can have different URL patterns for the same product
    # Return normalized product URL that looks like this:
    # https://www.prismamarket.ee/entry/<product-name>/<barcode>
    parts = url.split("/")
    category_id = parts.pop(4)

    try:
        int(category_id)
        return "/".join(parts)
    except ValueError:
        return url

def has_product_with_url(url):
    return db_util.get_product_by_url(url) != None

def get_product_title(soup):
    title = soup.find("h1", {"id": "product-name"}).text.strip()
    producer = soup.find("h2", {"id": "product-subname"}).text.strip()
    return f"{title}, {producer}" if len(producer) > 0 else title

def get_barcode(soup):
    return soup.find("span", {"itemprop": "sku"}).text.strip()

def get_contents(soup):
    contents_container = soup.find("p", {"id": "product-ingredients"})
    if contents_container != None:
        return contents_container.text.strip()

def get_page_soup(url, query_params=None):
    page = requests.get(url, params=query_params, verify=False)
    sleep(PAGE_SWITCH_SLEEP)
    return BeautifulSoup(page.text, "html.parser")

def insert_product_to_database(url, title, barcode, contents):
    db_util.insert_product(url, title, barcode, contents, "PRISMA")

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

        products_total = get_products_total(soup)
        has_next_page = has_next_products_page(products_total)
        links = get_product_links(soup)

        product_index = 0

        while product_index < len(links):
            print(f"Page {page['products']}: {product_index + 1}/{len(links)}", end="\r")
            path = links[product_index]
            product_url = get_normalized_product_url(f"{BASE_URL}{path}")

            if has_product_with_url(product_url):
                product_index += 1
                continue
            else:
                handle_product_page(product_url)
                product_index += 1

        if has_next_page:
            page["products"] += 1
            return True
    
    except Exception as e:
        handle_error(e, url)

def handle_category_page(url):
    try:
        soup = get_page_soup(url)
        link_objects = get_subcategory_link_objects(soup)

        for link in link_objects:
            subcategory = link.text
            path = link.get("href")
            print(subcategory)

            page["products"] = 1
            has_next_page = True

            while has_next_page:
                products_url = f"{BASE_URL}{path}/page/{page['products']}"
                has_next_page = handle_products_page(products_url)
    
    except Exception as e:
        handle_error(e, url)

def scrape():
    for category in conf.CATEGORIES:
        print(category)
        path = conf.CATEGORIES[category]
        url = f"{BASE_URL}{path}"

        handle_category_page(url)


if __name__ == "__main__":
    scrape()
