"""
Web Scraper Module for WorkProof
Extracts structured data from websites for comparison with OCR results.
Supports multiple HTML structures: tables, forms, labeled divs/spans.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import logging
import re

logger = logging.getLogger("WorkProof.WebScraper")


class WebScraper:
    """
    Flexible web scraper that can extract field-value pairs from various HTML structures.
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the web scraper.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_url(self, url: str) -> Dict[str, str]:
        """
        Main scraping function - tries multiple extraction strategies.
        
        Args:
            url: Target URL to scrape
            
        Returns:
            Dictionary of field-value pairs
            
        Raises:
            ValueError: If URL is invalid
            requests.RequestException: If request fails
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Scraping URL: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple extraction strategies and combine results
            data = {}
            
            # Strategy 1: Extract from tables
            table_data = self._extract_from_tables(soup)
            data.update(table_data)
            logger.info(f"Extracted {len(table_data)} fields from tables")
            
            # Strategy 2: Extract from forms
            form_data = self._extract_from_forms(soup)
            data.update(form_data)
            logger.info(f"Extracted {len(form_data)} fields from forms")
            
            # Strategy 3: Extract from labeled elements (divs, spans, etc.)
            labeled_data = self._extract_labeled_data(soup)
            data.update(labeled_data)
            logger.info(f"Extracted {len(labeled_data)} fields from labeled elements")
            
            # Strategy 4: Extract from definition lists
            dl_data = self._extract_from_definition_lists(soup)
            data.update(dl_data)
            logger.info(f"Extracted {len(dl_data)} fields from definition lists")
            
            logger.info(f"Total fields extracted: {len(data)}")
            return data
            
        except requests.Timeout:
            logger.error(f"Request timeout for URL: {url}")
            raise requests.RequestException(f"Request timed out after {self.timeout} seconds")
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}")
            raise
    
    def _extract_from_tables(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract data from HTML tables.
        Supports both horizontal (header row) and vertical (label column) tables.
        """
        data = {}
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Check if first row is a header row
            headers = []
            first_row = rows[0] if rows else None
            if first_row:
                header_cells = first_row.find_all(['th', 'td'])
                if header_cells and header_cells[0].name == 'th':
                    # Horizontal table with header row
                    headers = [self._clean_text(cell.get_text()) for cell in header_cells]
                    
                    # Extract data rows
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        for idx, cell in enumerate(cells):
                            if idx < len(headers):
                                key = headers[idx]
                                value = self._clean_text(cell.get_text())
                                if key and value:
                                    data[key] = value
                else:
                    # Vertical table (label-value pairs in rows)
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            key = self._clean_text(cells[0].get_text())
                            value = self._clean_text(cells[1].get_text())
                            if key and value:
                                data[key] = value
        
        return data
    
    def _extract_from_forms(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract data from HTML forms (input, select, textarea elements).
        """
        data = {}
        forms = soup.find_all('form')
        
        for form in forms:
            # Find all input fields
            inputs = form.find_all(['input', 'select', 'textarea'])
            
            for input_elem in inputs:
                # Get field name/id
                name = input_elem.get('name') or input_elem.get('id', '')
                
                # Get field value
                value = ''
                if input_elem.name == 'select':
                    selected = input_elem.find('option', selected=True)
                    value = selected.get_text() if selected else ''
                elif input_elem.name == 'textarea':
                    value = input_elem.get_text()
                else:
                    value = input_elem.get('value', '')
                
                # Try to find associated label
                label_text = self._find_label_for_input(soup, input_elem)
                
                key = label_text or self._clean_field_name(name)
                value = self._clean_text(value)
                
                if key and value:
                    data[key] = value
        
        return data
    
    def _extract_labeled_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract data from labeled elements (common patterns like label: value).
        """
        data = {}
        
        # Pattern 1: <label>Field Name:</label> <span>Value</span>
        labels = soup.find_all(['label', 'dt', 'strong', 'b'])
        for label in labels:
            label_text = self._clean_text(label.get_text())
            
            # Skip if label is empty or too long (likely not a field label)
            if not label_text or len(label_text) > 100:
                continue
            
            # Remove trailing colon
            label_text = label_text.rstrip(':').strip()
            
            # Find next sibling that might contain the value
            value_elem = label.find_next_sibling()
            if value_elem:
                value = self._clean_text(value_elem.get_text())
                if value and len(value) < 500:  # Reasonable value length
                    data[label_text] = value
        
        # Pattern 2: Divs with class patterns like "field", "data-item", etc.
        field_containers = soup.find_all(['div', 'span'], class_=re.compile(r'(field|data|item|row|entry)', re.I))
        
        for container in field_containers:
            # Look for label-value pairs within the container
            label_elem = container.find(['label', 'span', 'div'], class_=re.compile(r'(label|key|name)', re.I))
            value_elem = container.find(['span', 'div'], class_=re.compile(r'(value|data|text)', re.I))
            
            if label_elem and value_elem:
                key = self._clean_text(label_elem.get_text()).rstrip(':').strip()
                value = self._clean_text(value_elem.get_text())
                
                if key and value and len(key) < 100 and len(value) < 500:
                    data[key] = value
        
        return data
    
    def _extract_from_definition_lists(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract data from HTML definition lists (<dl>, <dt>, <dd>).
        """
        data = {}
        definition_lists = soup.find_all('dl')
        
        for dl in definition_lists:
            terms = dl.find_all('dt')
            definitions = dl.find_all('dd')
            
            # Pair up terms and definitions
            for dt, dd in zip(terms, definitions):
                key = self._clean_text(dt.get_text()).rstrip(':').strip()
                value = self._clean_text(dd.get_text())
                
                if key and value:
                    data[key] = value
        
        return data
    
    def _find_label_for_input(self, soup: BeautifulSoup, input_elem) -> Optional[str]:
        """
        Find the label associated with an input element.
        """
        input_id = input_elem.get('id')
        
        if input_id:
            # Look for <label for="input_id">
            label = soup.find('label', {'for': input_id})
            if label:
                return self._clean_text(label.get_text()).rstrip(':').strip()
        
        # Look for parent label
        parent_label = input_elem.find_parent('label')
        if parent_label:
            # Get label text excluding the input's value
            label_text = parent_label.get_text()
            return self._clean_text(label_text).rstrip(':').strip()
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and special characters.
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.strip()
        
        return text
    
    def _clean_field_name(self, name: str) -> str:
        """
        Convert field names from code format to human-readable format.
        Example: "customer_id" -> "Customer ID"
        """
        if not name:
            return ""
        
        # Replace underscores and hyphens with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is accessible.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is accessible, False otherwise
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = self.session.head(url, timeout=5)
            return response.status_code < 400
        except:
            return False


# Utility function for quick scraping
def scrape_website(url: str) -> Dict[str, str]:
    """
    Convenience function to scrape a website.
    
    Args:
        url: Target URL
        
    Returns:
        Dictionary of extracted field-value pairs
    """
    scraper = WebScraper()
    return scraper.scrape_url(url)
