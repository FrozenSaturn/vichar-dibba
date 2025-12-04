import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
import os
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StartupScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.data: List[Dict] = []

    def scrape_yc(self):
        """
        Scrapes Y Combinator companies using Algolia API found in the page source.
        """
        logger.info("Scraping Y Combinator via Algolia...")
        # Algolia credentials found in the HTML
        app_id = "45BWZJ1SGC"
        api_key = "MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0YzFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiUyQyUyMllDQ29tcGFueV9CeV9MYXVuY2hfRGF0ZV9wcm9kdWN0aW9uJTIyJTVEJnRhZ0ZpbHRlcnM9JTVCJTIyeWNkY19wdWJsaWMlMjIlNUQmYW5hbHl0aWNzVGFncz0lNUIlMjJ5Y2RjJTIyJTVE"
        
        url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes/YCCompany_production/query"
        
        headers = {
            'X-Algolia-API-Key': api_key,
            'X-Algolia-Application-Id': app_id,
        }
        
        # We need to paginate to get all companies
        page = 0
        hits_per_page = 1000 # Max allowed might be 1000
        total_companies = 0
        
        while True:
            payload = {
                "params": f"hitsPerPage={hits_per_page}&page={page}&tagFilters=%5B%22ycdc_public%22%5D"
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                hits = data.get('hits', [])
                
                if not hits:
                    break
                
                for company in hits:
                    self.data.append({
                        'name': company.get('name'),
                        'description': company.get('one_liner') or company.get('long_description'),
                        'source': 'Y Combinator',
                        'status': 'Active', # Most in directory are active or acquired, but some might be dead.
                        'website': company.get('website'),
                        'batch': company.get('batch_name')
                    })
                
                total_companies += len(hits)
                logger.info(f"Fetched page {page}, total so far: {total_companies}")
                
                if page >= data.get('nbPages', 0) - 1:
                    break
                
                page += 1
                time.sleep(0.5) # Be nice
                
            except Exception as e:
                logger.error(f"Error scraping YC Algolia: {e}")
                break

    def scrape_failory(self):
        """
        Scrapes Failory for failed startups.
        """
        logger.info("Scraping Failory...")
        url = "https://www.failory.com/cemetery"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Updated selector based on debug HTML
            cards = soup.find_all('a', class_='cemetery-card-link-block')
            
            count = 0
            for card in cards:
                name_tag = card.find('h3', class_='card-title-black') # Assuming title has this class or is inside
                # If h3 is not direct child or has different class, we might need to search deeper
                if not name_tag:
                     name_tag = card.find('div', class_='card-title-black') # Sometimes it's a div
                
                desc_tag = card.find('p') # Description usually in a p tag
                
                if name_tag:
                    self.data.append({
                        'name': name_tag.text.strip(),
                        'description': desc_tag.text.strip() if desc_tag else None,
                        'source': 'Failory',
                        'status': 'Failed',
                        'website': f"https://www.failory.com{card['href']}",
                        'batch': None
                    })
                    count += 1
            logger.info(f"Found {count} startups from Failory.")

        except Exception as e:
            logger.error(f"Error scraping Failory: {e}")

    def scrape_autopsy(self):
        """
        Scrapes Autopsy.io.
        NOTE: Domain is currently for sale (dead).
        """
        logger.warning("Autopsy.io appears to be down/for sale. Skipping.")

    def scrape_graveyard(self):
        """
        Scrapes Startup Graveyard.
        NOTE: Site returns 500 Error (dead).
        """
        logger.warning("Startup Graveyard appears to be down (500 Error). Skipping.")

    def save_data(self, filename=None):
        if filename is None:
            # Default to data directory relative to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            filename = os.path.join(data_dir, 'startups.csv')

        if not self.data:
            logger.warning("No data to save.")
            return
        
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(df)} records to {filename}")

if __name__ == "__main__":
    scraper = StartupScraper()
    scraper.scrape_yc()
    scraper.scrape_failory()
    scraper.scrape_autopsy()
    scraper.scrape_graveyard()
    scraper.save_data()
