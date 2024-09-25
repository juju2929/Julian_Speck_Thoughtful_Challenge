import logging
import os
import requests
import openpyxl
import requests
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from RPA.Robocorp.WorkItems import WorkItems
from RPA.Browser.Selenium import Selenium
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select


log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logging to both console and file
log_filename = os.path.join(log_dir, "news_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),  # Log to a file
        logging.StreamHandler()              # Also log to console
    ]
)

class CustomSelenium:
    def __init__(self):
        self.selenium_lib = Selenium()
        self.logger = logging.getLogger(__name__)

    def set_webdriver(self):
        self.selenium_lib.open_chrome_browser(url="https://www.aljazeera.com/", headless=False)

    def quit_driver(self):
        self.selenium_lib.close_browser()

    def find_element(self, by, value, timeout=10):
        try:
            return WebDriverWait(self.selenium_lib.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except Exception as e:
            self.logger.error(f"Failed to find element by {by} with value {value}: {e}")
            return None

class DataProcessor:
    @staticmethod
    def count_search_phrase(texts, search_phrase):
        """Count occurrences of a search phrase in multiple text sources."""
        count = 0
        for text in texts:
            count += text.lower().count(search_phrase.lower())  # Case insensitive count
        return count


    @staticmethod
    def check_contains_money(text):
        money_pattern = r'\$\d+(\.\d{2})?|\d+\s?(dollars?|usd)'
        return bool(re.search(money_pattern, text, re.IGNORECASE))

    @staticmethod
    def is_within_date_range(self, article_date_str):
        # Ensure article_date_str is a string
        if not isinstance(article_date_str, str):
            article_date_str = str(article_date_str)

        # Your existing date parsing logic here
        parsed_date = DataProcessor.parse_date(article_date_str)

        # Now use self.start_date and self.end_date to check if the parsed date is within range
        return parsed_date and (self.start_date <= parsed_date <= self.end_date)


    @staticmethod
    def is_within_date_range(article_date_str, start_date, end_date):
        # Your existing date parsing logic here
        parsed_date = DataProcessor.parse_date(article_date_str)
        
        if parsed_date is None:
            return False  # If date parsing fails, return False
            
        return start_date <= parsed_date <= end_date
        
    @staticmethod
    def parse_date(date_str):
        if not isinstance(date_str, str):
            return None  # If it's not a string, return None

        try:
            # Try parsing as "Month Day, Year" format
            return datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            try:
                # Try parsing as "Day Month Year" format
                return datetime.strptime(date_str, "%d %b %Y")
            except ValueError:
                # Handle "Last update" format
                if date_str.startswith("Last update"):
                    return datetime.strptime(date_str.replace("Last update ", ""), "%d %b %Y")
                # Return None for unrecognized formats
                return None


class ExcelHandler:
    def __init__(self, output_dir, filename):
        self.output_dir = output_dir
        self.filename = filename
        self.workbook = openpyxl.Workbook()
        self.worksheet = self.workbook.active

    def setup_worksheet(self):
        self.worksheet.append(["Title", "Date", "Description", "Picture Filename", "Search Phrase Count", "Contains Money"])

    def add_row(self, data):
        self.worksheet.append(data)

    def save(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.workbook.save(os.path.join(self.output_dir, self.filename))

class NewsBot:
    def __init__(self, search_phrase="USA", sort_category="date", num_months=1):
        self.work_items = WorkItems()
        self.selenium = CustomSelenium()
        self.data_processor = DataProcessor()
        self.excel_handler = ExcelHandler("output", "news_data.xlsx")
        self.logger = logging.getLogger(__name__)
        self.search_phrase = search_phrase
        self.sort_category = sort_category
        self.num_months = num_months
        self.get_input_work_item()

    def get_input_work_item(self):
        # Try to load the input work item
        try:
            self.work_items.get_input_work_item()
            self.logger.info("Input work item retrieved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to retrieve input work item: {e}")

    def save_to_work_item(self):
        try:
            # Save the Excel file to work item output
            excel_file_path = os.path.join(self.excel_handler.output_dir, self.excel_handler.filename)
            output_work_item = self.work_items.create_output_work_item(save=False)

            output_work_item.add_file(excel_file_path)  # Attach Excel file to the output work item

            # Save the images to the work item output (assuming images are downloaded in the output directory)
            for image_file in os.listdir("images"):
                image_file_path = os.path.join("images", image_file)
                output_work_item.add_file(image_file_path)  # Attach each image file to the output work item

            output_work_item.save()
            self.logger.info("Output work item saved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to save to work item: {e}")

    def handle_popup_ad(self):
        # Attempt to find and close the popup ad
        try:
            # Update this selector to match the specific popup's close button or overlay
            close_button = self.selenium.find_element(By.XPATH, "//button[contains(@class, 'close-popup-class')]")  # Update the class as needed
            if close_button:
                close_button.click()
                self.logger.info("Popup ad closed successfully.")
        except Exception as e:
            self.logger.warning(f"No popup ad found or issue handling it: {e}")

    def run(self):
        try:
            self.setup()
            self.open_news_site()
            self.handle_popup_ad()
            self.perform_search()
            self.handle_popup_ad()
            self.select_sort_option()
            self.run_scraping_process()
            self.save_to_work_item()
        except Exception as e:
            self.logger.error(f"An error occurred during execution: {e}")
        finally:
            self.cleanup()

    def setup(self):
        self.selenium.set_webdriver()
        self.excel_handler.setup_worksheet()

    def open_news_site(self):
        self.selenium.selenium_lib.driver.get("https://www.aljazeera.com/")

    def handle_cookies(self):
        try:
            accept_button = self.selenium.find_element(By.ID, "onetrust-accept-btn-handler", timeout=5)
            if accept_button:
                accept_button.click()
                self.logger.info("Cookie popup handled successfully.")
        except Exception as e:
            self.logger.warning(f"No cookie popup found or issue handling it: {e}")

    def perform_search(self):
        try:
            self.handle_cookies()
            search_button = self.selenium.find_element(By.XPATH, "//button[contains(@class, 'no-styles-button') and @aria-pressed='false']")
            if search_button:
                search_button.click()
                search_box = self.selenium.find_element(By.CSS_SELECTOR, "input.search-bar__input[placeholder='Search']")
                if search_box:
                    self.logger.info(f"Performing search for {self.search_phrase}")
                    search_box.send_keys(self.search_phrase)
                    search_box.submit()
                else:
                    self.logger.error("Search box not found after clicking search button.")
            else:
                self.logger.error("Search button not found.")
        except Exception as e:
            self.logger.error(f"Error while performing search: {e}")

    def select_sort_option(self, category="date"):
        try:
            sort_dropdown = Select(self.selenium.find_element(By.ID, "search-sort-option"))
            sort_dropdown.select_by_value(f"{category}")
            self.logger.info(f"Sort option {category} selected")
        except Exception as e:
            self.logger.error(f"Error selecting sort option: {e}")


    def run_scraping_process(self):
        # Step 1: Collect articles within the date range
        articles_within_date_range = self.collect_articles_within_date_range()
        
        # Step 2: Scrape the collected articles
        if articles_within_date_range:
            self.scrape_news(articles_within_date_range)
        else:
            self.logger.info("No articles found within the date range to scrape.")


    def scrape_news(self, articles):
        self.logger.info("Starting to scrape news articles from the collected list.")

        if not articles:
            self.logger.warning("No articles available for scraping.")
            return

        for i, article in enumerate(articles):
            try:
                # Extract title, date, description, etc.
                title = article.find_element(By.CSS_SELECTOR, "h3.gc__title a span").text

                # Ensure correct date extraction
                date_element = article.find_element(By.CSS_SELECTOR, ".gc__date .gc__date__date span[aria-hidden='true']")
                date_str = date_element.text if date_element else "Date not found"

                description = article.find_element(By.CSS_SELECTOR, ".gc__body-wrap .gc__excerpt p").text
                picture_filename = self.download_image(article,i)
                search_count = self.data_processor.count_search_phrase([title, description], self.search_phrase)
                contains_money = self.data_processor.check_contains_money(description)

                data_row = [title, date_str, description, picture_filename, search_count, contains_money]
                self.logger.info(f"Appending to Excel: {data_row}")
                self.excel_handler.add_row(data_row)
                self.excel_handler.save()  # Save the workbook after each article

            except StaleElementReferenceException:
                self.logger.warning(f"Stale element found while processing article {i}. Refetching the article.")
                try:
                    # Re-fetch the article and try again
                    updated_article = self.selenium.selenium_lib.driver.find_elements(By.CSS_SELECTOR, ".search-result__list article.gc")[i]
                    
                    # Retry processing the updated article
                    title = updated_article.find_element(By.CSS_SELECTOR, "h3.gc__title a span").text
                    date_element = updated_article.find_element(By.CSS_SELECTOR, ".gc__date .gc__date__date span[aria-hidden='true']")
                    date_str = date_element.text if date_element else "Date not found"
                    description = updated_article.find_element(By.CSS_SELECTOR, ".gc__body-wrap .gc__excerpt p").text
                    picture_filename = self.download_image(updated_article,i)
                    search_count = self.data_processor.count_search_phrase([title, description], self.search_phrase)
                    contains_money = self.data_processor.check_contains_money(description)

                    data_row = [title, date_str, description, picture_filename, search_count, contains_money]
                    self.logger.info(f"Appending to Excel: {data_row}")
                    self.excel_handler.add_row(data_row)
                    self.excel_handler.save()
                except Exception as e:
                    self.logger.error(f"Error reprocessing article {i} after refetching: {e}")

            except Exception as e:
                self.logger.error(f"Error processing article at index {i}: {e}")



    def collect_articles_within_date_range(self):
        self.logger.info("Starting to collect articles within the date range.")
        WebDriverWait(self.selenium.selenium_lib.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.gc.u-clickable-card"))
        )
        all_articles = []
        within_date_range = True

        # Calculate the date range
        end_date = datetime.now()

        # If num_months is 0, start from the first day of the current month
        if self.num_months == 0:
            start_date = end_date.replace(day=1)  # First day of the current month
        else:
            start_date = end_date - relativedelta(months=self.num_months)

        while within_date_range:
            articles = self.selenium.selenium_lib.driver.find_elements(By.CSS_SELECTOR, ".search-result__list article.gc")
            if not articles:
                self.logger.warning("No articles found. Check the CSS selector or page load.")
                break

            for article in articles[len(all_articles):]:
                try:
                    date_element = article.find_element(By.CSS_SELECTOR, ".gc__date .gc__date__date span[aria-hidden='true']")
                    date_str = date_element.text if date_element else "Date not found"
                    parsed_date = DataProcessor.parse_date(date_str)

                    # Check if parsed date is within the range
                    if parsed_date and self.data_processor.is_within_date_range(
                        str(parsed_date.strftime("%B %d, %Y")), start_date, end_date
                    ):
                        all_articles.append(article)
                    else:
                        within_date_range = False
                        self.logger.info(f"Article date {date_str} is outside the desired date range.")
                        break

                except Exception as e:
                    self.logger.error(f"Error processing article date: {e}")
                    continue

            if within_date_range:
                try:
                    show_more_button = WebDriverWait(self.selenium.selenium_lib.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[@aria-hidden='true' and text()='Show more']"))
                    )

                    self.selenium.selenium_lib.driver.execute_script(
                        "arguments[0].scrollIntoView(true); window.scrollBy(0, -200);", show_more_button
                    )

                    if show_more_button.is_displayed() and show_more_button.is_enabled():
                        show_more_button.click()
                        self.logger.info("Clicking 'Show more' to load more articles.")
                    
                    WebDriverWait(self.selenium.selenium_lib.driver, 15).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.gc.u-clickable-card"))
                    )
                except TimeoutException:
                    self.logger.info("No 'Show more' button found or no more articles to load.")
                    within_date_range = False

        self.logger.info(f"Collected {len(all_articles)} articles.")
        return all_articles




    def download_image(self, article, index):
        try:
            # Wait for the image to appear in the article
            WebDriverWait(self.selenium.selenium_lib.driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".gc__image"))
            )

            # Extract the image URL from the updated img element
            image_element = article.find_element(By.CSS_SELECTOR, ".gc__image")
            image_url = image_element.get_attribute("src")

            if image_url:
                # Create a unique filename for each image
                image_filename = f"article_image_{index}.jpg"
                image_path = os.path.join("images", image_filename)  # Assuming you have an 'images' folder

                # Ensure the 'images' directory exists
                os.makedirs("images", exist_ok=True)

                # Download the image and save it locally
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    with open(image_path, 'wb') as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)
                    
                    self.logger.info(f"Image downloaded and saved as {image_filename}.")
                    return image_filename  # Return the filename for further use

                else:
                    self.logger.warning(f"Failed to download image from {image_url}. Status code: {response.status_code}")

            else:
                self.logger.warning("No image URL found for the article.")
        
        except Exception as e:
            self.logger.error(f"Error downloading image: {e}")
        
        return None  # Return None if the image couldn't be downloaded

    def cleanup(self):
        self.excel_handler.save()
        self.selenium.quit_driver()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # These parameters should be obtained from Robocloud work item in a real scenario
    search_phrase = "climate"
    sort_category = "date"
    num_months = 2

    bot = NewsBot(search_phrase, sort_category, num_months)
    bot.run()
