# Mardey's Catalog API - Salesforce Product Attribute Analysis

This project connects to Salesforce to extract, analyze, and generate a comprehensive static attribute table for your product catalog. It identifies common attributes across departments, categories, and styles by analyzing 20-30 products per group.

## Features

- **Salesforce Integration**: Secure connection to Salesforce API using `simple-salesforce`
- **Schema Discovery**: Automatically discovers available product objects and fields
- **Product Extraction**: Pulls all product catalog data with attributes
- **Hierarchical Organization**: Organizes products by department, category, and style
- **Attribute Analysis**: Analyzes 20-30 products per group to identify common attributes
- **Frequency Analysis**: Calculates how often each attribute appears (configurable threshold)
- **Multiple Output Formats**: Generates JSON, CSV, and Excel attribute tables
- **Global Attributes**: Identifies attributes that span multiple product groups

## Project Structure

```
Mardeys-Catalog-API-Out-/
├── config.py                  # Configuration settings
├── salesforce_connector.py    # Salesforce API connection
├── catalog_extractor.py       # Product data extraction
├── attribute_analyzer.py      # Attribute analysis engine
├── table_generator.py         # Output table generation
├── main.py                    # Main orchestration script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
└── output/                   # Generated output files
    ├── catalog_raw_data.json
    ├── analysis_report.json
    ├── attribute_table.json
    ├── attribute_table.csv
    └── attribute_table.xlsx
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Salesforce account with API access
- Salesforce Security Token

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Salesforce Credentials

Copy the example environment file and fill in your Salesforce credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SF_USERNAME=your_salesforce_username@example.com
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_security_token
SF_DOMAIN=login  # Use 'login' for production or 'test' for sandbox
SF_API_VERSION=58.0
```

#### Getting Your Salesforce Security Token

1. Log into Salesforce
2. Click your profile icon → Settings
3. In Quick Find, search for "Reset My Security Token"
4. Click "Reset Security Token"
5. Check your email for the new token

### 4. Configure Analysis Settings

Adjust analysis parameters in `.env`:

```env
SAMPLE_SIZE_PER_CATEGORY=30        # Products to analyze per group
MIN_ATTRIBUTE_FREQUENCY=0.5        # 50% minimum frequency
```

## Usage

### Basic Usage

Run the complete analysis pipeline:

```bash
python main.py
```

This will:
1. Connect to Salesforce
2. Discover available product objects and fields
3. Extract all products
4. Organize by department, category, and style
5. Analyze attributes (20-30 products per group)
6. Generate attribute tables in JSON, CSV, and Excel formats

### Customizing Field Mapping

After running schema discovery, update `main.py` to match your Salesforce schema:

```python
# In main.py, update these sections:

# Custom fields to extract
custom_fields = [
    'Category__c',
    'Style__c',
    'Color__c',
    'Size__c',
    'Material__c',
    'Brand__c',
    # Add your custom fields
]

# Hierarchy field mapping
catalog_data = extractor.organize_by_hierarchy(
    products,
    department_field='Family',      # Your department field
    category_field='Category__c',   # Your category field
    style_field='Style__c'          # Your style field
)
```

### Advanced Usage

#### Schema Discovery Only

```python
from catalog_extractor import CatalogExtractor

extractor = CatalogExtractor()
schema = extractor.discover_schema()

for obj_name, obj_info in schema.items():
    print(f"{obj_name}: {len(obj_info['fields'])} fields")
```

#### Custom SOQL Queries

```python
from salesforce_connector import SalesforceConnector

connector = SalesforceConnector()
results = connector.query_with_soql(
    "SELECT Id, Name, Category__c, Color__c FROM Product2 WHERE IsActive = TRUE"
)
```

#### Analyze Specific Groups

```python
from attribute_analyzer import AttributeAnalyzer

analyzer = AttributeAnalyzer(min_frequency=0.6)  # 60% threshold
results = analyzer.analyze_group('Electronics', products, 'category')
```

## Output Files

### 1. `attribute_table.json`
Complete attribute mapping for website integration:

```json
{
  "metadata": {
    "description": "Static attribute table for product catalog",
    "min_frequency": 0.5
  },
  "departments": {
    "Electronics": {
      "attributes": [
        {
          "name": "Brand__c",
          "display_name": "Brand",
          "type": "string",
          "frequency": 0.967,
          "required": true,
          "filterable": true
        }
      ]
    }
  },
  "global_attributes": [...]
}
```

### 2. `attribute_table.csv`
Flattened format for spreadsheet analysis:

```csv
group_type,group_name,attribute_name,display_name,type,frequency,required,filterable
department,Electronics,Brand__c,Brand,string,0.967,true,true
```

### 3. `attribute_table.xlsx`
Multi-sheet Excel workbook:
- **Global Attributes**: Attributes appearing across 30%+ of groups
- **Departments**: Department-specific attributes
- **Categories**: Category-specific attributes
- **Styles**: Style-specific attributes
- **Summary**: Overall statistics

### 4. `analysis_report.json`
Detailed analysis with frequency data, sample values, and statistics.

### 5. `catalog_raw_data.json`
Raw extracted product data organized by hierarchy.

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SF_USERNAME` | Salesforce username | Required |
| `SF_PASSWORD` | Salesforce password | Required |
| `SF_SECURITY_TOKEN` | Salesforce security token | Required |
| `SF_DOMAIN` | Salesforce domain (login/test) | `login` |
| `SF_API_VERSION` | Salesforce API version | `58.0` |
| `SAMPLE_SIZE_PER_CATEGORY` | Products to analyze per group | `30` |
| `MIN_ATTRIBUTE_FREQUENCY` | Minimum attribute frequency (0-1) | `0.5` |

### Attribute Frequency Threshold

Controls which attributes are considered "common":
- `0.5` (50%): Attribute appears in at least half of products
- `0.7` (70%): Attribute appears in 70%+ of products
- `0.9` (90%): Attribute appears in 90%+ of products (marked as required)

## Integration with Website

### Using the JSON Attribute Table

```javascript
// Load attribute table
const attributeTable = await fetch('output/attribute_table.json');
const attributes = await attributeTable.json();

// Get attributes for a department
const electronicsAttrs = attributes.departments.Electronics.attributes;

// Filter for required attributes
const requiredAttrs = electronicsAttrs.filter(attr => attr.required);

// Build dynamic form fields
electronicsAttrs.forEach(attr => {
  if (attr.filterable) {
    createFilterField(attr.display_name, attr.sample_values);
  }
});
```

### Example: Dynamic Product Filter

```javascript
function buildProductFilters(department) {
  const deptAttrs = attributes.departments[department].attributes;
  
  return deptAttrs
    .filter(attr => attr.filterable && attr.frequency > 0.7)
    .map(attr => ({
      id: attr.name,
      label: attr.display_name,
      type: attr.type,
      options: attr.sample_values.map(v => v.value)
    }));
}
```

## Troubleshooting

### Authentication Errors

**Error**: `INVALID_LOGIN: Invalid username, password, security token`

**Solution**: 
1. Verify credentials in `.env`
2. Reset your security token if needed
3. For sandbox, set `SF_DOMAIN=test`

### API Limit Errors

**Error**: `API_LIMITS_EXCEEDED`

**Solution**: Reduce the number of products queried or add pagination:

```python
products = connector.query_products(object_name='Product2', limit=1000)
```

### Missing Custom Fields

**Error**: Field names not matching

**Solution**: Run schema discovery first to identify actual field names:

```bash
python -c "from catalog_extractor import CatalogExtractor; e = CatalogExtractor(); print(e.discover_schema())"
```

## API Reference

### SalesforceConnector

```python
connector = SalesforceConnector()
connector.get_product_objects()              # Discover product objects
connector.describe_object('Product2')        # Get field information
connector.query_products(fields=[...])       # Query products
connector.query_with_soql("SELECT...")       # Custom SOQL
```

### CatalogExtractor

```python
extractor = CatalogExtractor()
extractor.discover_schema()                  # Discover schema
extractor.extract_all_products()             # Extract products
extractor.organize_by_hierarchy(...)         # Organize by groups
```

### AttributeAnalyzer

```python
analyzer = AttributeAnalyzer(min_frequency=0.5)
analyzer.analyze_group(name, products, type) # Analyze single group
analyzer.analyze_all_groups(catalog_data)    # Analyze all groups
```

### AttributeTableGenerator

```python
generator = AttributeTableGenerator(analysis_results)
generator.generate_comprehensive_table()     # Generate table
generator.save_as_json(path)                # Save as JSON
generator.save_as_csv(path)                 # Save as CSV
generator.save_as_excel(path)               # Save as Excel
```

## Best Practices

1. **Start with Schema Discovery**: Run the script once to see available fields
2. **Customize Field Mapping**: Update field names to match your Salesforce schema
3. **Adjust Frequency Threshold**: Lower for more attributes, higher for core attributes
4. **Sample Size**: 20-30 products gives good coverage without over-analyzing
5. **Regular Updates**: Re-run analysis when adding new product types
6. **Version Control**: Keep attribute tables in version control for tracking changes

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Salesforce API documentation
3. Open an issue on GitHub
