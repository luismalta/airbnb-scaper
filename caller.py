from AirbnbScraper import AirbnbScraper, ProxiesScraper


scraper = AirbnbScraper.AirbnbScraper(use_server_proxy=False)
proxies_scrapper = ProxiesScraper.ProxiesScraper()

scraper.get_booking_information('Tiradentes--MinasGerais', 1, checkin='2023-05-01', checkout='2023-05-02')
scraper.property_booking_info_df.to_csv(
    'booking_data_test.csv', sep=',', index=False)