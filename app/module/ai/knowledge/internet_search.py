import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
from urllib.parse import quote_plus

class InternetSearch:
    def __init__(self, search_engine: str = "duckduckgo"):
        """
        Initialize the search class
        Args:
            search_engine (str): Either 'duckduckgo' or 'google'
        """
        self.search_engine = search_engine.lower()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _get_duckduckgo_results(self, query: str, num_results: int = 5) -> List[Dict]:
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for result in soup.select('.result'):
                if len(results) >= num_results:
                    break
                    
                title_elem = result.select_one('.result__title')
                link_elem = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')
                
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'link': link_elem.get_text(strip=True),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"Error fetching results: {str(e)}")

    def _get_google_results(self, query: str, num_results: int = 5) -> List[Dict]:
        encoded_query = quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for result in soup.select('div.g'):
                if len(results) >= num_results:
                    break
                    
                title_elem = result.select_one('h3')
                link_elem = result.select_one('a')
                snippet_elem = result.select_one('div.VwiC3b')
                
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'link': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
            
            return results
            
        except requests.RequestException as e:
            raise Exception(f"Error fetching results: {str(e)}")

    def search(self, query: str, num_results: int = 5) -> str:
        """
        Perform a search and return results
        Args:
            query (str): Search query
            num_results (int): Number of results to return (default: 5)
        Returns:
            str: JSON string containing search results
        """
        
        if self.search_engine == "duckduckgo":
            results = self._get_duckduckgo_results(query, num_results)
        elif self.search_engine == "google":
            results = self._get_google_results(query, num_results)
        else:
            raise ValueError("Invalid search engine. Use 'duckduckgo' or 'google'")
            
        return json.dumps(results, indent=2)
