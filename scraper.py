# -*- coding: utf-8 -*-

import argparse
import barbora_scraper
import kaupmees_scraper
import prisma_scraper
import rimi_scraper
import selver_scraper


def scrape(no_details=False):
    print("---------- BARBORA ----------")
    barbora_scraper.scrape(no_details=no_details)
    print("---------- KAUPMEES ----------")
    kaupmees_scraper.scrape(no_details=no_details)
    print("---------- PRISMA ----------")
    prisma_scraper.scrape(no_details=no_details)
    print("---------- RIMI ----------")
    rimi_scraper.scrape(no_details=no_details)
    print("---------- SELVER ----------")
    selver_scraper.scrape(no_details=no_details)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-details', action='store_true', help='Disable detailed logging for CI logs')
    args = parser.parse_args()
    scrape(no_details=args.no_details)
