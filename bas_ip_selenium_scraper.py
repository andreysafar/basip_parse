#!/usr/bin/env python3
"""
BAS-IP API Documentation Scraper with Selenium

This script uses Selenium to log into the BAS-IP developers portal and extract
API documentation for android-panels.
"""

import json
import time
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuration
BASE_URL = "https://developers.bas-ip.com"
OUTPUT_FILE = "bas_ip_android_panels_detailed.md"
API_DATA_FILE = "bas_ip_api_data_detailed.json"

# User credentials
EMAIL = "andrey.safar@gmail.com"
PASSWORD = "12345678"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SeleniumBasIPScraper:
    def __init__(self, headless=True):
        self.driver = None
        self.api_data = {}
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Set up Chrome driver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Use webdriver-manager to automatically download the correct driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome driver initialized")
    
    def login(self):
        """Log in to the BAS-IP developers portal"""
        try:
            logger.info("Navigating to BAS-IP developers portal...")
            self.driver.get(BASE_URL)
            time.sleep(3)  # Wait for page to load
            
            # Look for login button or form
            login_selectors = [
                "//button[contains(text(), 'Login')]",
                "//a[contains(text(), 'Login')]",
                "//button[contains(text(), 'Sign in')]",
                "//a[contains(text(), 'Sign in')]",
                "//input[@type='email']",
                "//input[@name='email']",
                "//input[@id='email']"
            ]
            
            login_found = False
            for selector in login_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.tag_name in ['button', 'a']:
                        element.click()
                        time.sleep(2)
                    login_found = True
                    break
                except NoSuchElementException:
                    continue
            
            # Try to find email and password fields
            try:
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='email' or @name='email' or @id='email']"))
                )
                password_field = self.driver.find_element(By.XPATH, "//input[@type='password' or @name='password' or @id='password']")
                
                logger.info("Found login form, entering credentials...")
                email_field.clear()
                email_field.send_keys(EMAIL)
                password_field.clear()
                password_field.send_keys(PASSWORD)
                
                # Find and click submit button
                submit_selectors = [
                    "//button[@type='submit']",
                    "//button[contains(text(), 'Login')]",
                    "//button[contains(text(), 'Sign in')]",
                    "//input[@type='submit']"
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_btn = self.driver.find_element(By.XPATH, selector)
                        submit_btn.click()
                        logger.info("Login form submitted")
                        time.sleep(3)
                        return True
                    except NoSuchElementException:
                        continue
                
                # If no submit button found, try pressing Enter
                password_field.send_keys(Keys.RETURN)
                time.sleep(3)
                return True
                
            except TimeoutException:
                logger.warning("Could not find login form")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def navigate_to_android_panels(self):
        """Navigate to android-panels documentation"""
        try:
            # Try different navigation paths
            nav_paths = [
                "//a[contains(text(), 'Android Panels')]",
                "//a[contains(text(), 'android-panels')]",
                "//a[contains(@href, 'android-panels')]",
                "//a[contains(text(), 'Android')]",
                "//a[contains(text(), 'API')]",
                "//a[contains(text(), 'Documentation')]"
            ]
            
            for path in nav_paths:
                try:
                    link = self.driver.find_element(By.XPATH, path)
                    logger.info(f"Found link: {link.text}")
                    link.click()
                    time.sleep(2)
                    
                    # Check if we're on android-panels page
                    if "android" in self.driver.current_url.lower():
                        logger.info("Successfully navigated to Android panels documentation")
                        return True
                except NoSuchElementException:
                    continue
            
            # Try direct URL navigation
            android_urls = [
                f"{BASE_URL}/documentation/android-panels",
                f"{BASE_URL}/docs/android-panels",
                f"{BASE_URL}/android-panels",
                f"{BASE_URL}/api/android-panels"
            ]
            
            for url in android_urls:
                self.driver.get(url)
                time.sleep(2)
                if self.driver.current_url != BASE_URL and "404" not in self.driver.page_source:
                    logger.info(f"Successfully navigated to {url}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return False
    
    def extract_api_methods(self):
        """Extract API methods from the current page"""
        try:
            # Wait for content to load
            time.sleep(3)
            
            # Common selectors for API documentation
            api_selectors = [
                "//div[contains(@class, 'api-method')]",
                "//div[contains(@class, 'method')]",
                "//div[contains(@class, 'endpoint')]",
                "//section[contains(@class, 'api')]",
                "//div[contains(@class, 'operation')]"
            ]
            
            for selector in api_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    logger.info(f"Found {len(elements)} API method elements")
                    for element in elements:
                        self.extract_method_details(element)
            
            # Also try to extract from code blocks
            code_blocks = self.driver.find_elements(By.XPATH, "//pre | //code")
            for block in code_blocks:
                text = block.text
                if any(method in text.upper() for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
                    self.parse_code_block(text)
            
            # Extract from tables
            tables = self.driver.find_elements(By.XPATH, "//table")
            for table in tables:
                self.parse_api_table(table)
                
        except Exception as e:
            logger.error(f"Error extracting API methods: {str(e)}")
    
    def extract_method_details(self, element):
        """Extract details from an API method element"""
        try:
            method_data = {
                'name': '',
                'endpoint': '',
                'method': '',
                'description': '',
                'parameters': [],
                'response': '',
                'example': ''
            }
            
            # Extract method name/title
            headers = element.find_elements(By.XPATH, ".//h1 | .//h2 | .//h3 | .//h4")
            if headers:
                method_data['name'] = headers[0].text.strip()
            
            # Extract HTTP method and endpoint
            method_text = element.text
            import re
            method_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)'
            matches = re.findall(method_pattern, method_text)
            if matches:
                method_data['method'] = matches[0][0]
                method_data['endpoint'] = matches[0][1]
            
            # Extract description
            desc_elements = element.find_elements(By.XPATH, ".//p")
            if desc_elements:
                method_data['description'] = desc_elements[0].text.strip()
            
            # Extract parameters
            param_sections = element.find_elements(By.XPATH, ".//table | .//dl | .//ul")
            for section in param_sections:
                self.extract_parameters(section, method_data['parameters'])
            
            # Extract example
            example_blocks = element.find_elements(By.XPATH, ".//pre | .//code")
            if example_blocks:
                method_data['example'] = example_blocks[0].text.strip()
            
            # Save to api_data
            if method_data['name'] or method_data['endpoint']:
                key = method_data['name'] or method_data['endpoint']
                self.api_data[key] = method_data
                logger.info(f"Extracted method: {key}")
                
        except Exception as e:
            logger.error(f"Error extracting method details: {str(e)}")
    
    def extract_parameters(self, element, params_list):
        """Extract parameters from a table or list element"""
        try:
            if element.tag_name == 'table':
                rows = element.find_elements(By.XPATH, ".//tr")[1:]  # Skip header
                for row in rows:
                    cells = row.find_elements(By.XPATH, ".//td")
                    if len(cells) >= 2:
                        param = {
                            'name': cells[0].text.strip(),
                            'type': cells[1].text.strip() if len(cells) > 1 else '',
                            'description': cells[2].text.strip() if len(cells) > 2 else '',
                            'required': cells[3].text.strip() if len(cells) > 3 else ''
                        }
                        params_list.append(param)
            
        except Exception as e:
            logger.error(f"Error extracting parameters: {str(e)}")
    
    def parse_code_block(self, text):
        """Parse API information from code blocks"""
        import re
        
        # Look for API endpoints
        endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)'
        matches = re.findall(endpoint_pattern, text)
        
        for method, endpoint in matches:
            if endpoint not in self.api_data:
                self.api_data[endpoint] = {
                    'method': method,
                    'endpoint': endpoint,
                    'raw_text': text
                }
    
    def parse_api_table(self, table):
        """Parse API information from tables"""
        try:
            headers = table.find_elements(By.XPATH, ".//th")
            if any('endpoint' in h.text.lower() or 'method' in h.text.lower() for h in headers):
                rows = table.find_elements(By.XPATH, ".//tr")[1:]
                for row in rows:
                    cells = row.find_elements(By.XPATH, ".//td")
                    if len(cells) >= 2:
                        # Extract endpoint and method info
                        endpoint_text = ' '.join(cell.text for cell in cells)
                        self.parse_code_block(endpoint_text)
                        
        except Exception as e:
            logger.error(f"Error parsing API table: {str(e)}")
    
    def save_data(self):
        """Save collected data to files"""
        # Save JSON data
        with open(API_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.api_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved API data to {API_DATA_FILE}")
        
        # Convert to markdown
        md_content = self.convert_to_markdown()
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Saved markdown to {OUTPUT_FILE}")
    
    def convert_to_markdown(self):
        """Convert collected data to markdown format"""
        md_lines = [
            "# BAS-IP Android Panels API Documentation",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*Using Selenium WebDriver*",
            "",
            "## Overview",
            "This document contains API documentation for BAS-IP Android Panels extracted using Selenium.",
            "",
            "## API Methods",
            ""
        ]
        
        if not self.api_data:
            md_lines.append("**No API data was collected. The website may require manual intervention or have changed its structure.**")
        else:
            for key, data in self.api_data.items():
                md_lines.append(f"### {data.get('name', key)}")
                
                if data.get('description'):
                    md_lines.append(data['description'])
                    md_lines.append("")
                
                if data.get('method') and data.get('endpoint'):
                    md_lines.append(f"```")
                    md_lines.append(f"{data['method']} {data['endpoint']}")
                    md_lines.append(f"```")
                    md_lines.append("")
                
                if data.get('parameters'):
                    md_lines.append("**Parameters:**")
                    md_lines.append("| Name | Type | Description | Required |")
                    md_lines.append("|------|------|-------------|----------|")
                    for param in data['parameters']:
                        md_lines.append(f"| {param.get('name', '')} | {param.get('type', '')} | {param.get('description', '')} | {param.get('required', '')} |")
                    md_lines.append("")
                
                if data.get('example'):
                    md_lines.append("**Example:**")
                    md_lines.append("```json")
                    md_lines.append(data['example'])
                    md_lines.append("```")
                    md_lines.append("")
                
                if data.get('raw_text'):
                    md_lines.append("**Raw Text:**")
                    md_lines.append("```")
                    md_lines.append(data['raw_text'])
                    md_lines.append("```")
                    md_lines.append("")
                
                md_lines.append("---")
                md_lines.append("")
        
        return "\n".join(md_lines)
    
    def run(self):
        """Main execution method"""
        try:
            logger.info("Starting Selenium-based BAS-IP scraper...")
            
            # Try to login
            login_success = self.login()
            
            # Navigate to android panels documentation
            if login_success:
                nav_success = self.navigate_to_android_panels()
            else:
                logger.warning("Proceeding without login...")
                nav_success = self.navigate_to_android_panels()
            
            # Extract API methods
            if nav_success or True:  # Always try to extract something
                self.extract_api_methods()
            
            # Save data
            self.save_data()
            
            logger.info("Scraping completed!")
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")

def main():
    # Run with headless=False to see the browser in action
    scraper = SeleniumBasIPScraper(headless=True)
    scraper.run()

if __name__ == "__main__":
    main()