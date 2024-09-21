from RPA.Browser.Selenium import Selenium
import logging
import openpyxl
import os
import requests

OUTPUT_DIR = "output"  # Define your output directory
EXCEL_FILENAME = "news_data.xlsx"  # Define your Excel filename

class CustomSelenium:
    def __init__(self):
        self.selenium_lib = Selenium()
        self.logger = logging.getLogger(__name__)

    def set_chrome_options(self):
        return [
            '--no-sandbox',
            '--disable-extensions',
            '--disable-gpu',
            '--disable-web-security',
            '--start-maximized'
        ]

    def set_webdriver(self):
        self.selenium_lib.open_chrome_browser(url="https://news.yahoo.com/", headless=True)

    def quit_driver(self):
        self.selenium_lib.close_browser()

    def find_element(self, by, value):
        try:
            return self.selenium_lib.find_element(by, value)
        except Exception as e:
            self.logger.error(f"Failed to find element by {by} with value {value}: {e}")
            return None

class NewsBot:
    def __init__(self, search_phrase, news_category, num_months):
        self.search_phrase = search_phrase
        self.news_category = news_category
        self.num_months = num_months
        self.selenium = CustomSelenium()
        self.workbook = None
        self.worksheet = None

    def run(self):
        self.setup_excel()
        self.selenium.set_webdriver()
        self.open_news_site()
        self.perform_search()
        self.select_category()
        self.scrape_news()
        self.save_excel()
        self.selenium.quit_driver()

    def setup_excel(self):
        self.workbook = openpyxl.Workbook()
        self.worksheet = self.workbook.active
        self.worksheet.append(["Title", "Date", "Description", "Picture Filename", "Search Phrase Count", "Contains Money"])

    def open_news_site(self):
        self.selenium.selenium_lib.driver.get("https://news.yahoo.com/")  # Replace with actual news site URL

    def perform_search(self):
        search_box = self.selenium.find_element("name", "q")
        search_box.send_keys(self.search_phrase)
        search_box.submit()

    def select_category(self):
        category_dropdown = self.selenium.selenium_lib.driver.find_element("id", "category")  # Adjust selector as needed
        category_dropdown.click()
        category_option = self.selenium.selenium_lib.driver.find_element("xpath", f"//option[text()='{self.news_category}']")
        category_option.click()

    def scrape_news(self):
        articles = self.selenium.selenium_lib.driver.find_elements("css selector", ".article")  # Adjust selector as needed
        for article in articles:
            title = article.find_element("css selector", "h2").text  # Adjust selector as needed
            date_str = article.find_element("css selector", ".date").text  # Adjust selector as needed
            description = article.find_element("css selector", ".description").text  # Adjust selector as needed
            picture_filename = self.download_image(article)  # Implement image downloading logic
            search_count = self.count_search_phrase(description)
            contains_money = self.check_contains_money(description)

            self.worksheet.append([title, date_str, description, picture_filename, search_count, contains_money])

    def download_image(self, article):
        img_element = article.find_element("css selector", "img")  # Adjust selector as needed
        img_url = img_element.get_attribute("src")
        filename = img_url.split("/")[-1]
        img_path = os.path.join(OUTPUT_DIR, filename)
        
        if not os.path.exists(img_path):
            response = requests.get(img_url)
            with open(img_path, 'wb') as f:
                f.write(response.content)  # Save the image data
        return filename

    def count_search_phrase(self, text):
        return text.lower().count(self.search_phrase.lower())

    def check_contains_money(self, text):
        return any(keyword in text.lower() for keyword in ["$", "dollars", "usd"])

    def save_excel(self):
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        self.workbook.save(os.path.join(OUTPUT_DIR, EXCEL_FILENAME))
