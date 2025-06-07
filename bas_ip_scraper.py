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
from datetime import datetime

# Configuration
LOGIN_URL = "https://developers.bas-ip.com/api/auth/login"
BASE_URL = "https://developers.bas-ip.com"
API_URL = "https://developers.bas-ip.com/api"
OUTPUT_FILE = "bas_ip_android_panels.md"

# User credentials
EMAIL = "andrey.safar@gmail.com"
PASSWORD = "12345678"

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": BASE_URL
}

def login():
    """
    Log in to the BAS-IP developers portal and return the session with cookies
    """
    print("Logging in to BAS-IP developers portal...")
    session = requests.Session()
    
    # First, get the CSRF token
    response = session.get(BASE_URL, headers=HEADERS)
    
    # Prepare login data
    login_data = {
        "email": EMAIL,
        "password": PASSWORD
    }
    
    # Perform login
    response = session.post(
        LOGIN_URL,
        headers=HEADERS,
        json=login_data
    )
    
    if response.status_code == 200:
        print("Login successful!")
        return session
    else:
        print(f"Login failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

def get_android_panels_data(session):
    """
    Extract data from the android-panels section
    """
    print("Fetching android-panels data...")
    
    # Get the main documentation structure
    docs_response = session.get(f"{API_URL}/docs", headers=HEADERS)
    if docs_response.status_code != 200:
        print(f"Failed to fetch documentation structure: {docs_response.status_code}")
        sys.exit(1)
    
    docs_data = docs_response.json()
    
    # Find the android-panels section
    android_panels_section = None
    for section in docs_data:
        if "android-panels" in section.get("slug", "").lower():
            android_panels_section = section
            break
    
    if not android_panels_section:
        print("Could not find android-panels section in the documentation")
        # Try to get all sections as fallback
        return {"sections": docs_data, "error": "android-panels section not found specifically"}
    
    # Get detailed content for the android-panels section
    section_id = android_panels_section.get("id")
    section_response = session.get(f"{API_URL}/docs/{section_id}", headers=HEADERS)
    
    if section_response.status_code != 200:
        print(f"Failed to fetch android-panels section: {section_response.status_code}")
        return {"section": android_panels_section, "error": f"Failed to fetch details: {section_response.status_code}"}
    
    section_data = section_response.json()
    
    # Get all child pages
    pages = []
    for child_id in section_data.get("childrenIds", []):
        page_response = session.get(f"{API_URL}/docs/{child_id}", headers=HEADERS)
        if page_response.status_code == 200:
            pages.append(page_response.json())
        else:
            print(f"Failed to fetch page {child_id}: {page_response.status_code}")
    
    return {
        "section": section_data,
        "pages": pages
    }

def convert_to_markdown(data):
    """
    Convert the API data to markdown format
    """
    print("Converting data to markdown...")
    
    md_content = []
    
    # Add header
    md_content.append("# BAS-IP Android Panels API Documentation")
    md_content.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    md_content.append("")
    
    # Add project description
    md_content.append("## Project Description")
    md_content.append("This document contains API documentation for BAS-IP Android Panels, extracted from the BAS-IP developers portal.")
    md_content.append("The goal is to create an MCP-server that retrieves current data from this API and provides information to AI agents.")
    md_content.append("")
    
    # Check if we have section data
    if "error" in data:
        md_content.append("## Error")
        md_content.append(f"An error occurred while fetching data: {data['error']}")
        md_content.append("")
        
        if "sections" in data:
            md_content.append("## Available Sections")
            for section in data["sections"]:
                md_content.append(f"- {section.get('title', 'Unknown')}: {section.get('slug', 'No slug')}")
        
        return "\n".join(md_content)
    
    # Add section information
    section = data.get("section", {})
    md_content.append(f"## {section.get('title', 'Android Panels')}")
    
    if "description" in section and section["description"]:
        md_content.append(section["description"])
    md_content.append("")
    
    # Add table of contents
    md_content.append("## Table of Contents")
    for page in data.get("pages", []):
        md_content.append(f"- [{page.get('title', 'Unknown')}](#{page.get('slug', '').replace('/', '-')})")
    md_content.append("")
    
    # Add each page content
    for page in data.get("pages", []):
        page_title = page.get("title", "Unknown")
        page_slug = page.get("slug", "").replace("/", "-")
        
        md_content.append(f"## {page_title} <a name='{page_slug}'></a>")
        
        if "description" in page and page["description"]:
            md_content.append(page["description"])
        
        # Process content
        content = page.get("content", "")
        if content:
            # Convert HTML to markdown (simple version)
            # Remove HTML tags but keep the text
            content = re.sub(r'<[^>]*>', '', content)
            md_content.append(content)
        
        # Add code examples if available
        if "examples" in page and page["examples"]:
            md_content.append("### Examples")
            for example in page["examples"]:
                md_content.append(f"#### {example.get('title', 'Example')}")
                md_content.append("```" + example.get("language", ""))
                md_content.append(example.get("content", ""))
                md_content.append("```")
        
        md_content.append("")
    
    # Add implementation notes
    md_content.append("## Implementation Notes for MCP-Server")
    md_content.append("When implementing the MCP-server for BAS-IP Android Panels API, consider the following:")
    md_content.append("1. Authentication is required for all API endpoints")
    md_content.append("2. Regular polling may be necessary to keep data current")
    md_content.append("3. Consider implementing caching to reduce API calls")
    md_content.append("4. Error handling should account for network issues and API changes")
    md_content.append("5. Structure the data in a format that's easily consumable by AI agents")
    md_content.append("")
    
    return "\n".join(md_content)

def save_to_file(content, filename=OUTPUT_FILE):
    """
    Save the markdown content to a file
    """
    print(f"Saving content to {filename}...")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Content saved successfully to {filename}")

def main():
    """
    Main function to orchestrate the scraping process
    """
    print("Starting BAS-IP API documentation scraper...")
    
    try:
        # Login to the portal
        session = login()
        
        # Get android-panels data
        data = get_android_panels_data(session)
        
        # Convert to markdown
        md_content = convert_to_markdown(data)
        
        # Save to file
        save_to_file(md_content)
        
        print("Process completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
