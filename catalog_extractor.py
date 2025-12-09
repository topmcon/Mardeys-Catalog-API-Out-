"""
Catalog data extraction and organization module.
"""
from salesforce_connector import SalesforceConnector
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)


class CatalogExtractor:
    """Extracts and organizes catalog data from Salesforce"""
    
    def __init__(self):
        """Initialize with Salesforce connector"""
        self.connector = SalesforceConnector()
        self.catalog_data = {
            'departments': {},
            'categories': {},
            'styles': {},
            'products': []
        }
    
    def discover_schema(self, sample_model_numbers=None):
        """
        Discover the product data schema by fetching sample products.
        
        Args:
            sample_model_numbers: List of model numbers to use as samples
        
        Returns:
            Information about available fields in product data
        """
        logger.info("Discovering product schema from API...")
        
        # Use provided samples or defaults
        if not sample_model_numbers:
            sample_model_numbers = ["62558LF-PC", "PRO4850G"]
        
        try:
            # Fetch sample products
            data = self.connector.search_products_by_model_numbers(sample_model_numbers)
            
            # Extract products
            products = []
            if isinstance(data, dict):
                products = data.get('details', data.get('products', data.get('results', data.get('data', [data]))))
            elif isinstance(data, list):
                products = data
            
            # Analyze schema from sample products
            schema_info = {
                'api_endpoint': 'ferguson-search',
                'total_samples': len(products),
                'fields': {}
            }
            
            # Collect all unique fields
            for product in products:
                if isinstance(product, dict):
                    for field_name, field_value in product.items():
                        if field_name not in schema_info['fields']:
                            schema_info['fields'][field_name] = {
                                'name': field_name,
                                'type': type(field_value).__name__,
                                'sample_value': str(field_value)[:100]  # First 100 chars
                            }
            
            logger.info(f"Discovered {len(schema_info['fields'])} fields from {len(products)} sample products")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error discovering schema: {str(e)}")
            raise
    
    def extract_products_by_model_numbers(self, model_numbers):
        """
        Extract products by their model numbers.
        
        Args:
            model_numbers: List of model numbers to extract
        
        Returns:
            List of product records with all attributes
        """
        logger.info(f"Extracting {len(model_numbers)} products by model number...")
        
        # Query products
        data = self.connector.search_products_by_model_numbers(model_numbers)
        
        # Extract products from response
        products = []
        if isinstance(data, dict):
            products = data.get('details', data.get('products', data.get('results', data.get('data', [data]))))
        elif isinstance(data, list):
            products = data
        
        self.catalog_data['products'] = products
        logger.info(f"Extracted {len(products)} products")
        
        return products
    
    def extract_all_products(self, model_numbers_file=None):
        """
        Extract all products. Requires a file with model numbers.
        
        Args:
            model_numbers_file: Path to file containing model numbers (one per line)
        
        Returns:
            List of product records with all attributes
        """
        if not model_numbers_file:
            logger.error("This API requires model numbers. Please provide model_numbers_file parameter.")
            logger.info("Create a file with one model number per line, then call extract_all_products('model_numbers.txt')")
            return []
        
        logger.info(f"Loading model numbers from {model_numbers_file}...")
        
        try:
            with open(model_numbers_file, 'r') as f:
                model_numbers = [line.strip() for line in f if line.strip()]
            
            logger.info(f"Loaded {len(model_numbers)} model numbers")
            return self.extract_products_by_model_numbers(model_numbers)
            
        except FileNotFoundError:
            logger.error(f"File not found: {model_numbers_file}")
            return []
        except Exception as e:
            logger.error(f"Error loading model numbers: {str(e)}")
            return []
    
    def organize_by_hierarchy(self, products, department_field='Family', 
                             category_field=None, style_field=None):
        """
        Organize products by department, category, and style.
        
        Args:
            products: List of product records
            department_field: Field name for department
            category_field: Field name for category
            style_field: Field name for style
        
        Returns:
            Organized catalog structure
        """
        logger.info("Organizing products by hierarchy...")
        
        departments = defaultdict(list)
        categories = defaultdict(list)
        styles = defaultdict(list)
        
        for product in products:
            # Organize by department
            dept = product.get(department_field, 'Uncategorized')
            if dept:
                departments[dept].append(product)
            
            # Organize by category if field provided
            if category_field:
                cat = product.get(category_field, 'Uncategorized')
                if cat:
                    categories[cat].append(product)
            
            # Organize by style if field provided
            if style_field:
                style = product.get(style_field, 'Uncategorized')
                if style:
                    styles[style].append(product)
        
        self.catalog_data['departments'] = dict(departments)
        self.catalog_data['categories'] = dict(categories)
        self.catalog_data['styles'] = dict(styles)
        
        logger.info(f"Found {len(departments)} departments, "
                   f"{len(categories)} categories, {len(styles)} styles")
        
        return self.catalog_data
    
    def extract_product_attributes(self, product):
        """
        Extract all non-null attributes from a product record.
        
        Args:
            product: Product record dictionary
        
        Returns:
            Dictionary of attribute names and values
        """
        # Exclude system fields
        system_fields = {'Id', 'IsDeleted', 'CreatedDate', 'CreatedById', 
                        'LastModifiedDate', 'LastModifiedById', 'SystemModstamp',
                        'IsArchived', 'IsActive'}
        
        attributes = {}
        for field, value in product.items():
            if field not in system_fields and value is not None:
                attributes[field] = value
        
        return attributes
    
    def get_sample_products(self, group_key, products, sample_size=30):
        """
        Get a sample of products from a group.
        
        Args:
            group_key: Name of the group (department, category, or style)
            products: List of products in the group
            sample_size: Number of products to sample
        
        Returns:
            Sample of products (up to sample_size)
        """
        return products[:sample_size]
    
    def save_catalog_data(self, filepath):
        """Save extracted catalog data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.catalog_data, f, indent=2, default=str)
            logger.info(f"Catalog data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving catalog data: {str(e)}")
            raise
    
    def load_catalog_data(self, filepath):
        """Load catalog data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.catalog_data = json.load(f)
            logger.info(f"Catalog data loaded from {filepath}")
            return self.catalog_data
        except Exception as e:
            logger.error(f"Error loading catalog data: {str(e)}")
            raise
