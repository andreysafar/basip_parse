#!/usr/bin/env python3
"""
BAS-IP MCP Server

MCP (Model Context Protocol) server for BAS-IP Android Panels API documentation.
This server provides API information to AI agents and can update its knowledge base.
"""

import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
from pydantic import BaseModel, Field
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Import our scrapers
from bas_ip_scraper import BasIPScraper
from bas_ip_selenium_scraper import SeleniumBasIPScraper

# Configuration
API_DATA_FILE = "bas_ip_api_data.json"
MARKDOWN_FILE = "bas_ip_android_panels.md"
UPDATE_INTERVAL_HOURS = 24  # Auto-update every 24 hours

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasIPKnowledgeBase:
    """Knowledge base for BAS-IP API documentation"""
    
    def __init__(self):
        self.api_data = {}
        self.last_update = None
        self.load_data()
    
    def load_data(self):
        """Load API data from JSON file"""
        try:
            if os.path.exists(API_DATA_FILE):
                with open(API_DATA_FILE, 'r', encoding='utf-8') as f:
                    self.api_data = json.load(f)
                self.last_update = datetime.fromtimestamp(os.path.getmtime(API_DATA_FILE))
                logger.info(f"Loaded {len(self.api_data)} API methods from {API_DATA_FILE}")
            else:
                logger.warning(f"{API_DATA_FILE} not found. Knowledge base is empty.")
        except Exception as e:
            logger.error(f"Error loading API data: {str(e)}")
    
    def search_methods(self, query: str) -> List[Dict[str, Any]]:
        """Search for API methods matching the query"""
        query_lower = query.lower()
        results = []
        
        for key, data in self.api_data.items():
            # Search in method name, endpoint, and description
            if (query_lower in key.lower() or 
                query_lower in data.get('endpoint', '').lower() or
                query_lower in data.get('description', '').lower() or
                query_lower in data.get('name', '').lower()):
                results.append({
                    'key': key,
                    'data': data
                })
        
        return results
    
    def get_method_details(self, method_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific API method"""
        return self.api_data.get(method_name)
    
    def get_all_methods(self) -> List[str]:
        """Get list of all available API methods"""
        return list(self.api_data.keys())
    
    def update_knowledge(self) -> bool:
        """Update knowledge base by running the scraper"""
        try:
            logger.info("Starting knowledge base update...")
            
            # Try Selenium scraper first for more detailed data
            try:
                scraper = SeleniumBasIPScraper(headless=True)
                if scraper.run():
                    self.load_data()
                    logger.info("Knowledge base updated successfully with Selenium scraper")
                    return True
            except Exception as e:
                logger.warning(f"Selenium scraper failed: {str(e)}")
            
            # Fall back to regular scraper
            scraper = BasIPScraper()
            if scraper.run():
                self.load_data()
                logger.info("Knowledge base updated successfully with regular scraper")
                return True
            
            logger.error("Failed to update knowledge base")
            return False
            
        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            return False

class BasIPMCPServer:
    """MCP Server for BAS-IP API documentation"""
    
    def __init__(self):
        self.server = Server("bas-ip-mcp-server")
        self.knowledge_base = BasIPKnowledgeBase()
        self.scheduler = AsyncIOScheduler()
        self.setup_tools()
        self.setup_resources()
        self.setup_scheduler()
    
    def setup_tools(self):
        """Set up available tools for the MCP server"""
        
        @self.server.tool()
        async def search_api_methods(query: str = Field(description="Search query for API methods")) -> str:
            """Search for BAS-IP API methods by keyword"""
            results = self.knowledge_base.search_methods(query)
            
            if not results:
                return f"No API methods found matching '{query}'"
            
            response = f"Found {len(results)} API methods matching '{query}':\n\n"
            for result in results[:10]:  # Limit to first 10 results
                data = result['data']
                response += f"**{result['key']}**\n"
                if data.get('method') and data.get('endpoint'):
                    response += f"  `{data['method']} {data['endpoint']}`\n"
                if data.get('description'):
                    response += f"  {data['description']}\n"
                response += "\n"
            
            if len(results) > 10:
                response += f"\n... and {len(results) - 10} more results"
            
            return response
        
        @self.server.tool()
        async def get_api_method_details(method_name: str = Field(description="Name or endpoint of the API method")) -> str:
            """Get detailed information about a specific BAS-IP API method"""
            details = self.knowledge_base.get_method_details(method_name)
            
            if not details:
                # Try searching for it
                results = self.knowledge_base.search_methods(method_name)
                if results:
                    details = results[0]['data']
                    method_name = results[0]['key']
                else:
                    return f"API method '{method_name}' not found in the knowledge base"
            
            response = f"# {method_name}\n\n"
            
            if details.get('description'):
                response += f"{details['description']}\n\n"
            
            if details.get('method') and details.get('endpoint'):
                response += "## Endpoint\n```\n"
                response += f"{details['method']} {details['endpoint']}\n"
                response += "```\n\n"
            
            if details.get('parameters'):
                response += "## Parameters\n"
                response += "| Name | Type | Description | Required |\n"
                response += "|------|------|-------------|----------|\n"
                for param in details['parameters']:
                    response += f"| {param.get('name', '')} | {param.get('type', '')} | {param.get('description', '')} | {param.get('required', '')} |\n"
                response += "\n"
            
            if details.get('example'):
                response += "## Example\n```json\n"
                response += details['example']
                response += "\n```\n\n"
            
            if details.get('response'):
                response += f"## Response\n{details['response']}\n\n"
            
            return response
        
        @self.server.tool()
        async def list_all_api_methods() -> str:
            """List all available BAS-IP API methods"""
            methods = self.knowledge_base.get_all_methods()
            
            if not methods:
                return "No API methods available in the knowledge base. Try updating the knowledge base."
            
            response = f"## Available BAS-IP API Methods ({len(methods)} total)\n\n"
            
            # Group by endpoint prefix if possible
            grouped = {}
            for method in methods:
                data = self.knowledge_base.get_method_details(method)
                if data and data.get('endpoint'):
                    prefix = data['endpoint'].split('/')[1] if '/' in data['endpoint'] else 'other'
                else:
                    prefix = 'other'
                
                if prefix not in grouped:
                    grouped[prefix] = []
                grouped[prefix].append(method)
            
            for prefix, method_list in sorted(grouped.items()):
                response += f"\n### {prefix.upper()}\n"
                for method in sorted(method_list):
                    response += f"- {method}\n"
            
            return response
        
        @self.server.tool()
        async def update_knowledge_base() -> str:
            """Update the BAS-IP API knowledge base by fetching latest documentation"""
            success = self.knowledge_base.update_knowledge()
            
            if success:
                return f"Knowledge base updated successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                return "Failed to update knowledge base. Check logs for details."
        
        @self.server.tool()
        async def get_knowledge_base_status() -> str:
            """Get the current status of the BAS-IP knowledge base"""
            num_methods = len(self.knowledge_base.api_data)
            
            status = f"## BAS-IP Knowledge Base Status\n\n"
            status += f"- **Total API Methods**: {num_methods}\n"
            
            if self.knowledge_base.last_update:
                status += f"- **Last Updated**: {self.knowledge_base.last_update.strftime('%Y-%m-%d %H:%M:%S')}\n"
                age = datetime.now() - self.knowledge_base.last_update
                status += f"- **Age**: {age.days} days, {age.seconds // 3600} hours\n"
            else:
                status += "- **Last Updated**: Never\n"
            
            status += f"- **Auto-update Interval**: Every {UPDATE_INTERVAL_HOURS} hours\n"
            
            # Show some statistics
            if num_methods > 0:
                methods_with_params = sum(1 for m in self.knowledge_base.api_data.values() if m.get('parameters'))
                methods_with_examples = sum(1 for m in self.knowledge_base.api_data.values() if m.get('example'))
                
                status += f"\n### Statistics\n"
                status += f"- Methods with parameters: {methods_with_params}\n"
                status += f"- Methods with examples: {methods_with_examples}\n"
            
            return status
    
    def setup_resources(self):
        """Set up available resources"""
        
        @self.server.resource("knowledge-base")
        async def get_knowledge_base() -> Resource:
            """Get the entire BAS-IP API knowledge base as a resource"""
            return Resource(
                uri="bas-ip://knowledge-base",
                name="BAS-IP API Knowledge Base",
                description="Complete BAS-IP Android Panels API documentation",
                mimeType="application/json",
                text=json.dumps(self.knowledge_base.api_data, indent=2)
            )
        
        @self.server.resource("markdown-docs")
        async def get_markdown_docs() -> Resource:
            """Get the markdown version of the documentation"""
            try:
                with open(MARKDOWN_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                content = "Markdown documentation not available"
            
            return Resource(
                uri="bas-ip://markdown-docs",
                name="BAS-IP API Markdown Documentation",
                description="Markdown formatted BAS-IP API documentation",
                mimeType="text/markdown",
                text=content
            )
    
    def setup_scheduler(self):
        """Set up the scheduler for automatic updates"""
        # Schedule automatic updates
        self.scheduler.add_job(
            self.knowledge_base.update_knowledge,
            'interval',
            hours=UPDATE_INTERVAL_HOURS,
            id='auto_update',
            name='Auto-update BAS-IP knowledge base'
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started. Auto-update every {UPDATE_INTERVAL_HOURS} hours.")
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting BAS-IP MCP Server...")
        
        # Initial knowledge base check
        if not self.knowledge_base.api_data:
            logger.info("Knowledge base is empty. Attempting initial update...")
            self.knowledge_base.update_knowledge()
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)

async def main():
    """Main entry point"""
    server = BasIPMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())