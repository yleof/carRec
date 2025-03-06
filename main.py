# app/main.py
import argparse
from scrapers import AutoTraderScraper, KijijiScraper
from database import Database
from llm_service import LLMService
from analyzer import CarAnalyzer
from config import Config

def main():
    """Main entry point for the car recommendation application."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Pre-owned Car Recommendation Tool')
    parser.add_argument('--scrape', action='store_true', help='Scrape new car listings')
    parser.add_argument('--analyze', action='store_true', help='Analyze stored car listings')
    parser.add_argument('--criteria', type=str, help='Search criteria in JSON format')
    args = parser.parse_args()
    
    # Load configuration
    config = Config()
    
    # Initialize components
    db = Database(config.database_path)
    llm_service = LLMService(config.llm_config)
    analyzer = CarAnalyzer(db, llm_service)
    
    # Execute requested operation
    if args.scrape:
        print("Scraping car listings...")
        autotrader_scraper = AutoTraderScraper()
        kijiji_scraper = KijijiScraper()
        
        # Scrape and store car listings
        autotrader_cars = autotrader_scraper.scrape(args.criteria)
        kijiji_cars = kijiji_scraper.scrape(args.criteria)
        
        # Store the results
        db.add_cars(autotrader_cars + kijiji_cars)
        print(f"Scraped and stored {len(autotrader_cars) + len(kijiji_cars)} car listings")
    
    if args.analyze:
        print("Analyzing car listings...")
        top_recommendations = analyzer.get_recommendations(args.criteria)
        for idx, car in enumerate(top_recommendations, 1):
            print(f"{idx}. {car['year']} {car['make']} {car['model']} - ${car['price']}")
            print(f"   Analysis: {car['analysis']}")
            print()

if __name__ == "__main__":
    main()