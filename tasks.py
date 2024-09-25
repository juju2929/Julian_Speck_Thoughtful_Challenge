from robocorp import workitems
from news_scraper import NewsBot
from robocorp.tasks import task
import logging
import json
import os
import glob

import logging

@task
def run_task():
    # Automatically load the first input work item

    item = workitems.inputs.current
    """
    Runs the news scraper task.

    Automatically loads the first input work item and retrieves the following variables from it:
        - search_phrase: The search phrase to search for on the news site.
        - sort_category: The category to sort the results by.
        - num_months: The number of months to search for.

    Logs the received variables and runs the news scraper with the provided variables.

    Stores the scraped data in an output work item variable named "scraped_data" and saves the output work item.

    :raises KeyError: If any of the required variables are missing from the input work item.
    """
    print("Received item:", item)
    print("Received payload:", item.payload)

    try:
        search_phrase = item.get_work_item_variable("search_phrase")
        sort_category = item.get_work_item_variable("sort_category")
        num_months = item.get_work_item_variable("num_months")

    except KeyError as e:
        logging.error(f"Missing variable: {e}")
        return

    # Log the received variables
    logging.info(f"Search Phrase: {search_phrase}, Sort Category: {sort_category}, Number of Months: {num_months}")

    # Here, you can implement the logic for your NewsBot or any other processing
    scraper = NewsBot(search_phrase, sort_category, num_months)
    scraped_data = scraper.run()

    # Create an output work item to store the results
    workitems.create_output_work_item()
    workitems.set_work_item_variable("scraped_data", scraped_data)

    # Save the output work item
    workitems.save_work_item()

if __name__ == "__main__":
    run_task()
