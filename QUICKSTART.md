# Quick Start Guide

## First Time Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your Salesforce credentials
   ```

3. **Discover your schema** (first run):
   ```bash
   python main.py
   ```
   
   This will show you available fields in your Salesforce instance.

4. **Customize field mapping** in `main.py`:
   - Update `custom_fields` list with your custom Salesforce fields
   - Update `department_field`, `category_field`, `style_field` to match your schema

5. **Run full analysis**:
   ```bash
   python main.py
   ```

6. **Check output** in `output/` directory:
   - `attribute_table.json` - Use this for website integration
   - `attribute_table.xlsx` - Review in Excel
   - `attribute_table.csv` - For data analysis

## Common Salesforce Field Names

You may need to look for these types of fields in your Salesforce schema:

- **Department**: `Family`, `Department__c`, `ProductLine__c`
- **Category**: `Category__c`, `ProductCategory__c`, `Type`
- **Style**: `Style__c`, `ProductStyle__c`, `SubCategory__c`
- **Color**: `Color__c`, `Colour__c`
- **Size**: `Size__c`, `Dimensions__c`
- **Material**: `Material__c`, `Fabric__c`
- **Brand**: `Brand__c`, `Manufacturer__c`

Custom fields in Salesforce typically end with `__c`.

## Example Workflow

```bash
# 1. First run - discover schema
python main.py

# Output shows:
# Available Product Objects:
#   - Product2: 45 fields
# Sample product fields: ['Id', 'Name', 'Family', 'ProductCode', ...]

# 2. Edit main.py to add your custom fields
# custom_fields = ['Category__c', 'Style__c', 'Color__c']

# 3. Run again with custom fields
python main.py

# 4. Review output files
ls -la output/

# 5. Use attribute_table.json in your website
```

## Adjusting Analysis Parameters

In `.env`:

```env
# Analyze more products per group for better accuracy
SAMPLE_SIZE_PER_CATEGORY=50

# Only include attributes that appear in 70%+ of products
MIN_ATTRIBUTE_FREQUENCY=0.7
```

## Troubleshooting

**No products found?**
- Check that `IsActive = TRUE` filter is appropriate for your data
- Verify field names match your Salesforce schema

**Authentication failed?**
- Verify username, password, and security token
- For sandbox: set `SF_DOMAIN=test`

**Missing attributes?**
- Lower `MIN_ATTRIBUTE_FREQUENCY` to see more attributes
- Check that custom fields are spelled correctly

## Next Steps

After generating the attribute table:
1. Review `attribute_table.xlsx` in Excel
2. Identify which attributes to display on your website
3. Use `attribute_table.json` to build dynamic filters
4. Implement product attribute display using the type information
