from RPA.Robocorp.WorkItems import WorkItems
from news_scraper import NewsBot
from robocorp.tasks import task
import logging

@task
def run_task():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        work_items = WorkItems()
        work_items.get_input_work_item()

        # Extract payload from the current work item
        payload = work_items.get_work_item_variables()
        search_phrase = payload.get("search_phrase", "tech")
        sort_category = payload.get("sort_category", "date")
        num_months = int(payload.get("num_months", 0))

        # Log the received variables
        logging.info(f"Search Phrase: {search_phrase}, Sort Category: {sort_category}, Number of Months: {num_months}")

        # Initialize and run the NewsBot with the parameters
        scraper = NewsBot(search_phrase, sort_category, num_months)
        scraper.run()

        # The results are saved within the NewsBot's run method, so we don't need to handle it here

    except ValueError as e:
        logging.error(f"Invalid value in work item: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    run_task()