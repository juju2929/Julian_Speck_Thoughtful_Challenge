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
    search_phrase = payload.get("search_phrase", "default phrase")
    news_category = payload.get("news_category", "general")
    num_months = payload.get("num_months", 3)

    # Initialize and run the scraper
    scraper = NewsBot(search_phrase, news_category, num_months)
    scraper.run()

if __name__ == "__main__":
    run_task()
