#!/usr/bin/env python3
"""
Test script for BAS-IP MCP Server

This script tests the functionality of the MCP server by simulating client requests.
"""

import asyncio
import json
from bas_ip_mcp_server import BasIPKnowledgeBase

async def test_knowledge_base():
    """Test the knowledge base functionality"""
    print("=== Testing BAS-IP Knowledge Base ===\n")
    
    # Create knowledge base instance
    kb = BasIPKnowledgeBase()
    
    # Test 1: Check if data loaded
    print(f"1. Loaded API methods: {len(kb.api_data)}")
    if kb.api_data:
        print("   ✓ Data loaded successfully")
    else:
        print("   ✗ No data loaded")
    print()
    
    # Test 2: List all methods
    print("2. Available API methods:")
    methods = kb.get_all_methods()
    for method in methods[:5]:  # Show first 5
        print(f"   - {method}")
    if len(methods) > 5:
        print(f"   ... and {len(methods) - 5} more")
    print()
    
    # Test 3: Search functionality
    print("3. Testing search functionality:")
    search_terms = ["door", "camera", "sip", "network"]
    for term in search_terms:
        results = kb.search_methods(term)
        print(f"   Search '{term}': Found {len(results)} results")
        if results:
            print(f"      First result: {results[0]['key']}")
    print()
    
    # Test 4: Get method details
    print("4. Testing method details:")
    if methods:
        test_method = methods[0]
        details = kb.get_method_details(test_method)
        print(f"   Method: {test_method}")
        print(f"   - Name: {details.get('name', 'N/A')}")
        print(f"   - Endpoint: {details.get('endpoint', 'N/A')}")
        print(f"   - Method: {details.get('method', 'N/A')}")
        print(f"   - Parameters: {len(details.get('parameters', []))}")
    print()
    
    # Test 5: Simulate MCP server responses
    print("5. Simulating MCP server responses:")
    
    # Search API methods
    print("\n   a) search_api_methods('door'):")
    results = kb.search_methods('door')
    if results:
        for result in results[:2]:
            data = result['data']
            print(f"      **{result['key']}**")
            if data.get('method') and data.get('endpoint'):
                print(f"        `{data['method']} {data['endpoint']}`")
            if data.get('description'):
                print(f"        {data['description']}")
    
    # Get API method details
    print("\n   b) get_api_method_details('openDoor'):")
    details = kb.get_method_details('openDoor')
    if details:
        print(f"      # {details.get('name', 'openDoor')}")
        if details.get('description'):
            print(f"      {details['description']}")
        if details.get('method') and details.get('endpoint'):
            print(f"      ## Endpoint")
            print(f"      ```")
            print(f"      {details['method']} {details['endpoint']}")
            print(f"      ```")
        if details.get('parameters'):
            print(f"      ## Parameters")
            print(f"      | Name | Type | Description | Required |")
            print(f"      |------|------|-------------|----------|")
            for param in details['parameters']:
                print(f"      | {param.get('name', '')} | {param.get('type', '')} | {param.get('description', '')} | {param.get('required', '')} |")
    
    # Knowledge base status
    print("\n   c) get_knowledge_base_status():")
    print(f"      - Total API Methods: {len(kb.api_data)}")
    if kb.last_update:
        print(f"      - Last Updated: {kb.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"      - Last Updated: Never")
    
    print("\n=== All tests completed ===")

async def main():
    """Main test function"""
    await test_knowledge_base()

if __name__ == "__main__":
    asyncio.run(main())