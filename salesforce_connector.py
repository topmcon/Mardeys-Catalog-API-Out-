"""
Salesforce connection and data extraction module.
"""
import requests
import json
from config import SalesforceConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalesforceConnector:
    """Handles connection and queries to Salesforce Apex REST API"""
    
    def __init__(self):
        """Initialize Salesforce API connection"""
        SalesforceConfig.validate()
        
        self.api_url = SalesforceConfig.get_full_url()
        self.session = requests.Session()
        
        # Set up headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add authentication if provided
        if SalesforceConfig.API_KEY:
            self.headers['Authorization'] = f'Bearer {SalesforceConfig.API_KEY}'
        
        logger.info(f"Salesforce API URL: {self.api_url}")
        logger.info("Successfully initialized Salesforce connector")
    
    def search_products_by_model_numbers(self, model_numbers):
        """
        Search products by model numbers using the ferguson-search API.
        
        Args:
            model_numbers: List of model numbers to search
        
        Returns:
            List of product records
        """
        try:
            payload = {'model_numbers': model_numbers}
            
            logger.info(f"Searching for {len(model_numbers)} model numbers")
            logger.debug(f"Payload: {payload}")
            
            response = self.session.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"API request successful, received response")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching products: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_all_products(self, batch_size=100):
        """
        Get all products by fetching in batches.
        Note: This requires knowing product model numbers or IDs in advance.
        
        Args:
            batch_size: Number of products to fetch per request
        
        Returns:
            List of all product records
        """
        logger.warning("get_all_products: This API requires model numbers. "
                      "Consider maintaining a list of model numbers or implementing pagination.")
        return []
    
    def query_products(self, model_numbers=None, limit=None):
        """
        Query products using the ferguson-search API.
        
        Args:
            model_numbers: List of model numbers to search. If None, returns empty list.
            limit: Maximum number of records to retrieve (applied after fetching)
        
        Returns:
            List of product records
        """
        if not model_numbers:
            logger.warning("No model numbers provided. Use search_products_by_model_numbers() "
                          "or provide a list of model numbers.")
            return []
        
        try:
            # Fetch products
            data = self.search_products_by_model_numbers(model_numbers)
            
            # Extract products from response
            products = []
            if isinstance(data, dict):
                # Handle different response structures
                products = data.get('details', data.get('products', data.get('results', data.get('data', [data]))))
            elif isinstance(data, list):
                products = data
            
            # Apply limit if specified
            if limit and len(products) > limit:
                products = products[:limit]
            
            logger.info(f"Retrieved {len(products)} product records")
            return products
            
        except Exception as e:
            logger.error(f"Error querying products: {str(e)}")
            raise
    
    def test_connection(self):
        """
        Test the API connection with sample model numbers.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test with sample model numbers
            test_models = ["62558LF-PC", "PRO4850G"]
            result = self.search_products_by_model_numbers(test_models)
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
