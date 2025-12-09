"""
Attribute analysis engine for identifying common attributes across product categories.
"""
from collections import defaultdict, Counter
from config import AnalysisConfig
import logging
import json

logger = logging.getLogger(__name__)


class AttributeAnalyzer:
    """Analyzes product attributes to identify common patterns"""
    
    def __init__(self, min_frequency=None):
        """
        Initialize analyzer.
        
        Args:
            min_frequency: Minimum frequency (0-1) for an attribute to be considered common
        """
        self.min_frequency = min_frequency or AnalysisConfig.MIN_ATTRIBUTE_FREQUENCY
        self.analysis_results = {}
    
    def analyze_group(self, group_name, products, group_type='category'):
        """
        Analyze attributes for a group of products.
        
        Args:
            group_name: Name of the group (department, category, or style)
            products: List of product records
            group_type: Type of grouping (department, category, style)
        
        Returns:
            Analysis results for the group
        """
        logger.info(f"Analyzing {len(products)} products in {group_type}: {group_name}")
        
        # Count attribute occurrences
        attribute_counts = Counter()
        attribute_values = defaultdict(Counter)
        attribute_types = {}
        
        total_products = len(products)
        
        for product in products:
            for attr_name, attr_value in product.items():
                if attr_value is not None and attr_name != 'attributes':
                    attribute_counts[attr_name] += 1
                    
                    # Track unique values for each attribute (only for hashable types)
                    value_type = self._infer_type(attr_value)
                    if value_type in ['string', 'number', 'boolean']:
                        # Only track values for simple types
                        attribute_values[attr_name][attr_value] += 1
                    
                    # Infer attribute type
                    if attr_name not in attribute_types:
                        attribute_types[attr_name] = value_type
        
        # Calculate frequencies and identify common attributes
        common_attributes = {}
        for attr_name, count in attribute_counts.items():
            frequency = count / total_products
            
            if frequency >= self.min_frequency:
                values = dict(attribute_values[attr_name])
                
                common_attributes[attr_name] = {
                    'frequency': round(frequency, 3),
                    'occurrences': count,
                    'total_products': total_products,
                    'type': attribute_types[attr_name],
                    'unique_values_count': len(values),
                    'sample_values': self._get_top_values(values, top_n=10)
                }
        
        # Sort by frequency
        sorted_attributes = dict(sorted(
            common_attributes.items(),
            key=lambda x: x[1]['frequency'],
            reverse=True
        ))
        
        result = {
            'group_name': group_name,
            'group_type': group_type,
            'total_products': total_products,
            'total_attributes': len(attribute_counts),
            'common_attributes': sorted_attributes,
            'attribute_count': len(sorted_attributes)
        }
        
        logger.info(f"Found {len(sorted_attributes)} common attributes "
                   f"(frequency >= {self.min_frequency})")
        
        return result
    
    def analyze_all_groups(self, catalog_data, sample_size=None):
        """
        Analyze attributes across all departments, categories, and styles.
        
        Args:
            catalog_data: Organized catalog data with departments, categories, styles
            sample_size: Number of products to sample per group
        
        Returns:
            Complete analysis results
        """
        sample_size = sample_size or AnalysisConfig.SAMPLE_SIZE_PER_CATEGORY
        
        results = {
            'departments': {},
            'categories': {},
            'styles': {},
            'summary': {}
        }
        
        # Analyze departments
        logger.info("Analyzing departments...")
        for dept_name, products in catalog_data.get('departments', {}).items():
            sample = products[:sample_size]
            if sample:
                results['departments'][dept_name] = self.analyze_group(
                    dept_name, sample, 'department'
                )
        
        # Analyze categories
        logger.info("Analyzing categories...")
        for cat_name, products in catalog_data.get('categories', {}).items():
            sample = products[:sample_size]
            if sample:
                results['categories'][cat_name] = self.analyze_group(
                    cat_name, sample, 'category'
                )
        
        # Analyze styles
        logger.info("Analyzing styles...")
        for style_name, products in catalog_data.get('styles', {}).items():
            sample = products[:sample_size]
            if sample:
                results['styles'][style_name] = self.analyze_group(
                    style_name, sample, 'style'
                )
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        self.analysis_results = results
        return results
    
    def _infer_type(self, value):
        """Infer the type of an attribute value"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, (int, float)):
            return 'number'
        elif isinstance(value, str):
            if len(value) > 100:
                return 'text'
            else:
                return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'
    
    def _get_top_values(self, value_counts, top_n=10):
        """Get the most common values for an attribute"""
        sorted_values = sorted(
            value_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'value': str(val), 'count': count}
            for val, count in sorted_values[:top_n]
        ]
    
    def _generate_summary(self, results):
        """Generate summary statistics from analysis results"""
        all_attributes = set()
        
        # Collect all unique attributes
        for group_type in ['departments', 'categories', 'styles']:
            for group_data in results[group_type].values():
                all_attributes.update(group_data['common_attributes'].keys())
        
        # Count attribute frequencies across groups
        attribute_group_counts = Counter()
        for group_type in ['departments', 'categories', 'styles']:
            for group_data in results[group_type].values():
                for attr in group_data['common_attributes'].keys():
                    attribute_group_counts[attr] += 1
        
        summary = {
            'total_departments': len(results['departments']),
            'total_categories': len(results['categories']),
            'total_styles': len(results['styles']),
            'unique_attributes': len(all_attributes),
            'most_common_attributes': [
                {'attribute': attr, 'group_count': count}
                for attr, count in attribute_group_counts.most_common(20)
            ]
        }
        
        return summary
    
    def save_analysis(self, filepath):
        """Save analysis results to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            logger.info(f"Analysis results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            raise
