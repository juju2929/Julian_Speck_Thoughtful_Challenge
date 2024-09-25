from robocorp import workitems
from news_scraper import NewsBot
from robocorp.tasks import task
import logging
import json
import os
import glob

import logging
from RPA.Robocorp.WorkItems import WorkItems

# Initialize the WorkItems library
workitems = WorkItems()

@task
def run_task():
    # Automatically load the first input work item

    item = workitems.inputs.current
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
