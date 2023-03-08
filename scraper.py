# -*- coding: utf-8 -*-

import barbora_scraper
# import coop_scraper
import kaupmees_scraper
import prisma_scraper
import rimi_scraper
import selver_scraper


def scrape():
    print("---------- BARBORA ----------")
    barbora_scraper.scrape()
    # print("---------- COOP ----------")
    # coop_scraper.scrape()
    print("---------- KAUPMEES ----------")
    kaupmees_scraper.scrape()
    print("---------- PRISMA ----------")
    prisma_scraper.scrape()
    print("---------- RIMI ----------")
    rimi_scraper.scrape()
    print("---------- SELVER ----------")
    selver_scraper.scrape()


if __name__ == "__main__":
    scrape()
