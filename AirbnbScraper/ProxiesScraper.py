from random import random
import requests
from lxml import etree
from bs4 import BeautifulSoup


class ProxiesScraper():
    url = 'https://free-proxy-list.net/'
    page = None
    proxies_list = []

    def get_proxies_list(self):
        self._get_page_as_etree()
        self._extract_proxies_from_page()

    def get_random_proxy(self):
        if not self.proxies_list:
            self.get_proxies_list()
        return random.choice(self.proxies_list)

    def _get_page_as_etree(self):
        result = requests.get(self.url)
        content = result.content
        page = BeautifulSoup(content, features='html.parser')
        self.page = etree.HTML(str(page))

    def _extract_proxies_from_page(self):

        table_row = self.page.xpath('//*[@id="list"]/div/div[2]/div/table/tbody/tr')

        for row in table_row:
            self.proxies_list.append(row.xpath('td')[0].text + ':' + row.xpath('td')[1].text)
