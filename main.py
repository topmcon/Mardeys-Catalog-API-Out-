"""
Main orchestration script for the Salesforce Catalog Analysis pipeline.
"""
import os
from pathlib import Path
import logging

from config import AnalysisConfig, SalesforceConfig
from salesforce_connector import SalesforceConnector
from catalog_extractor import CatalogExtractor
from attribute_analyzer import AttributeAnalyzer
from table_generator import AttributeTableGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_output_directory():
    """Create output directory if it doesn't exist"""
    output_dir = Path(AnalysisConfig.OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {output_dir.absolute()}")
    return output_dir


def main():
    """Main execution pipeline"""
    logger.info("=" * 80)
    logger.info("SALESFORCE CATALOG ANALYSIS PIPELINE")
    logger.info("=" * 80)
    
    try:
        # Setup
        output_dir = setup_output_directory()
        
        # Step 1: Test Connection and Discover Schema
        logger.info("\n--- STEP 1: CONNECTION TEST & SCHEMA DISCOVERY ---")
        extractor = CatalogExtractor()
        
        # Test connection
        if not extractor.connector.test_connection():
            logger.error("Failed to connect to Salesforce API. Check your configuration.")
            return
        
        # Discover schema with sample products
        schema = extractor.discover_schema(["62558LF-PC", "PRO4850G"])
        
        print("\nAPI Endpoint:", schema.get('api_endpoint'))
        print(f"Sample Products Analyzed: {schema.get('total_samples')}")
        print(f"\nAvailable Fields ({len(schema.get('fields', {}))} total):")
        for field_name, field_info in list(schema.get('fields', {}).items())[:20]:
            print(f"  - {field_name} ({field_info['type']})")
        if len(schema.get('fields', {})) > 20:
            print(f"  ... and {len(schema.get('fields', {})) - 20} more fields")
        
        # Step 2: Extract Products
        logger.info("\n--- STEP 2: PRODUCT EXTRACTION ---")
        
        print("\nNOTE: This API requires model numbers to search.")
        print("Options:")
        print("  1. Create 'model_numbers.txt' with one model number per line")
        print("  2. Or provide a list programmatically")
        
        # Check if model numbers file exists
        import os
        model_file = 'model_numbers.txt'
        
        if os.path.exists(model_file):
            products = extractor.extract_all_products(model_numbers_file=model_file)
        else:
            # Use sample model numbers for demo
            logger.info("No model_numbers.txt found. Using sample model numbers...")
            sample_models = ["62558LF-PC", "PRO4850G"]
            products = extractor.extract_products_by_model_numbers(sample_models)
        
        print(f"\nExtracted {len(products)} products")
        if products:
            print(f"Sample product fields: {list(products[0].keys()) if isinstance(products[0], dict) else 'N/A'}")
        
        # Step 3: Organize by Hierarchy
        logger.info("\n--- STEP 3: ORGANIZE BY HIERARCHY ---")
        
        # Auto-detect hierarchy fields from schema
        # Common field names to look for
        dept_candidates = ['department', 'family', 'category', 'productLine', 'product_line']
        cat_candidates = ['category', 'subcategory', 'type', 'productCategory', 'product_category']
        style_candidates = ['style', 'productStyle', 'product_style', 'subtype']
        
        # Find matching fields in the schema (case-insensitive)
        schema_fields = [f.lower() for f in schema.get('fields', {}).keys()]
        
        dept_field = next((f for c in dept_candidates for f in schema.get('fields', {}).keys() if c in f.lower()), None)
        cat_field = next((f for c in cat_candidates for f in schema.get('fields', {}).keys() if c in f.lower()), None)
        style_field = next((f for c in style_candidates for f in schema.get('fields', {}).keys() if c in f.lower()), None)
        
        print(f"\nDetected hierarchy fields:")
        print(f"  Department: {dept_field or 'Not found'}")
        print(f"  Category: {cat_field or 'Not found'}")
        print(f"  Style: {style_field or 'Not found'}")
        
        catalog_data = extractor.organize_by_hierarchy(
            products,
            department_field=dept_field,
            category_field=cat_field,
            style_field=style_field
        )
        
        # Save raw catalog data
        raw_data_path = output_dir / AnalysisConfig.RAW_DATA_FILE
        extractor.save_catalog_data(str(raw_data_path))
        
        print(f"\nOrganization Summary:")
        print(f"  Departments: {len(catalog_data['departments'])}")
        print(f"  Categories: {len(catalog_data['categories'])}")
        print(f"  Styles: {len(catalog_data['styles'])}")
        
        # Step 4: Analyze Attributes
        logger.info("\n--- STEP 4: ATTRIBUTE ANALYSIS ---")
        
        analyzer = AttributeAnalyzer(min_frequency=AnalysisConfig.MIN_ATTRIBUTE_FREQUENCY)
        analysis_results = analyzer.analyze_all_groups(
            catalog_data,
            sample_size=AnalysisConfig.SAMPLE_SIZE_PER_CATEGORY
        )
        
        # Save analysis report
        report_path = output_dir / AnalysisConfig.ANALYSIS_REPORT
        analyzer.save_analysis(str(report_path))
        
        print(f"\nAnalysis Summary:")
        summary = analysis_results['summary']
        print(f"  Departments Analyzed: {summary['total_departments']}")
        print(f"  Categories Analyzed: {summary['total_categories']}")
        print(f"  Styles Analyzed: {summary['total_styles']}")
        print(f"  Unique Attributes Found: {summary['unique_attributes']}")
        
        print(f"\n  Top 10 Most Common Attributes:")
        for item in summary['most_common_attributes'][:10]:
            print(f"    - {item['attribute']}: appears in {item['group_count']} groups")
        
        # Step 5: Generate Attribute Tables
        logger.info("\n--- STEP 5: GENERATE ATTRIBUTE TABLES ---")
        
        generator = AttributeTableGenerator(analysis_results)
        attribute_table = generator.generate_comprehensive_table()
        
        # Save in multiple formats
        json_path = output_dir / AnalysisConfig.ATTRIBUTE_TABLE_JSON
        csv_path = output_dir / AnalysisConfig.ATTRIBUTE_TABLE_CSV
        excel_path = output_dir / AnalysisConfig.ATTRIBUTE_TABLE_EXCEL
        
        generator.save_as_json(str(json_path))
        generator.save_as_csv(str(csv_path))
        generator.save_as_excel(str(excel_path))
        
        print(f"\n  Global Attributes (appear in 30%+ of groups):")
        for attr in attribute_table['global_attributes'][:15]:
            print(f"    - {attr['display_name']} ({attr['name']}): "
                  f"{attr['group_count']} groups, avg frequency {attr['avg_frequency']}")
        
        # Final Summary
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        print(f"\nOutput Files:")
        print(f"  Raw Data: {raw_data_path}")
        print(f"  Analysis Report: {report_path}")
        print(f"  Attribute Table (JSON): {json_path}")
        print(f"  Attribute Table (CSV): {csv_path}")
        print(f"  Attribute Table (Excel): {excel_path}")
        
        print(f"\nNext Steps:")
        print(f"  1. Review the attribute tables in the output/ directory")
        print(f"  2. Use attribute_table.json for your website integration")
        print(f"  3. Customize filtering and display logic based on the analysis")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
