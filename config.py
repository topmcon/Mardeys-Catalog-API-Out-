"""
Configuration module for Salesforce connection and analysis settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SalesforceConfig:
    """Salesforce API connection configuration"""
    API_BASE_URL = os.getenv('SF_API_BASE_URL', 'https://data-nosoftware-2565.my.salesforce-sites.com')
    API_ENDPOINT = os.getenv('SF_API_ENDPOINT', '/services/apexrest/ferguson-search')
    API_KEY = os.getenv('SF_API_KEY')  # Optional
    USERNAME = os.getenv('SF_USERNAME')  # Optional
    PASSWORD = os.getenv('SF_PASSWORD')  # Optional
    
    @classmethod
    def get_full_url(cls):
        """Get the complete API URL"""
        return f"{cls.API_BASE_URL.rstrip('/')}{cls.API_ENDPOINT}"
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        if not cls.API_BASE_URL:
            raise ValueError("Missing required environment variable: SF_API_BASE_URL")
        if not cls.API_ENDPOINT:
            raise ValueError("Missing required environment variable: SF_API_ENDPOINT")
        
        return True


class AnalysisConfig:
    """Analysis configuration"""
    SAMPLE_SIZE_PER_CATEGORY = int(os.getenv('SAMPLE_SIZE_PER_CATEGORY', 30))
    MIN_ATTRIBUTE_FREQUENCY = float(os.getenv('MIN_ATTRIBUTE_FREQUENCY', 0.5))
    
    # Output file paths
    OUTPUT_DIR = 'output'
    RAW_DATA_FILE = 'catalog_raw_data.json'
    ATTRIBUTE_TABLE_JSON = 'attribute_table.json'
    ATTRIBUTE_TABLE_CSV = 'attribute_table.csv'
    ATTRIBUTE_TABLE_EXCEL = 'attribute_table.xlsx'
    ANALYSIS_REPORT = 'analysis_report.json'
