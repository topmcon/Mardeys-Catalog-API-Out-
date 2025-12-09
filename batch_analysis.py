"""
Batch processor for analyzing all model numbers in smaller batches.
Processes 30 model numbers at a time with delays to avoid API limits.
"""
import time
import json
from salesforce_connector import SalesforceConnector
from catalog_extractor import CatalogExtractor
from attribute_analyzer import AttributeAnalyzer
from table_generator import AttributeTableGenerator
from config import AnalysisConfig
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_in_batches(model_numbers, batch_size=30, delay=2):
    """
    Process model numbers in batches with delays.
    
    Args:
        model_numbers: List of model numbers to process
        batch_size: Number of models per batch
        delay: Seconds to wait between batches
    
    Returns:
        List of all product records
    """
    connector = SalesforceConnector()
    all_products = []
    total_batches = (len(model_numbers) + batch_size - 1) // batch_size
    
    logger.info(f"Processing {len(model_numbers)} model numbers in {total_batches} batches of {batch_size}")
    
    for i in range(0, len(model_numbers), batch_size):
        batch = model_numbers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} models)...")
        
        try:
            result = connector.search_products_by_model_numbers(batch)
            
            # Extract products from response
            products = []
            if isinstance(result, dict):
                products = result.get('details', result.get('products', result.get('results', [])))
            elif isinstance(result, list):
                products = result
            
            all_products.extend(products)
            logger.info(f"  ✓ Batch {batch_num} complete: retrieved {len(products)} products")
            
            # Save progress after each batch
            if products:
                progress_file = f'output/batch_progress_{batch_num}.json'
                Path('output').mkdir(exist_ok=True)
                with open(progress_file, 'w') as f:
                    json.dump(products, f, indent=2, default=str)
            
            # Delay between batches (except for the last one)
            if i + batch_size < len(model_numbers):
                logger.info(f"  Waiting {delay} seconds before next batch...")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"  ✗ Error processing batch {batch_num}: {str(e)}")
            logger.info(f"  Continuing with next batch...")
            time.sleep(delay * 2)  # Longer delay after error
            continue
    
    logger.info(f"Batch processing complete: {len(all_products)} total products retrieved")
    return all_products


def main():
    """Main execution for batch analysis"""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE CATALOG ANALYSIS - BATCH PROCESSING")
    logger.info("=" * 80)
    
    # Setup output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Load model numbers
    model_file = 'model_numbers.txt'
    logger.info(f"\nLoading model numbers from {model_file}...")
    
    with open(model_file, 'r') as f:
        model_numbers = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(model_numbers)} model numbers")
    
    # Process in batches
    logger.info("\n--- BATCH PRODUCT EXTRACTION ---")
    all_products = process_in_batches(model_numbers, batch_size=30, delay=2)
    
    if not all_products:
        logger.error("No products retrieved. Exiting.")
        return
    
    # Save combined results
    logger.info(f"\nSaving combined results...")
    with open('output/all_products_combined.json', 'w') as f:
        json.dump(all_products, f, indent=2, default=str)
    logger.info(f"  ✓ Saved {len(all_products)} products to all_products_combined.json")
    
    # Organize by hierarchy
    logger.info("\n--- ORGANIZING BY HIERARCHY ---")
    extractor = CatalogExtractor()
    extractor.catalog_data['products'] = all_products
    
    # Try to detect hierarchy fields
    sample_product = all_products[0] if all_products else {}
    dept_field = next((k for k in sample_product.keys() if 'category' in k.lower() or 'department' in k.lower()), None)
    cat_field = next((k for k in sample_product.keys() if 'base_category' in k.lower() or 'product_type' in k.lower()), None)
    
    catalog_data = extractor.organize_by_hierarchy(
        all_products,
        department_field=dept_field or 'business_category',
        category_field=cat_field or 'base_category',
        style_field=None
    )
    
    extractor.save_catalog_data('output/catalog_full_data.json')
    
    print(f"\nOrganization Summary:")
    print(f"  Total Products: {len(all_products)}")
    print(f"  Departments: {len(catalog_data['departments'])}")
    print(f"  Categories: {len(catalog_data['categories'])}")
    print(f"  Styles: {len(catalog_data['styles'])}")
    
    # List departments and their counts
    print(f"\nDepartments Found:")
    for dept_name, products in sorted(catalog_data['departments'].items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  - {dept_name}: {len(products)} products")
    
    # List categories
    if catalog_data['categories']:
        print(f"\nCategories Found:")
        for cat_name, products in sorted(catalog_data['categories'].items(), key=lambda x: len(x[1]), reverse=True)[:20]:
            print(f"  - {cat_name}: {len(products)} products")
        if len(catalog_data['categories']) > 20:
            print(f"  ... and {len(catalog_data['categories']) - 20} more categories")
    
    # Analyze attributes
    logger.info("\n--- ATTRIBUTE ANALYSIS ---")
    analyzer = AttributeAnalyzer(min_frequency=0.5)
    analysis_results = analyzer.analyze_all_groups(catalog_data, sample_size=30)
    analyzer.save_analysis('output/full_analysis_report.json')
    
    print(f"\nAttribute Analysis Summary:")
    summary = analysis_results['summary']
    print(f"  Unique Attributes: {summary['unique_attributes']}")
    print(f"\n  Top 20 Most Common Attributes:")
    for item in summary['most_common_attributes'][:20]:
        print(f"    - {item['attribute']}: appears in {item['group_count']} groups")
    
    # Generate attribute tables
    logger.info("\n--- GENERATING ATTRIBUTE TABLES ---")
    generator = AttributeTableGenerator(analysis_results)
    attribute_table = generator.generate_comprehensive_table()
    
    generator.save_as_json('output/attribute_table_full.json')
    generator.save_as_csv('output/attribute_table_full.csv')
    generator.save_as_excel('output/attribute_table_full.xlsx')
    
    print(f"\n  Global Attributes (appear in 30%+ of groups):")
    for attr in attribute_table['global_attributes'][:20]:
        print(f"    - {attr['display_name']}: {attr['group_count']} groups, "
              f"avg frequency {attr['avg_frequency']}")
    
    # Generate insights report
    logger.info("\n--- GENERATING INSIGHTS ---")
    insights = generate_insights(all_products, catalog_data, analysis_results)
    
    with open('output/catalog_insights.json', 'w') as f:
        json.dump(insights, f, indent=2, default=str)
    
    print(f"\n" + "=" * 80)
    print("COMPREHENSIVE ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nOutput Files:")
    print(f"  - output/all_products_combined.json")
    print(f"  - output/catalog_full_data.json")
    print(f"  - output/full_analysis_report.json")
    print(f"  - output/attribute_table_full.json")
    print(f"  - output/attribute_table_full.csv")
    print(f"  - output/attribute_table_full.xlsx")
    print(f"  - output/catalog_insights.json")


def generate_insights(products, catalog_data, analysis_results):
    """Generate insights from the analysis"""
    insights = {
        'overview': {
            'total_products': len(products),
            'total_departments': len(catalog_data['departments']),
            'total_categories': len(catalog_data['categories']),
            'unique_attributes': analysis_results['summary']['unique_attributes']
        },
        'departments': {},
        'common_attributes': [],
        'attribute_coverage': {}
    }
    
    # Department insights
    for dept_name, dept_products in catalog_data['departments'].items():
        brands = set()
        price_range = {'min': float('inf'), 'max': 0}
        
        for product in dept_products:
            if isinstance(product, dict):
                if 'brand' in product and product['brand']:
                    brands.add(product['brand'])
                if 'price' in product and product['price']:
                    try:
                        price = float(product['price'])
                        price_range['min'] = min(price_range['min'], price)
                        price_range['max'] = max(price_range['max'], price)
                    except:
                        pass
        
        insights['departments'][dept_name] = {
            'product_count': len(dept_products),
            'brand_count': len(brands),
            'brands': sorted(list(brands))[:10],
            'price_range': {
                'min': price_range['min'] if price_range['min'] != float('inf') else None,
                'max': price_range['max'] if price_range['max'] > 0 else None
            }
        }
    
    # Common attributes
    for attr_info in analysis_results['summary']['most_common_attributes'][:30]:
        insights['common_attributes'].append(attr_info)
    
    return insights


if __name__ == "__main__":
    main()
