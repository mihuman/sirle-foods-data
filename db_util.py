# -*- coding: utf-8 -*-

import os
import time
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()
MONGO_DB_URI = os.environ.get("MONGO_DB_URI")

client = MongoClient(MONGO_DB_URI)
db = client.foods


def get_product_by_url(url):
    return db.products.find_one({"url": url})

def get_retailer_product_by_barcode(retailer, barcode):
    return db.products.find_one({"rtlr": retailer, "bc": barcode})

def get_all_products_by_barcode(barcode):
    return db.products.find({"bc": barcode})

def insert_product(url, title, barcode, contents, price, retailer):
    db.products.insert_one({
        "url": url,
        "title": title,
        "bc": barcode,
        "cts": contents,
        "prc": price,
        "rtlr": retailer,
        "lastScraped": int(time.time() * 1000)
    })

def update_product_price(url, price):
    db.products.update_one(
        {"url": url},
        {"$set": {"prc": price, "lastScraped": int(time.time() * 1000)}}
    )
