"""
Output generator for creating static attribute tables in various formats.
"""
import json
import csv
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AttributeTableGenerator:
    """Generates static attribute tables from analysis results"""
    
    def __init__(self, analysis_results):
        """
        Initialize with analysis results.
        
        Args:
            analysis_results: Complete analysis results from AttributeAnalyzer
        """
        self.analysis_results = analysis_results
        self.attribute_table = None
    
    def generate_comprehensive_table(self):
        """
        Generate a comprehensive attribute mapping table.
        
        Returns:
            Dictionary with attribute mappings for each group type
        """
        logger.info("Generating comprehensive attribute table...")
        
        table = {
            'metadata': {
                'description': 'Static attribute table for product catalog',
                'min_frequency': 0.5,
                'sample_size_per_group': 30
            },
            'departments': {},
            'categories': {},
            'styles': {},
            'global_attributes': []
        }
        
        # Process departments
        for dept_name, dept_data in self.analysis_results.get('departments', {}).items():
            table['departments'][dept_name] = self._format_group_attributes(dept_data)
        
        # Process categories
        for cat_name, cat_data in self.analysis_results.get('categories', {}).items():
            table['categories'][cat_name] = self._format_group_attributes(cat_data)
        
        # Process styles
        for style_name, style_data in self.analysis_results.get('styles', {}).items():
            table['styles'][style_name] = self._format_group_attributes(style_data)
        
        # Extract global attributes (appearing across multiple groups)
        table['global_attributes'] = self._extract_global_attributes()
        
        self.attribute_table = table
        logger.info("Attribute table generated successfully")
        
        return table
    
    def _format_group_attributes(self, group_data):
        """Format attributes for a single group"""
        attributes = []
        
        for attr_name, attr_info in group_data.get('common_attributes', {}).items():
            attributes.append({
                'name': attr_name,
                'display_name': self._format_display_name(attr_name),
                'type': attr_info['type'],
                'frequency': attr_info['frequency'],
                'required': attr_info['frequency'] >= 0.9,  # 90%+ = required
                'filterable': attr_info['unique_values_count'] < 50,
                'unique_values': attr_info['unique_values_count'],
                'sample_values': attr_info['sample_values']
            })
        
        return {
            'total_products_analyzed': group_data.get('total_products', 0),
            'attribute_count': len(attributes),
            'attributes': attributes
        }
    
    def _extract_global_attributes(self):
        """Extract attributes that appear across multiple groups"""
        attribute_frequencies = {}
        
        # Count how many groups each attribute appears in
        for group_type in ['departments', 'categories', 'styles']:
            for group_name, group_data in self.analysis_results.get(group_type, {}).items():
                for attr_name, attr_info in group_data.get('common_attributes', {}).items():
                    if attr_name not in attribute_frequencies:
                        attribute_frequencies[attr_name] = {
                            'count': 0,
                            'total_frequency': 0,
                            'type': attr_info['type']
                        }
                    attribute_frequencies[attr_name]['count'] += 1
                    attribute_frequencies[attr_name]['total_frequency'] += attr_info['frequency']
        
        # Filter for truly global attributes (appear in 50%+ of groups)
        total_groups = (
            len(self.analysis_results.get('departments', {})) +
            len(self.analysis_results.get('categories', {})) +
            len(self.analysis_results.get('styles', {}))
        )
        
        global_attrs = []
        for attr_name, attr_data in attribute_frequencies.items():
            if attr_data['count'] >= total_groups * 0.3:  # 30%+ of groups
                global_attrs.append({
                    'name': attr_name,
                    'display_name': self._format_display_name(attr_name),
                    'type': attr_data['type'],
                    'group_count': attr_data['count'],
                    'avg_frequency': round(attr_data['total_frequency'] / attr_data['count'], 3)
                })
        
        # Sort by group count
        global_attrs.sort(key=lambda x: x['group_count'], reverse=True)
        
        return global_attrs
    
    def _format_display_name(self, field_name):
        """Convert field name to human-readable display name"""
        # Remove common prefixes
        name = field_name.replace('__c', '').replace('Product_', '')
        
        # Split on underscores and capitalize
        words = name.replace('_', ' ').split()
        return ' '.join(word.capitalize() for word in words)
    
    def save_as_json(self, filepath):
        """Save attribute table as JSON"""
        if not self.attribute_table:
            self.generate_comprehensive_table()
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.attribute_table, f, indent=2, default=str)
            logger.info(f"Attribute table saved as JSON: {filepath}")
        except Exception as e:
            logger.error(f"Error saving JSON: {str(e)}")
            raise
    
    def save_as_csv(self, filepath):
        """Save attribute table as CSV (flattened format)"""
        if not self.attribute_table:
            self.generate_comprehensive_table()
        
        try:
            rows = []
            
            # Flatten the structure for CSV
            for group_type in ['departments', 'categories', 'styles']:
                for group_name, group_data in self.attribute_table.get(group_type, {}).items():
                    for attr in group_data.get('attributes', []):
                        rows.append({
                            'group_type': group_type.rstrip('s'),  # singular
                            'group_name': group_name,
                            'attribute_name': attr['name'],
                            'display_name': attr['display_name'],
                            'type': attr['type'],
                            'frequency': attr['frequency'],
                            'required': attr['required'],
                            'filterable': attr['filterable'],
                            'unique_values': attr['unique_values']
                        })
            
            # Write CSV
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(filepath, index=False, encoding='utf-8')
                logger.info(f"Attribute table saved as CSV: {filepath}")
            else:
                logger.warning("No data to write to CSV")
                
        except Exception as e:
            logger.error(f"Error saving CSV: {str(e)}")
            raise
    
    def save_as_excel(self, filepath):
        """Save attribute table as Excel with multiple sheets"""
        if not self.attribute_table:
            self.generate_comprehensive_table()
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Global attributes sheet
                if self.attribute_table.get('global_attributes'):
                    global_df = pd.DataFrame(self.attribute_table['global_attributes'])
                    global_df.to_excel(writer, sheet_name='Global Attributes', index=False)
                
                # Department attributes
                dept_rows = self._flatten_group_data('departments')
                if dept_rows:
                    pd.DataFrame(dept_rows).to_excel(writer, sheet_name='Departments', index=False)
                
                # Category attributes
                cat_rows = self._flatten_group_data('categories')
                if cat_rows:
                    pd.DataFrame(cat_rows).to_excel(writer, sheet_name='Categories', index=False)
                
                # Style attributes
                style_rows = self._flatten_group_data('styles')
                if style_rows:
                    pd.DataFrame(style_rows).to_excel(writer, sheet_name='Styles', index=False)
                
                # Summary sheet
                summary_data = {
                    'Metric': [
                        'Total Departments',
                        'Total Categories',
                        'Total Styles',
                        'Global Attributes',
                        'Unique Attributes'
                    ],
                    'Count': [
                        len(self.attribute_table.get('departments', {})),
                        len(self.attribute_table.get('categories', {})),
                        len(self.attribute_table.get('styles', {})),
                        len(self.attribute_table.get('global_attributes', [])),
                        len(self._get_all_unique_attributes())
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"Attribute table saved as Excel: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving Excel: {str(e)}")
            raise
    
    def _flatten_group_data(self, group_type):
        """Flatten group data for tabular format"""
        rows = []
        for group_name, group_data in self.attribute_table.get(group_type, {}).items():
            for attr in group_data.get('attributes', []):
                rows.append({
                    'group_name': group_name,
                    'attribute_name': attr['name'],
                    'display_name': attr['display_name'],
                    'type': attr['type'],
                    'frequency': attr['frequency'],
                    'required': attr['required'],
                    'filterable': attr['filterable'],
                    'unique_values': attr['unique_values']
                })
        return rows
    
    def _get_all_unique_attributes(self):
        """Get all unique attribute names across all groups"""
        all_attrs = set()
        
        for group_type in ['departments', 'categories', 'styles']:
            for group_data in self.attribute_table.get(group_type, {}).values():
                for attr in group_data.get('attributes', []):
                    all_attrs.add(attr['name'])
        
        return all_attrs
