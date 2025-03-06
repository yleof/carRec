# app/scrapers.py
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from typing import List, Dict, Any, Optional
import logging

class BaseScraper:
    """Base class for car listing scrapers."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def scrape(self, criteria: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape car listings based on provided criteria.
        
        Args:
            criteria: JSON string with search parameters
        
        Returns:
            List of car listing dictionaries
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def _parse_criteria(self, criteria_str: Optional[str]) -> Dict[str, Any]:
        """Parse JSON criteria string into a dictionary."""
        if not criteria_str:
            return {}
        try:
            return json.loads(criteria_str)
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON criteria provided")
            return {}


class AutoTraderScraper(BaseScraper):
    """Scraper for autotrader.ca car listings."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.autotrader.ca"
    
    def scrape(self, criteria: Optional[str] = None) -> List[Dict[str, Any]]:
        search_params = self._parse_criteria(criteria)
        cars = []
        
        # Construct search URL based on parameters
        search_url = self._build_search_url(search_params)
        
        # Get total pages
        total_pages = self._get_total_pages(search_url)
        
        # Scrape each page
        for page in range(1, total_pages + 1):
            page_url = f"{search_url}&page={page}"
            self.logger.info(f"Scraping page {page} of {total_pages}")
            
            try:
                response = requests.get(page_url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                car_listings = soup.select('.listing-details')
                
                for listing in car_listings:
                    car = self._parse_listing(listing)
                    if car:
                        cars.append(car)
                
                # Respect the website by waiting between requests
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                self.logger.error(f"Error scraping page {page}: {str(e)}")
        
        return cars
    
    def _build_search_url(self, params: Dict[str, Any]) -> str:
        """Build AutoTrader search URL from parameters."""
        base_search_url = f"{self.base_url}/cars/used"
        
        # Add search parameters
        query_parts = []
        if 'make' in params:
            query_parts.append(f"make={params['make']}")
        if 'model' in params:
            query_parts.append(f"model={params['model']}")
        if 'min_year' in params:
            query_parts.append(f"year-min={params['min_year']}")
        if 'max_year' in params:
            query_parts.append(f"year-max={params['max_year']}")
        if 'max_price' in params:
            query_parts.append(f"price-max={params['max_price']}")
        
        # Construct final URL
        if query_parts:
            return f"{base_search_url}?{'&'.join(query_parts)}"
        return base_search_url
    
    def _get_total_pages(self, url: str) -> int:
        """Get the total number of search result pages."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            pagination = soup.select('.pagination-dropdown-button')
            
            if pagination:
                text = pagination[0].get_text().strip()
                if 'of' in text:
                    return int(text.split('of')[1].strip())
            
            # If no pagination found or unable to parse, assume at least 1 page
            return 1
            
        except Exception as e:
            self.logger.error(f"Error getting total pages: {str(e)}")
            return 1
    
    def _parse_listing(self, listing_element) -> Dict[str, Any]:
        """Parse individual car listing HTML into a dictionary."""
        try:
            # Extract car details
            title_element = listing_element.select_one('.listing-title')
            price_element = listing_element.select_one('.price-amount')
            
            if not title_element or not price_element:
                return None
                
            title = title_element.get_text().strip()
            price_text = price_element.get_text().strip().replace('$', '').replace(',', '')
            
            # Parse title to extract year, make, model
            title_parts = title.split()
            year = int(title_parts[0]) if title_parts and title_parts[0].isdigit() else None
            make = title_parts[1] if len(title_parts) > 1 else ""
            model = ' '.join(title_parts[2:]) if len(title_parts) > 2 else ""
            
            # Extract additional details
            details = {}
            detail_elements = listing_element.select('.detail-line')
            for detail in detail_elements:
                key_element = detail.select_one('.key')
                value_element = detail.select_one('.value')
                
                if key_element and value_element:
                    key = key_element.get_text().strip().lower().replace(' ', '_')
                    value = value_element.get_text().strip()
                    details[key] = value
            
            # Extract URL
            url_element = listing_element.select_one('a.link')
            url = self.base_url + url_element['href'] if url_element and 'href' in url_element.attrs else None
            
            # Construct structured car data
            car = {
                'source': 'autotrader',
                'year': year,
                'make': make,
                'model': model,
                'price': int(price_text) if price_text.isdigit() else None,
                'url': url,
                'details': details,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return car
            
        except Exception as e:
            self.logger.error(f"Error parsing listing: {str(e)}")
            return None


class KijijiScraper(BaseScraper):
    """Scraper for kijiji.ca car listings."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.kijiji.ca"
    
    def scrape(self, criteria: Optional[str] = None) -> List[Dict[str, Any]]:
        search_params = self._parse_criteria(criteria)
        cars = []
        
        # Construct search URL based on parameters
        search_url = self._build_search_url(search_params)
        
        # Get total pages
        total_pages = self._get_total_pages(search_url)
        
        # Scrape each page
        for page in range(1, total_pages + 1):
            page_url = f"{search_url}&page={page}"
            self.logger.info(f"Scraping page {page} of {total_pages}")
            
            try:
                response = requests.get(page_url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                car_listings = soup.select('.search-item')
                
                for listing in car_listings:
                    car = self._parse_listing(listing)
                    if car:
                        cars.append(car)
                
                # Respect the website by waiting between requests
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                self.logger.error(f"Error scraping page {page}: {str(e)}")
        
        return cars
    
    def _build_search_url(self, params: Dict[str, Any]) -> str:
        """Build Kijiji search URL from parameters."""
        base_search_url = f"{self.base_url}/b-cars-vehicles/canada"
        
        # Add search parameters
        query_parts = []
        if 'make' in params:
            query_parts.append(f"carMake={params['make']}")
        if 'model' in params:
            query_parts.append(f"carModel={params['model']}")
        if 'min_year' in params:
            query_parts.append(f"carYearFrom={params['min_year']}")
        if 'max_year' in params:
            query_parts.append(f"carYearTo={params['max_year']}")
        if 'max_price' in params:
            query_parts.append(f"price_max={params['max_price']}")
        
        # Construct final URL
        if query_parts:
            return f"{base_search_url}?{'&'.join(query_parts)}"
        return base_search_url
    
    def _get_total_pages(self, url: str) -> int:
        """Get the total number of search result pages."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            pagination = soup.select('.pagination')
            
            if pagination:
                page_links = pagination[0].select('a')
                if page_links:
                    # Last page number is usually in the second-to-last link
                    last_page_text = page_links[-2].get_text().strip()
                    if last_page_text.isdigit():
                        return int(last_page_text)
            
            # If no pagination found or unable to parse, assume at least 1 page
            return 1
            
        except Exception as e:
            self.logger.error(f"Error getting total pages: {str(e)}")
            return 1
    
    def _parse_listing(self, listing_element) -> Dict[str, Any]:
        """Parse individual car listing HTML into a dictionary."""
        try:
            # Extract car details
            title_element = listing_element.select_one('.title')
            price_element = listing_element.select_one('.price')
            
            if not title_element or not price_element:
                return None
                
            title = title_element.get_text().strip()
            price_text = price_element.get_text().strip().replace('$', '').replace(',', '')
            
            # Extract year, make, model from title
            year = None
            make = ""
            model = ""
            
            # Attempt to extract year from title (assuming format like "2018 Honda Civic")
            words = title.split()
            if words and words[0].isdigit() and 1900 < int(words[0]) < 2100:
                year = int(words[0])
                if len(words) > 1:
                    make = words[1]
                if len(words) > 2:
                    model = ' '.join(words[2:])
            
            # Extract additional details
            details = {}
            attribute_elements = listing_element.select('.attribute')
            for attribute in attribute_elements:
                if ':' in attribute.get_text():
                    key, value = attribute.get_text().split(':', 1)
                    details[key.strip().lower().replace(' ', '_')] = value.strip()
            
            # Extract URL
            url_element = listing_element.select_one('a.title')
            url = self.base_url + url_element['href'] if url_element and 'href' in url_element.attrs else None
            
            # Parse price
            try:
                price = int(''.join(c for c in price_text if c.isdigit()))
            except:
                price = None
            
            # Construct structured car data
            car = {
                'source': 'kijiji',
                'year': year,
                'make': make,
                'model': model,
                'price': price,
                'url': url,
                'details': details,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return car
            
        except Exception as e:
            self.logger.error(f"Error parsing listing: {str(e)}")
            return None