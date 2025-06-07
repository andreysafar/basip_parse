#!/usr/bin/env python3
"""
BAS-IP API Documentation Scraper

This script logs into the BAS-IP developers portal, extracts information from the android-panels
section, and saves it to a markdown file for local reference.

Usage:
    python bas_ip_scraper.py

Requirements:
    - requests
    - beautifulsoup4
    - selenium (для более надежного парсинга)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
import sys
from datetime import datetime
import logging

# Configuration
BASE_URL = "https://developers.bas-ip.com"
OUTPUT_FILE = "bas_ip_android_panels.md"
API_DATA_FILE = "bas_ip_api_data.json"

# User credentials
EMAIL = "andrey.safar@gmail.com"
PASSWORD = "12345678"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

class BasIPScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.api_data = {}
        
    def login(self):
        """
        Log in to the BAS-IP developers portal
        """
        logger.info("Starting login process...")
        
        try:
            # First, visit the main page to get session cookies
            response = self.session.get(BASE_URL)
            logger.info(f"Initial page status: {response.status_code}")
            
            # Try to find the login form
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for CSRF tokens or hidden fields
            csrf_token = None
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                csrf_token = csrf_meta.get('content')
                logger.info("Found CSRF token")
            
            # Try different login endpoints
            login_endpoints = [
                f"{BASE_URL}/api/auth/login",
                f"{BASE_URL}/auth/login",
                f"{BASE_URL}/login",
                f"{BASE_URL}/api/login"
            ]
            
            for endpoint in login_endpoints:
                logger.info(f"Trying login endpoint: {endpoint}")
                
                login_data = {
                    "email": EMAIL,
                    "password": PASSWORD
                }
                
                if csrf_token:
                    login_data["_token"] = csrf_token
                    self.session.headers["X-CSRF-TOKEN"] = csrf_token
                
                # Try JSON request
                self.session.headers["Content-Type"] = "application/json"
                response = self.session.post(endpoint, json=login_data)
                
                if response.status_code == 200:
                    logger.info(f"Login successful at {endpoint}")
                    return True
                
                # Try form data
                self.session.headers["Content-Type"] = "application/x-www-form-urlencoded"
                response = self.session.post(endpoint, data=login_data)
                
                if response.status_code == 200:
                    logger.info(f"Login successful at {endpoint}")
                    return True
                
                logger.warning(f"Login failed at {endpoint}: {response.status_code}")
            
            # If all login attempts failed, try to parse the page directly
            logger.warning("All login attempts failed, trying direct page parsing...")
            return self.try_direct_parsing()
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def try_direct_parsing(self):
        """
        Try to parse the documentation directly without login
        """
        logger.info("Attempting direct parsing of documentation...")
        
        try:
            # Common documentation URLs
            doc_urls = [
                f"{BASE_URL}/documentation",
                f"{BASE_URL}/docs",
                f"{BASE_URL}/api-docs",
                f"{BASE_URL}/reference",
                f"{BASE_URL}/bas-ip-android-panels"
            ]
            
            for url in doc_urls:
                logger.info(f"Trying URL: {url}")
                response = self.session.get(url)
                
                if response.status_code == 200:
                    logger.info(f"Successfully accessed {url}")
                    self.parse_documentation_page(response.text, url)
            
            return len(self.api_data) > 0
            
        except Exception as e:
            logger.error(f"Direct parsing error: {str(e)}")
            return False
    
    def parse_documentation_page(self, html_content, url):
        """
        Parse a documentation page for API information
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for API endpoints
        # Common patterns in API documentation
        api_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)',
            r'endpoint[:\s]+([^\s]+)',
            r'url[:\s]+([^\s]+)',
            r'path[:\s]+([^\s]+)'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    method = match[0] if len(match) > 1 else 'GET'
                    endpoint = match[1] if len(match) > 1 else match[0]
                else:
                    method = 'GET'
                    endpoint = match
                
                if endpoint not in self.api_data:
                    self.api_data[endpoint] = {
                        'method': method,
                        'url': url,
                        'parameters': [],
                        'description': ''
                    }
        
        # Look for code blocks that might contain API examples
        code_blocks = soup.find_all(['code', 'pre'])
        for block in code_blocks:
            text = block.get_text()
            # Look for JSON examples
            if '{' in text and '}' in text:
                try:
                    json_data = json.loads(text)
                    logger.info(f"Found JSON example: {json_data}")
                except:
                    pass
    
    def get_android_panels_data(self):
        """
        Extract data specific to android-panels
        """
        logger.info("Searching for android-panels documentation...")
        
        # Search for android panels specific pages
        search_terms = [
            "android-panels",
            "android_panels",
            "android panels",
            "bas-ip-android",
            "android api"
        ]
        
        for term in search_terms:
            search_url = f"{BASE_URL}/search?q={term}"
            response = self.session.get(search_url)
            
            if response.status_code == 200:
                self.parse_documentation_page(response.text, search_url)
        
        # Try specific android panels URLs
        android_urls = [
            f"{BASE_URL}/documentation/android-panels",
            f"{BASE_URL}/docs/android-panels",
            f"{BASE_URL}/api/android-panels",
            f"{BASE_URL}/reference/android-panels"
        ]
        
        for url in android_urls:
            response = self.session.get(url)
            if response.status_code == 200:
                logger.info(f"Found android panels documentation at {url}")
                self.parse_android_panels_page(response.text, url)
    
    def parse_android_panels_page(self, html_content, url):
        """
        Parse android panels specific documentation
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract all API methods
        api_sections = soup.find_all(['div', 'section'], class_=re.compile(r'api|method|endpoint', re.I))
        
        for section in api_sections:
            # Extract method name
            method_name = None
            method_header = section.find(['h1', 'h2', 'h3', 'h4'])
            if method_header:
                method_name = method_header.get_text().strip()
            
            # Extract parameters
            params = []
            param_table = section.find('table')
            if param_table:
                rows = param_table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        param_name = cells[0].get_text().strip()
                        param_type = cells[1].get_text().strip() if len(cells) > 1 else ''
                        param_desc = cells[2].get_text().strip() if len(cells) > 2 else ''
                        params.append({
                            'name': param_name,
                            'type': param_type,
                            'description': param_desc
                        })
            
            # Extract description
            description = ''
            desc_elem = section.find(['p', 'div'], class_=re.compile(r'desc|description', re.I))
            if desc_elem:
                description = desc_elem.get_text().strip()
            
            if method_name:
                self.api_data[method_name] = {
                    'url': url,
                    'parameters': params,
                    'description': description
                }
    
    def save_data(self):
        """
        Save collected data to files
        """
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
        """
        Convert collected data to markdown format
        """
        md_lines = [
            "# BAS-IP Android Panels API Documentation",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Overview",
            "This document contains API documentation for BAS-IP Android Panels.",
            "",
            "## API Methods",
            ""
        ]
        
        if not self.api_data:
            md_lines.append("**No API data was collected. This might be due to authentication issues or changes in the website structure.**")
            md_lines.append("")
            md_lines.append("## Manual Steps Required")
            md_lines.append("1. Visit https://developers.bas-ip.com manually")
            md_lines.append("2. Log in with the provided credentials")
            md_lines.append("3. Navigate to the android-panels documentation")
            md_lines.append("4. Update this script with the correct authentication method")
        else:
            for endpoint, data in self.api_data.items():
                md_lines.append(f"### {endpoint}")
                if data.get('description'):
                    md_lines.append(data['description'])
                md_lines.append("")
                
                if data.get('method'):
                    md_lines.append(f"**Method:** `{data['method']}`")
                    md_lines.append("")
                
                if data.get('parameters'):
                    md_lines.append("**Parameters:**")
                    md_lines.append("| Name | Type | Description |")
                    md_lines.append("|------|------|-------------|")
                    for param in data['parameters']:
                        md_lines.append(f"| {param.get('name', '')} | {param.get('type', '')} | {param.get('description', '')} |")
                    md_lines.append("")
        
        return "\n".join(md_lines)
    
    def run(self):
        """
        Main execution method
        """
        logger.info("Starting BAS-IP API documentation scraper...")
        
        if self.login() or self.try_direct_parsing():
            self.get_android_panels_data()
            self.save_data()
            logger.info("Scraping completed successfully!")
            return True
        else:
            logger.error("Failed to access BAS-IP documentation")
            # Save what we have anyway
            self.save_data()
            return False

def main():
    scraper = BasIPScraper()
    scraper.run()

if __name__ == "__main__":
    main()
