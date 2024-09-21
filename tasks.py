# task.py
from robocorp import workitems
from news_scraper import NewsScraper

def main():
    # Get work item variables
    item = workitems.inputs.current
    search_phrase = item.payload["search_phrase"]
    news_category = item.payload["news_category"]
    num_months = item.payload["num_months"]

    # Initialize and run the scraper
    scraper = NewsScraper(search_phrase, news_category, num_months)
    scraper.run()

if __name__ == "__main__":
    main()