from robocorp import workitems
from news_scraper import NewsBot

from robocorp.tasks import task

@task
def run_task():
    # Get the current work item
    item = workitems.inputs.current
    
    # Safeguard for payload
    payload = item.payload if item and item.payload else {}

    # Extract variables with fallback defaults
    search_phrase = payload.get("search_phrase", "animals")
    sort_category = payload.get("sort_category", "date")
    num_months = payload.get("num_months", 12)

    # Initialize and run the scraper
    scraper = NewsBot(search_phrase, sort_category, num_months)
    scraper.run()

if __name__ == "__main__":
    run_task()
