# Salesforce Ferguson-Search API Integration

Quick setup guide for connecting to the custom Salesforce API endpoint.

## API Endpoint

```
POST https://data-nosoftware-2565.my.salesforce-sites.com/services/apexrest/ferguson-search
Content-Type: application/json

{
    "model_numbers": ["62558LF-PC", "PRO4850G"]
}
```

## Quick Setup

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   
   The `.env` file should contain:
   ```env
   SF_API_BASE_URL=https://data-nosoftware-2565.my.salesforce-sites.com
   SF_API_ENDPOINT=/services/apexrest/ferguson-search
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test connection:**
   ```bash
   python test_connection.py
   ```
   
   This will test the API with sample model numbers and show you the response structure.

4. **Prepare model numbers:**
   
   Create `model_numbers.txt` with your product model numbers (one per line):
   ```
   62558LF-PC
   PRO4850G
   MODEL-123
   MODEL-456
   ```

5. **Run full analysis:**
   ```bash
   python main.py
   ```

## How It Works

This API differs from standard Salesforce APIs:

- **Model-based search**: Requires model numbers to fetch products
- **REST API**: Uses standard HTTP POST requests (not SOQL)
- **Custom endpoint**: Uses Apex REST custom endpoint

### Workflow

1. **Schema Discovery**: Fetches sample products to discover available fields
2. **Product Extraction**: Searches for products by model numbers
3. **Organization**: Groups products by department, category, style
4. **Analysis**: Analyzes 20-30 products per group to find common attributes
5. **Output**: Generates attribute tables in JSON, CSV, and Excel

## API Methods

### SalesforceConnector

```python
from salesforce_connector import SalesforceConnector

connector = SalesforceConnector()

# Search by model numbers
products = connector.search_products_by_model_numbers(["62558LF-PC", "PRO4850G"])

# Test connection
connector.test_connection()
```

### CatalogExtractor

```python
from catalog_extractor import CatalogExtractor

extractor = CatalogExtractor()

# Discover schema
schema = extractor.discover_schema(["62558LF-PC", "PRO4850G"])

# Extract specific products
products = extractor.extract_products_by_model_numbers(["MODEL-1", "MODEL-2"])

# Extract from file
products = extractor.extract_all_products(model_numbers_file='model_numbers.txt')
```

## Troubleshooting

### Connection Issues

If `test_connection.py` fails:

1. **Check URL**: Verify the API base URL is correct
2. **Check endpoint**: Verify the endpoint path is `/services/apexrest/ferguson-search`
3. **Network**: Ensure you can reach `data-nosoftware-2565.my.salesforce-sites.com`
4. **Authentication**: Check if the endpoint requires authentication (API key, cookies, etc.)

### Authentication

If the API requires authentication, update `.env`:

```env
# If API key required
SF_API_KEY=your_api_key_here

# If username/password required
SF_USERNAME=your_username
SF_PASSWORD=your_password
```

### No Products Found

The API requires exact model numbers. Make sure:
- Model numbers are spelled correctly
- Model numbers exist in the Salesforce database
- Model numbers are active/available

### Response Format

Run `test_connection.py` to see the actual response structure. The script saves the full response to `api_test_response.json` for inspection.

## Next Steps

1. Run `test_connection.py` to verify connectivity
2. Create `model_numbers.txt` with your actual product model numbers
3. Run `main.py` to perform full catalog analysis
4. Review output files in `output/` directory
5. Use `attribute_table.json` for website integration

## Differences from Standard Salesforce

| Standard Salesforce API | Ferguson-Search API |
|------------------------|---------------------|
| SOQL queries | Model number search |
| OAuth authentication | Public/custom auth |
| Object-based (Product2, etc.) | Custom response format |
| Field-level access control | Full product data |

This custom API is optimized for searching products by model number rather than querying all objects.
