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
    workitems.get_input_work_item()

    try:
        search_phrase = workitems.get_work_item_variable("search_phrase", default_value="animals")
        sort_category = workitems.get_work_item_variable("sort_category", default_value="date")
        num_months = workitems.get_work_item_variable("num_months", default_value=0)

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
