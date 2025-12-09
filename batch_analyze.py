"""
Batch processing script for analyzing large numbers of products.
Handles API rate limits by processing in batches.
"""
import os
import time
import json
from pathlib import Path
import logging

from config import AnalysisConfig
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


def batch_extract_products(model_numbers, batch_size=50, delay=2):
    """
    Extract products in batches to avoid API limits.
    
    Args:
        model_numbers: List of model numbers
        batch_size: Number of models per batch
        delay: Delay between batches in seconds
    
    Returns:
        List of all extracted products
    """
    connector = SalesforceConnector()
    all_products = []
    
    total_batches = (len(model_numbers) + batch_size - 1) // batch_size
    
    for i in range(0, len(model_numbers), batch_size):
        batch = model_numbers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} models)")
        
        try:
            data = connector.search_products_by_model_numbers(batch)
            
            # Extract products from response
            products = []
            if isinstance(data, dict):
                products = data.get('details', data.get('products', data.get('results', data.get('data', []))))
            elif isinstance(data, list):
                products = data
            
            logger.info(f"  Retrieved {len(products)} products from batch")
            all_products.extend(products)
            
            # Delay between batches to respect rate limits
            if i + batch_size < len(model_numbers):
                logger.info(f"  Waiting {delay} seconds before next batch...")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"Error processing batch {batch_num}: {str(e)}")
            logger.warning(f"Skipping batch {batch_num} and continuing...")
            continue
    
    logger.info(f"Total products extracted: {len(all_products)}")
    return all_products


def main():
    """Main batch processing pipeline"""
    logger.info("=" * 80)
    logger.info("SALESFORCE CATALOG ANALYSIS - BATCH PROCESSING")
    logger.info("=" * 80)
    
    try:
        # Setup
        output_dir = Path(AnalysisConfig.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        
        # Load model numbers
        model_file = 'model_numbers.txt'
        logger.info(f"\nLoading model numbers from {model_file}...")
        
        with open(model_file, 'r') as f:
            model_numbers = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(model_numbers)} model numbers")
        
        # Extract products in batches
        logger.info("\n--- BATCH EXTRACTION ---")
        print(f"\nExtracting {len(model_numbers)} products in batches of 50...")
        print("This may take several minutes...")
        
        products = batch_extract_products(model_numbers, batch_size=50, delay=2)
        
        if not products:
            logger.error("No products were extracted. Check API connectivity and model numbers.")
            return
        
        print(f"\n✓ Successfully extracted {len(products)} products")
        
        # Save raw products
        raw_path = output_dir / 'products_raw.json'
        with open(raw_path, 'w') as f:
            json.dump(products, f, indent=2, default=str)
        logger.info(f"Raw products saved to {raw_path}")
        
        # Organize by hierarchy
        logger.info("\n--- ORGANIZING BY HIERARCHY ---")
        extractor = CatalogExtractor()
        
        # Auto-detect hierarchy fields from first product
        if products and isinstance(products[0], dict):
            fields = list(products[0].keys())
            print(f"\nSample product fields: {fields[:10]}...")
            
            # Detect hierarchy fields
            dept_candidates = ['business_category', 'department', 'family', 'category']
            cat_candidates = ['base_category', 'categories', 'subcategory', 'type']
            style_candidates = ['product_type', 'style', 'base_type']
            
            dept_field = next((f for c in dept_candidates for f in fields if c in f.lower()), None)
            cat_field = next((f for c in cat_candidates for f in fields if c in f.lower() and f != dept_field), None)
            style_field = next((f for c in style_candidates for f in fields if c in f.lower()), None)
            
            print(f"\nDetected hierarchy fields:")
            print(f"  Department: {dept_field or 'Not found'}")
            print(f"  Category: {cat_field or 'Not found'}")
            print(f"  Style: {style_field or 'Not found'}")
        else:
            dept_field = cat_field = style_field = None
        
        catalog_data = extractor.organize_by_hierarchy(
            products,
            department_field=dept_field,
            category_field=cat_field,
            style_field=style_field
        )
        
        catalog_path = output_dir / AnalysisConfig.RAW_DATA_FILE
        extractor.save_catalog_data(str(catalog_path))
        
        print(f"\nOrganization Summary:")
        print(f"  Departments: {len(catalog_data['departments'])}")
        print(f"  Categories: {len(catalog_data['categories'])}")
        print(f"  Styles: {len(catalog_data['styles'])}")
        
        # Display department breakdown
        if catalog_data['departments']:
            print(f"\nDepartments found:")
            for dept, dept_products in sorted(catalog_data['departments'].items(), key=lambda x: len(x[1]), reverse=True):
                print(f"  - {dept}: {len(dept_products)} products")
        
        # Analyze attributes
        logger.info("\n--- ATTRIBUTE ANALYSIS ---")
        
        analyzer = AttributeAnalyzer(min_frequency=AnalysisConfig.MIN_ATTRIBUTE_FREQUENCY)
        analysis_results = analyzer.analyze_all_groups(
            catalog_data,
            sample_size=AnalysisConfig.SAMPLE_SIZE_PER_CATEGORY
        )
        
        report_path = output_dir / AnalysisConfig.ANALYSIS_REPORT
        analyzer.save_analysis(str(report_path))
        
        print(f"\nAnalysis Summary:")
        summary = analysis_results['summary']
        print(f"  Departments Analyzed: {summary['total_departments']}")
        print(f"  Categories Analyzed: {summary['total_categories']}")
        print(f"  Styles Analyzed: {summary['total_styles']}")
        print(f"  Unique Attributes Found: {summary['unique_attributes']}")
        
        print(f"\n  Top 20 Most Common Attributes:")
        for item in summary['most_common_attributes'][:20]:
            print(f"    - {item['attribute']}: appears in {item['group_count']} groups")
        
        # Generate attribute tables
        logger.info("\n--- GENERATING ATTRIBUTE TABLES ---")
        
        generator = AttributeTableGenerator(analysis_results)
        attribute_table = generator.generate_comprehensive_table()
        
        json_path = output_dir / AnalysisConfig.ATTRIBUTE_TABLE_JSON
        csv_path = output_dir / AnalysisConfig.ATTRIBUTE_TABLE_CSV
        excel_path = output_dir / AnalysisConfig.ATTRIBUTE_TABLE_EXCEL
        
        generator.save_as_json(str(json_path))
        generator.save_as_csv(str(csv_path))
        generator.save_as_excel(str(excel_path))
        
        print(f"\n  Global Attributes (appear in 30%+ of groups):")
        for attr in attribute_table['global_attributes'][:20]:
            print(f"    - {attr['display_name']} ({attr['name']}): "
                  f"{attr['group_count']} groups, avg frequency {attr['avg_frequency']}")
        
        # Final Summary
        logger.info("\n" + "=" * 80)
        logger.info("BATCH PROCESSING COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        print(f"\n✓ Analysis Complete!")
        print(f"\nOutput Files:")
        print(f"  Raw Products: {raw_path}")
        print(f"  Catalog Data: {catalog_path}")
        print(f"  Analysis Report: {report_path}")
        print(f"  Attribute Table (JSON): {json_path}")
        print(f"  Attribute Table (CSV): {csv_path}")
        print(f"  Attribute Table (Excel): {excel_path}")
        
        print(f"\nKey Findings:")
        print(f"  - Processed {len(products)} products")
        print(f"  - Found {len(catalog_data['departments'])} departments")
        print(f"  - Identified {summary['unique_attributes']} unique attributes")
        print(f"  - Created comprehensive attribute mappings")
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
