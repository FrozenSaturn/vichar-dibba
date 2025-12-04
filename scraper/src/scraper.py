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
        Iterates through batches to overcome the 1000 hit limit.
        """
        logger.info("Scraping Y Combinator via Algolia...")
        app_id = "45BWZJ1SGC"
        api_key = "MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0YzFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiUyQyUyMllDQ29tcGFueV9CeV9MYXVuY2hfRGF0ZV9wcm9kdWN0aW9uJTIyJTVEJnRhZ0ZpbHRlcnM9JTVCJTIyeWNkY19wdWJsaWMlMjIlNUQmYW5hbHl0aWNzVGFncz0lNUIlMjJ5Y2RjJTIyJTVE"
        
        url = f"https://{app_id.lower()}-dsn.algolia.net/1/indexes/YCCompany_production/query"
        
        headers = {
            'X-Algolia-API-Key': api_key,
            'X-Algolia-Application-Id': app_id,
        }

        # Step 1: Get all batches
        try:
            payload = {
                "params": "hitsPerPage=0&facets=%5B%22batch%22%5D&tagFilters=%5B%22ycdc_public%22%5D"
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            facets = response.json().get('facets', {}).get('batch', {})
            batches = list(facets.keys())
            logger.info(f"Found {len(batches)} batches to scrape.")
        except Exception as e:
            logger.error(f"Error fetching YC batches: {e}")
            return

        total_companies = 0
        
        # Step 2: Iterate over batches
        for batch in batches:
            # logger.info(f"Scraping batch: {batch}")
            page = 0
            while True:
                # Filter by batch
                filters = f'batch:"{batch}"'
                # URL encode the filter? requests json handles it if we pass it correctly?
                # Algolia params string needs to be carefully formatted.
                # Better to use `facetFilters` in the params string or JSON.
                # params string format: `facetFilters=[["batch:Winter 2024"]]`
                
                # Let's construct the params string carefully
                # We can use `filters` parameter which is easier: `filters=batch:"Winter 2024"`
                
                payload = {
                    "params": f"hitsPerPage=1000&page={page}&filters=batch:\"{batch}\"&tagFilters=%5B%22ycdc_public%22%5D"
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
                            'status': 'Active', 
                            'website': company.get('website'),
                            'batch': company.get('batch')
                        })
                    
                    total_companies += len(hits)
                    
                    if page >= data.get('nbPages', 0) - 1:
                        break
                    page += 1
                    time.sleep(0.1) 
                    
                except Exception as e:
                    logger.error(f"Error scraping batch {batch}: {e}")
                    break
            
            # logger.info(f"Finished batch {batch}. Total so far: {total_companies}")
            time.sleep(0.1)

        logger.info(f"Finished scraping YC. Total companies: {total_companies}")

    def scrape_failory(self):
        """
        Scrapes Failory's cemetery for failed startups.
        Iterates through all pages using the 'Next' pagination link.
        """
        logger.info("Scraping Failory...")
        base_url = "https://www.failory.com"
        url = f"{base_url}/cemetery"
        
        count = 0
        page_num = 1
        
        while url:
            # logger.info(f"Fetching Failory page {page_num}: {url}")
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch {url}: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Cards are in 'a' tags with class 'cemetery-card-link-block'
                cards = soup.find_all('a', class_='cemetery-card-link-block')
                
                if not cards:
                    logger.warning(f"No cards found on page {page_num}")
                    break
                
                for card in cards:
                    # Name is usually in h3 or div with class 'card-title-black'
                    name_tag = card.find(class_='card-title-black')
                    if not name_tag:
                        continue
                    
                    name = name_tag.text.strip()
                    
                    # Description
                    desc_tag = card.find(class_='card-date-black') # Based on debug HTML, description is here
                    description = desc_tag.text.strip() if desc_tag else None
                    
                    # Link
                    link = f"{base_url}{card['href']}" if card.get('href') else None
                    
                    # Status - Failory is about failed startups, but some might be acquired
                    # We can try to find the 'outcome' filter tag if present, or default to 'Failed'
                    # In the debug HTML, there are hidden fields like fs-list-field="outcome"
                    outcome = "Failed"
                    outcome_tag = card.find(attrs={"fs-list-field": "outcome"})
                    if outcome_tag:
                        outcome = outcome_tag.text.strip()
                    
                    self.data.append({
                        'name': name,
                        'description': description,
                        'source': 'Failory',
                        'status': outcome,
                        'website': link,
                        'batch': None
                    })
                    count += 1
                
                # Pagination
                next_button = soup.find('a', class_='w-pagination-next')
                if next_button and next_button.get('href'):
                    url = f"{base_url}/cemetery{next_button['href']}" # href is likely like ?page=2
                    page_num += 1
                    time.sleep(0.5)
                else:
                    url = None
                    
            except Exception as e:
                logger.error(f"Error scraping Failory page {page_num}: {e}")
                break
                
        logger.info(f"Found {count} startups from Failory.")

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

    def scrape_betalist(self):
        """
        Scrapes BetaList for new startups.
        Fetches from homepage and popular topics.
        """
        logger.info("Scraping BetaList...")
        base_url = "https://betalist.com"
        topics = [
            "/",
            "/topics/saas",
            "/topics/ai-tools",
            "/topics/developer-tools",
            "/topics/web-tools",
            "/topics/apps",
            "/topics/b2b",
            "/topics/education",
            "/topics/productivity"
        ]
        
        count = 0
        seen_names = set()
        
        # Pre-populate seen_names with existing data to avoid duplicates across sources if needed
        # But for now just avoid duplicates within BetaList scrape
        
        for topic in topics:
            url = f"{base_url}{topic}"
            # logger.info(f"Fetching BetaList topic: {topic}")
            try:
                response = requests.get(url, headers=self.headers)
                # BetaList might 404 on some topics if they don't exist, but these are from homepage
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Startups are usually in a div with id starting with 'startup-' inside a grid
                # Based on debug HTML: <div class="block" id="startup-140720">
                startup_cards = soup.find_all('div', id=lambda x: x and x.startswith('startup-'))
                
                for card in startup_cards:
                    # Name is in an 'a' tag with class 'font-medium'
                    # <a ... href="/startups/mindpali">Mindpali</a>
                    name_tag = card.find('a', class_='font-medium')
                    if not name_tag:
                        continue
                    
                    name = name_tag.text.strip()
                    if name in seen_names:
                        continue
                    
                    # Description is in the next 'a' tag or div
                    # <a class="block text-gray-500..." href="...">Turn study notes...</a>
                    desc_tag = card.find('a', class_='text-gray-500')
                    description = desc_tag.text.strip() if desc_tag else None
                    
                    # Link
                    link = f"{base_url}{name_tag['href']}"
                    
                    self.data.append({
                        'name': name,
                        'description': description,
                        'source': 'BetaList',
                        'status': 'Active', # BetaList is for new startups
                        'website': link, # This is the BetaList profile link. The actual site is on that page.
                        'batch': None
                    })
                    seen_names.add(name)
                    count += 1
                
                time.sleep(0.5) # Be nice
                
            except Exception as e:
                logger.error(f"Error scraping BetaList {topic}: {e}")
        
        logger.info(f"Found {count} startups from BetaList.")

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
    scraper.scrape_betalist()
    scraper.scrape_autopsy()
    scraper.scrape_graveyard()
    scraper.save_data()
