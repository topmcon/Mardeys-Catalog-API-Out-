"""
Simple test script to verify connection to the Salesforce API.
"""
import os
import sys
from salesforce_connector import SalesforceConnector
import json

def test_connection():
    """Test the API connection with sample data"""
    print("=" * 60)
    print("SALESFORCE API CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Initialize connector
        print("\n1. Initializing connector...")
        connector = SalesforceConnector()
        print("   ✓ Connector initialized")
        
        # Test with sample model numbers
        print("\n2. Testing API with sample model numbers...")
        test_models = ["62558LF-PC", "PRO4850G"]
        print(f"   Model Numbers: {test_models}")
        
        result = connector.search_products_by_model_numbers(test_models)
        print("   ✓ API request successful")
        
        # Display results
        print("\n3. Response received:")
        print(f"   Response type: {type(result).__name__}")
        
        if isinstance(result, dict):
            print(f"   Keys: {list(result.keys())}")
            
            # Try to find products in response
            products = result.get('details', result.get('products', result.get('results', result.get('data', []))))
            if products:
                print(f"   Products found: {len(products)}")
                if products and isinstance(products, list) and len(products) > 0:
                    print(f"\n   First product sample:")
                    first_product = products[0]
                    if isinstance(first_product, dict):
                        for key, value in list(first_product.items())[:10]:
                            value_str = str(value)[:100]
                            print(f"     - {key}: {value_str}")
                        if len(first_product) > 10:
                            print(f"     ... and {len(first_product) - 10} more fields")
            else:
                print(f"   No products array found in response")
                
        elif isinstance(result, list):
            print(f"   Products in list: {len(result)}")
            if len(result) > 0 and isinstance(result[0], dict):
                print(f"\n   First product sample:")
                for key, value in list(result[0].items())[:10]:
                    value_str = str(value)[:100]
                    print(f"     - {key}: {value_str}")
        
        # Save full response for inspection
        output_file = 'api_test_response.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n   ✓ Full response saved to: {output_file}")
        
        print("\n" + "=" * 60)
        print("CONNECTION TEST PASSED ✓")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ CONNECTION TEST FAILED")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check that .env file exists and contains SF_API_BASE_URL")
        print("  2. Verify the API endpoint is accessible")
        print("  3. Check if authentication is required")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
