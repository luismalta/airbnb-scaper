
import os
import requests
import pandas as pd
import multiprocessing
from functools import partial
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from AirbnbScraper.ProxiesScraper import ProxiesScraper


property_scraper_selectors = {
    "name": '_1n81at5',
    "rating": '_17p6nbba',
    "is_superhost": '_1mhorg9',
    "type ": '_cv5qq4',
    "guests_rooms_beds_bathrooms": 'lgx66tx',
    "price_per_night": '_1k4xcdh',
    "total_price": '_1k4xcdh',
}


def extracts_booking_information_from_properties_job(property_url, use_proxy_server):

    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument('--blink-settings=imagesEnabled=false')

    if (use_proxy_server):
        chrome_options.add_argument(
            f"--proxy-server={proxies_scrapper.get_random_proxy()}")

    # driver = webdriver.Chrome(options=chrome_options)

    driver = webdriver.Remote(
        command_executor=f"http://{os.environ['SELENIUM_URL']}:4444",
        options=chrome_options,
    )

    driver.get(property_url)

    property_booking_info = {}

    for info in property_scraper_selectors:
        try:
            data = WebDriverWait(driver, timeout=3).until(
                lambda d: d.find_element(
                    By.CLASS_NAME, property_scraper_selectors[info])
            ).text
        except NoSuchElementException:
            data = '-'
        except TimeoutException:
            data = ''
        property_booking_info[info] = data

    driver.quit()
    return property_booking_info


class AirbnbScraper():

    property_search_page_urls = []
    properties_pages_urls = []
    property_scraper_selectors = {}
    property_booking_information_list = []
    property_booking_info_df = None
    selenium_driver = None
    use_server_proxy = False

    def __init__(self, use_server_proxy=False):
        self.use_server_proxy = use_server_proxy

    def get_booking_information(self, location: str, page_qty: int, **kwargs):
        """
          location:
          qty:
          checkin: 
          checkout:
          guests:
        """

        self.generate_properties_listing_urls(location, page_qty, **kwargs)
        self.extract_properties_list_from_search_urls()
        self.extracts_booking_information_from_properties()
        self.build_property_booking_info_dataframe()

    def generate_properties_listing_urls(self, location, page_qty, **kwargs):

        urls = []
        for i in range(page_qty):
            query = [f'items_offset={i*20}']

            for key, value in kwargs.items():
                query.append('{}={}'.format(key, value))

            url = "https://www.airbnb.com.br/s/{}/homes?{}".format(
                location, '&'.join(query))

            urls.append(url)

        self.property_search_page_urls = urls

    def extract_properties_list_from_search_urls(self):
        for url in self.property_search_page_urls:
            page = self.get_and_parse_page(url)
            properties_nodes = page.findAll("meta", {"itemprop": "url"})
            self.properties_pages_urls += list(
                map(lambda node: 'https://' + node["content"], properties_nodes))

    def extracts_booking_information_from_properties(self):
        cpu_number = os.cpu_count()
        with multiprocessing.Pool(cpu_number) as pool:
            result = pool.map(
                partial(
                    extracts_booking_information_from_properties_job,
                    use_proxy_server=self.use_server_proxy),
                self.properties_pages_urls)
        pool.close()
        pool.join()
        self.property_booking_information_list += result

    def build_property_booking_info_dataframe(self):
        property_booking_info_df = pd.DataFrame(
            self.property_booking_information_list)
        self.property_booking_info_df = self.clean_dataframe(
            property_booking_info_df)
        self.property_booking_info_df = property_booking_info_df

    def get_and_parse_page(self, url):
        result = requests.get(url, timeout=5)
        content = result.content
        return BeautifulSoup(content, features='html.parser')

    def get_text_if_exist(self, node):
        return node.get_text() if node else None

    def clean_dataframe(self, dataframe):

        dataframe['rating'] = dataframe['rating'].apply(
            lambda item: item.replace(' ·', ''))
        dataframe[['guests', 'rooms', 'beds', 'bathrooms']
                  ] = dataframe['guests_rooms_beds_bathrooms'].str.split('·', expand=True)
        dataframe = dataframe.drop('guests_rooms_beds_bathrooms', axis=1)

        return dataframe
