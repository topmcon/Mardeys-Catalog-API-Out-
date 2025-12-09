"""
Ultra-conservative batch processing to work around API SOQL limits.
Processes 10 models at a time with longer delays.
"""
import os
import time
import json
from pathlib import Path
import logging

from salesforce_connector import SalesforceConnector
from catalog_extractor import CatalogExtractor
from attribute_analyzer import AttributeAnalyzer
from table_generator import AttributeTableGenerator
from config import AnalysisConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def safe_batch_extract(model_numbers, batch_size=10, delay=5):
    """Extract products with conservative batching"""
    connector = SalesforceConnector()
    all_products = []
    failed_batches = []
    
    total_batches = (len(model_numbers) + batch_size - 1) // batch_size
    
    print(f"\nProcessing {len(model_numbers)} models in {total_batches} batches of {batch_size}")
    print(f"Estimated time: ~{total_batches * delay / 60:.1f} minutes\n")
    
    for i in range(0, len(model_numbers), batch_size):
        batch = model_numbers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"[{batch_num}/{total_batches}] Processing {len(batch)} models...", end=" ")
        
        try:
            data = connector.search_products_by_model_numbers(batch)
            
            products = []
            if isinstance(data, dict):
                products = data.get('details', [])
            elif isinstance(data, list):
                products = data
            
            print(f"✓ Got {len(products)} products")
            all_products.extend(products)
            
            if i + batch_size < len(model_numbers):
                time.sleep(delay)
                
        except Exception as e:
            print(f"✗ Failed: {str(e)[:50]}")
            failed_batches.append(batch_num)
            time.sleep(delay * 2)  # Longer wait after error
    
    logger.info(f"\nExtraction complete: {len(all_products)} products from {len(model_numbers)} models")
    if failed_batches:
        logger.warning(f"Failed batches: {failed_batches}")
    
    return all_products


def main():
    print("=" * 80)
    print("COMPREHENSIVE PRODUCT CATALOG ANALYSIS")
    print("=" * 80)
    
    try:
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Load model numbers
        with open('model_numbers.txt', 'r') as f:
            model_numbers = [line.strip() for line in f if line.strip()]
        
        print(f"\nLoaded {len(model_numbers)} model numbers")
        
        # Extract products
        products = safe_batch_extract(model_numbers, batch_size=10, delay=5)
        
        if not products:
            print("\n✗ No products extracted. Please check API status.")
            return
        
        # Save raw data
        with open(output_dir / 'products_raw.json', 'w') as f:
            json.dump(products, f, indent=2, default=str)
        
        print(f"\n✓ Extracted {len(products)} products ({len(products)/len(model_numbers)*100:.1f}% match rate)")
        
        # Analyze and organize
        extractor = CatalogExtractor()
        
        catalog_data = extractor.organize_by_hierarchy(
            products,
            department_field='business_category',
            category_field='base_category',
            style_field='product_type'
        )
        
        extractor.save_catalog_data(str(output_dir / 'catalog_raw_data.json'))
        
        print(f"\n--- PRODUCT ORGANIZATION ---")
        print(f"Departments: {len(catalog_data['departments'])}")
        print(f"Categories: {len(catalog_data['categories'])}")
        print(f"Styles: {len(catalog_data['styles'])}")
        
        if catalog_data['departments']:
            print(f"\nDepartment Breakdown:")
            for dept, prods in sorted(catalog_data['departments'].items(), key=lambda x: len(x[1]), reverse=True):
                print(f"  • {dept}: {len(prods)} products")
        
        # Attribute analysis
        print(f"\n--- ANALYZING ATTRIBUTES ---")
        analyzer = AttributeAnalyzer(min_frequency=0.5)
        analysis_results = analyzer.analyze_all_groups(catalog_data, sample_size=30)
        analyzer.save_analysis(str(output_dir / 'analysis_report.json'))
        
        summary = analysis_results['summary']
        print(f"\nAttribute Analysis Results:")
        print(f"  • Unique attributes found: {summary['unique_attributes']}")
        print(f"  • Groups analyzed: {summary['total_departments'] + summary['total_categories'] + summary['total_styles']}")
        
        # Generate output tables
        print(f"\n--- GENERATING OUTPUT FILES ---")
        generator = AttributeTableGenerator(analysis_results)
        attribute_table = generator.generate_comprehensive_table()
        
        generator.save_as_json(str(output_dir / 'attribute_table.json'))
        generator.save_as_csv(str(output_dir / 'attribute_table.csv'))
        generator.save_as_excel(str(output_dir / 'attribute_table.xlsx'))
        
        print(f"\n✓ Generated attribute tables in multiple formats")
        
        # Display key findings
        print(f"\n{' KEY FINDINGS ':-^80}")
        
        if attribute_table['global_attributes']:
            print(f"\nGlobal Attributes (appear across 30%+ of product groups):")
            for attr in attribute_table['global_attributes'][:15]:
                print(f"  • {attr['display_name']}: {attr['group_count']} groups, {attr['avg_frequency']:.0%} avg frequency")
        
        print(f"\n{' OUTPUT FILES ':-^80}")
        print(f"\n  📄 output/attribute_table.json     - Website integration")
        print(f"  📊 output/attribute_table.xlsx     - Excel analysis")
        print(f"  📈 output/attribute_table.csv      - CSV export")
        print(f"  📋 output/analysis_report.json     - Detailed analysis")
        print(f"  💾 output/catalog_raw_data.json    - Organized catalog")
        print(f"  📦 output/products_raw.json        - Raw product data")
        
        print(f"\n{'='*80}")
        print(f"✓ ANALYSIS COMPLETE - {len(products)} products analyzed")
        print(f"{'='*80}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    main()
