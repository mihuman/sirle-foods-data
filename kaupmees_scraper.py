# -*- coding: utf-8 -*-

import requests
from time import sleep
import traceback

from config import kaupmees_config as conf
import db_util


BASE_URL = "https://www.kaupmees.ee"

PAGE_SWITCH_SLEEP = 1
NETWORK_ERROR_SLEEP = 60


def has_product_with_barcode(barcode):
    return db_util.get_retailer_product_by_barcode("KAUPMEES", barcode) is not None

def insert_product_to_database(url, title, barcode, contents):
    db_util.insert_product(url, title, barcode, contents, "KAUPMEES")

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

def get_info(url, info_type, headers=None):
    try:
        response = requests.get(url, headers=headers)
        sleep(PAGE_SWITCH_SLEEP)
        data = response.json()

        if info_type == "PRODUCTS":
            return data["foundProducts"].values()
        elif info_type == "INGREDIENTS":
            return data["details"]["ingredients"]
    
    except Exception as e:
        handle_error(e, url)

def handle_product(product_info):
    try:
        key = product_info["key"]
        url = product_info["thumb"]
        title = product_info["name"]
        barcode = product_info["ean"]

        if not has_product_with_barcode(barcode):
            product_details_url = f"{BASE_URL}/products/{key}/details"
            headers = {"Accept": "application/json"}
            contents = get_info(product_details_url, "INGREDIENTS", headers)

            insert_product_to_database(url, title, barcode, contents)

    except Exception as e:
        handle_error(e, url)

def scrape():
    for category in conf.CATEGORIES:
        print(category)
        category_id = conf.CATEGORIES[category]

        url = f"{BASE_URL}/products/search/?groups={category_id}"
        products = get_info(url, "PRODUCTS")

        product_index = 0
        
        for product in products:
            print(f"Product {product_index + 1}/{len(products)}", end="\r")
            handle_product(product)
            product_index += 1


if __name__ == "__main__":
    scrape()
