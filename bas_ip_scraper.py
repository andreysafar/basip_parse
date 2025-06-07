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
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
import sys
import hashlib
from datetime import datetime
import logging

# Configuration
BASE_URL = "https://developers.bas-ip.com"
AUTH_URL = "https://developers.bas-ip.com/api/auth/login"
API_BASE_URL = "https://developers.bas-ip.com/api"
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
    "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
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
        self.token = None
        
    def get_md5_hash(self, password):
        """Convert password to MD5 hash as required by API"""
        return hashlib.md5(password.encode()).hexdigest().upper()
        
    def login(self):
        """
        Log in to the BAS-IP developers portal using the correct API
        """
        logger.info("Starting login process...")
        
        try:
            # Hash the password
            password_hash = self.get_md5_hash(PASSWORD)
            logger.info(f"Password hash: {password_hash}")
            
            # Try the documented login endpoint with GET method and query parameters
            login_params = {
                "username": EMAIL,
                "password": password_hash
            }
            
            logger.info(f"Attempting login to {AUTH_URL}")
            logger.info(f"Username: {EMAIL}")
            
            response = self.session.get(AUTH_URL, params=login_params)
            logger.info(f"Login response status: {response.status_code}")
            logger.info(f"Login response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"Login response data: {response_data}")
                    
                    if 'token' in response_data:
                        self.token = response_data['token']
                        # Add Bearer token to session headers
                        self.session.headers["Authorization"] = f"Bearer {self.token}"
                        logger.info("Login successful! Bearer token obtained.")
                        return True
                    else:
                        logger.error("No token in response")
                        return False
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON response")
                    logger.info(f"Response text: {response.text}")
                    return False
            else:
                logger.error(f"Login failed with status {response.status_code}")
                logger.info(f"Response text: {response.text}")
                
                # Try alternative login endpoints if main one fails
                alternative_endpoints = [
                    f"{BASE_URL}/auth/login",
                    f"{BASE_URL}/api/login",
                    f"{BASE_URL}/api/v1/auth/login",
                    f"{API_BASE_URL}/login"
                ]
                
                for endpoint in alternative_endpoints:
                    logger.info(f"Trying alternative endpoint: {endpoint}")
                    
                    # Try GET with query params
                    response = self.session.get(endpoint, params=login_params)
                    logger.info(f"GET {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if 'token' in response_data:
                                self.token = response_data['token']
                                self.session.headers["Authorization"] = f"Bearer {self.token}"
                                logger.info(f"Login successful at {endpoint}!")
                                return True
                        except:
                            pass
                    
                    # Try POST with JSON
                    response = self.session.post(endpoint, json=login_params)
                    logger.info(f"POST {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if 'token' in response_data:
                                self.token = response_data['token']
                                self.session.headers["Authorization"] = f"Bearer {self.token}"
                                logger.info(f"Login successful at {endpoint}!")
                                return True
                        except:
                            pass
                
                return self.try_direct_parsing()
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return self.try_direct_parsing()
    
    def try_direct_parsing(self):
        """
        Try to parse the documentation directly without login
        """
        logger.info("Attempting direct parsing of documentation...")
        
        try:
            # Use the actual URLs found on the website
            api_docs_urls = [
                f"{BASE_URL}/Android-panels",  # API 2.x.x
                f"{BASE_URL}/Android-panels-1.8.0",  # API 1.x.x
                f"{BASE_URL}/category/android-panels",  # API Specification 2.x.x
                f"{BASE_URL}/category/android-panels-1.8.0",  # API Specification 1.x.x
                f"{BASE_URL}/Camdroid-panels",  # Individual panels
                f"{BASE_URL}/category/camdroid-panels",  # Individual panels spec
                f"{BASE_URL}/category/android-monitors",  # Android monitors
                f"{BASE_URL}/category/camdroid-monitors"  # Linux monitors
            ]
            
            for url in api_docs_urls:
                logger.info(f"Trying URL: {url}")
                response = self.session.get(url)
                
                if response.status_code == 200:
                    logger.info(f"Successfully accessed {url}")
                    self.parse_documentation_page(response.text, url)
                    
                    # Try to find API endpoints in the page
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for links to specific API methods
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href')
                        if href and (href.startswith('/') and any(keyword in href.lower() for keyword in ['api', 'android', 'camdroid', 'auth', 'login', 'system', 'device', 'door', 'camera'])):
                            if not href.startswith('http'):
                                full_url = f"{BASE_URL}{href}"
                            else:
                                full_url = href
                            
                            logger.info(f"Found potential API link: {full_url}")
                            
                            try:
                                sub_response = self.session.get(full_url)
                                if sub_response.status_code == 200:
                                    self.parse_api_page(sub_response.text, full_url)
                                    time.sleep(0.5)  # Be nice to the server
                            except Exception as e:
                                logger.debug(f"Error accessing {full_url}: {str(e)}")
                else:
                    logger.info(f"Status {response.status_code} for {url}")
            
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
            r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s<>]+)',
            r'endpoint[:\s]+([/\w\-{}]+)',
            r'url[:\s]+([/\w\-{}]+)',
            r'path[:\s]+([/\w\-{}]+)',
            r'/api/[^\s<>"]+'
        ]
        
        text_content = soup.get_text()
        
        for pattern in api_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    method = match[0] if len(match) > 1 else 'GET'
                    endpoint = match[1] if len(match) > 1 else match[0]
                else:
                    method = 'GET'
                    endpoint = match
                
                if endpoint.startswith('/') and endpoint not in self.api_data:
                    self.api_data[endpoint] = {
                        'method': method,
                        'url': url,
                        'endpoint': endpoint,
                        'parameters': [],
                        'description': self.extract_endpoint_description(soup, endpoint)
                    }
                    logger.info(f"Found API endpoint: {method} {endpoint}")
        
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
    
    def parse_api_page(self, html_content, url):
        """
        Parse a specific API page
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract API method details
        title = soup.find('h1') or soup.find('h2')
        method_name = title.get_text().strip() if title else url.split('/')[-1]
        
        # Look for HTTP method and endpoint
        method = 'GET'
        endpoint = ''
        
        # Search for method indicators
        method_indicators = soup.find_all(string=re.compile(r'(GET|POST|PUT|DELETE|PATCH)', re.I))
        if method_indicators:
            method = method_indicators[0].strip().upper()
        
        # Search for endpoint patterns
        endpoint_patterns = [
            r'/api/[^\s<>"\']+',
            r'/[a-zA-Z][^\s<>"\']*'
        ]
        
        page_text = soup.get_text()
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                endpoint = matches[0]
                break
        
        # Extract parameters
        parameters = []
        param_sections = soup.find_all(['table', 'dl', 'ul'])
        for section in param_sections:
            if section.name == 'table':
                rows = section.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        param_name = cells[0].get_text().strip()
                        param_type = cells[1].get_text().strip() if len(cells) > 1 else ''
                        param_desc = cells[2].get_text().strip() if len(cells) > 2 else ''
                        param_required = cells[3].get_text().strip() if len(cells) > 3 else ''
                        
                        if param_name and not any(keyword in param_name.lower() for keyword in ['parameter', 'name', 'type']):
                            parameters.append({
                                'name': param_name,
                                'type': param_type,
                                'description': param_desc,
                                'required': param_required
                            })
        
        # Extract description
        description = ''
        desc_elements = soup.find_all('p')
        if desc_elements:
            description = desc_elements[0].get_text().strip()
        
        if method_name and (endpoint or method != 'GET'):
            key = endpoint if endpoint else method_name
            self.api_data[key] = {
                'name': method_name,
                'method': method,
                'endpoint': endpoint,
                'url': url,
                'parameters': parameters,
                'description': description
            }
            logger.info(f"Parsed API method: {method_name}")
    
    def extract_endpoint_description(self, soup, endpoint):
        """
        Try to extract description for an endpoint
        """
        # Simple heuristic to find description near the endpoint
        text = soup.get_text()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if endpoint in line:
                # Look at surrounding lines for description
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context_lines = lines[start:end]
                
                for context_line in context_lines:
                    clean_line = context_line.strip()
                    if clean_line and not any(char in clean_line for char in ['{', '}', '/', 'http']):
                        if len(clean_line) > 20:  # Likely a description
                            return clean_line
        
        return ''
    
    def get_android_panels_data(self):
        """
        Extract data specific to android-panels
        """
        logger.info("Searching for android-panels documentation...")
        
        if not self.token:
            logger.warning("No authentication token, trying without auth...")
        
        # Use the correct URLs found on the website
        android_endpoints = [
            f"{BASE_URL}/Android-panels",  # Main API Reference
            f"{BASE_URL}/Android-panels-1.8.0",  # Legacy API Reference
            f"{BASE_URL}/category/android-panels",  # API Specification
            f"{BASE_URL}/category/android-panels-1.8.0",  # Legacy API Specification
        ]
        
        for endpoint in android_endpoints:
            try:
                logger.info(f"Trying android endpoint: {endpoint}")
                response = self.session.get(endpoint)
                
                if response.status_code == 200:
                    logger.info(f"Successfully accessed {endpoint}")
                    self.parse_api_page(response.text, endpoint)
                    
                    # Also parse as documentation page to catch more patterns
                    self.parse_documentation_page(response.text, endpoint)
                else:
                    logger.info(f"Status {response.status_code} for {endpoint}")
                    
            except Exception as e:
                logger.error(f"Error accessing {endpoint}: {str(e)}")
        
        # Also try to login through the web interface
        self.try_web_auth()
        
    def try_web_auth(self):
        """
        Try to authenticate through the web interface
        """
        logger.info("Attempting web authentication...")
        
        try:
            auth_url = f"{BASE_URL}/auth"
            logger.info(f"Trying auth page: {auth_url}")
            
            response = self.session.get(auth_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for login form
                form = soup.find('form')
                if form:
                    logger.info("Found login form")
                    
                    # Extract form details
                    action = form.get('action', '/auth')
                    method = form.get('method', 'POST').upper()
                    
                    if not action.startswith('http'):
                        action = BASE_URL + action if action.startswith('/') else f"{BASE_URL}/{action}"
                    
                    # Find input fields
                    inputs = form.find_all('input')
                    form_data = {}
                    
                    for input_tag in inputs:
                        name = input_tag.get('name')
                        input_type = input_tag.get('type', 'text')
                        value = input_tag.get('value', '')
                        
                        if input_type == 'email' or name in ['email', 'username', 'login']:
                            form_data[name] = EMAIL
                        elif input_type == 'password' or name == 'password':
                            form_data[name] = PASSWORD
                        elif input_type == 'hidden':
                            form_data[name] = value
                        elif name:
                            form_data[name] = value
                    
                    logger.info(f"Submitting form to {action} with method {method}")
                    logger.info(f"Form data: {list(form_data.keys())}")
                    
                    if method == 'POST':
                        auth_response = self.session.post(action, data=form_data)
                    else:
                        auth_response = self.session.get(action, params=form_data)
                    
                    logger.info(f"Auth response status: {auth_response.status_code}")
                    
                    if auth_response.status_code == 200:
                        # Check if we're now authenticated
                        if 'login' not in auth_response.url.lower() and 'auth' not in auth_response.url.lower():
                            logger.info("Web authentication appears successful!")
                            return True
                    
        except Exception as e:
            logger.error(f"Web auth error: {str(e)}")
        
        return False
    
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
            md_lines.append("4. Check if authentication method has changed")
        else:
            for endpoint, data in self.api_data.items():
                md_lines.append(f"### {data.get('name', endpoint)}")
                if data.get('description'):
                    md_lines.append(data['description'])
                md_lines.append("")
                
                if data.get('method') and data.get('endpoint'):
                    md_lines.append(f"**Method:** `{data['method']} {data['endpoint']}`")
                    md_lines.append("")
                
                if data.get('parameters'):
                    md_lines.append("**Parameters:**")
                    md_lines.append("| Name | Type | Description | Required |")
                    md_lines.append("|------|------|-------------|----------|")
                    for param in data['parameters']:
                        md_lines.append(f"| {param.get('name', '')} | {param.get('type', '')} | {param.get('description', '')} | {param.get('required', '')} |")
                    md_lines.append("")
                
                md_lines.append("---")
                md_lines.append("")
        
        return "\n".join(md_lines)
    
    def run(self):
        """
        Main execution method
        """
        logger.info("Starting BAS-IP API documentation scraper...")
        
        # Try to login
        login_success = self.login()
        
        if login_success:
            logger.info("Authentication successful, proceeding with authenticated requests...")
        else:
            logger.warning("Authentication failed, proceeding with public access...")
        
        # Get android panels data
        self.get_android_panels_data()
        
        # Save data
        self.save_data()
        
        logger.info("Scraping completed!")
        return len(self.api_data) > 0

def main():
    scraper = BasIPScraper()
    success = scraper.run()
    
    if success:
        logger.info(f"Successfully scraped {len(scraper.api_data)} API methods")
    else:
        logger.warning("No API data was collected")

if __name__ == "__main__":
    main()
