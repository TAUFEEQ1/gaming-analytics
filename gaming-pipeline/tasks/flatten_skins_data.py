"""
Luigi task to flatten the Skins_Price.csv dataset into simple item-price pairings.

This task transforms the wide-format dataset where each row contains multiple price columns
into a long-format dataset where each row represents a single item-price pair.

The item name combines weapon attributes (weapon, case, rarity) with condition and StatTrak status.
"""

import luigi
import pandas as pd
import numpy as np
import os
from pathlib import Path


class FlattenSkinsDataTask(luigi.Task):
    """
    Luigi task to flatten the skins price dataset.
    
    Converts from wide format (multiple price columns) to long format (item-price pairs).
    Each row in the output will have:
    - item: Combined name with weapon, case, rarity, condition, and StatTrak status
    - price: The price value for that specific item configuration
    """
    
    input_file = luigi.Parameter(default="data/Skins_Price.csv")
    output_file = luigi.Parameter(default="output/flattened_skins_data.csv")
    
    def requires(self):
        """No dependencies for this task."""
        return []
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Execute the flattening transformation."""
        # Read the input data
        df = pd.read_csv(self.input_file)
        
        # Define the price columns and their corresponding conditions
        price_columns = {
            'StatTrak Factory New': 'StatTrak Factory New',
            'StatTrak Minimal Wear': 'StatTrak Minimal Wear',
            'StatTrak Field-Tested': 'StatTrak Field-Tested',
            'StatTrak Well-Worn': 'StatTrak Well-Worn',
            'StatTrak Battle-Scarred': 'StatTrak Battle-Scarred',
            'Factory New': 'Factory New',
            'Minimal Wear': 'Minimal Wear',
            'Field-Tested': 'Field-Tested',
            'Well-Worn': 'Well-Worn',
            'Battle-Scarred': 'Battle-Scarred'
        }
        
        # Prepare list to store flattened rows
        flattened_rows = []
        
        for _, row in df.iterrows():
            # Base item attributes
            weapon = row['Weapon']
            case = row['Case']
            rarity = row['Rarity']
            min_wear = row['Min Wear']
            max_wear = row['Max Wear']
            case_1 = row['Case_1']
            
            # Create base item identifier with key attributes
            base_item = f"{weapon} | {case} | {rarity}"
            
            # Process each price column
            for price_col, condition in price_columns.items():
                price_str = str(row[price_col]).strip()
                
                # Skip if price is not available or is "Not Possible"
                if pd.isna(row[price_col]) or price_str in ['Not Possible', 'nan', '']:
                    continue
                
                try:
                    # Clean price string and convert to float
                    clean_price = price_str.replace('$', '').replace(',', '')
                    price = float(clean_price)
                    
                    # Create full item name with condition
                    full_item = f"{base_item} | {condition}"
                    
                    # Add metadata as part of the item name for context
                    detailed_item = f"{full_item} (Wear: {min_wear}-{max_wear}, Case: {case_1})"
                    
                    # Add to flattened rows
                    flattened_rows.append({
                        'item': detailed_item,
                        'price': price,
                        'weapon': weapon,
                        'case': case,
                        'rarity': rarity,
                        'condition': condition,
                        'is_stattrak': 'StatTrak' in condition,
                        'min_wear': min_wear,
                        'max_wear': max_wear,
                        'case_source': case_1
                    })
                    
                except (ValueError, TypeError):
                    # Skip invalid price values
                    continue
        
        # Create DataFrame from flattened rows
        flattened_df = pd.DataFrame(flattened_rows)
        
        # Sort by price descending to see most expensive items first
        flattened_df = flattened_df.sort_values('price', ascending=False)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save to CSV
        flattened_df.to_csv(self.output_file, index=False)
        
        print(f"Flattened {len(df)} rows into {len(flattened_df)} item-price pairs")
        print(f"Output saved to: {self.output_file}")
        print(f"Price range: ${flattened_df['price'].min():.2f} - ${flattened_df['price'].max():.2f}")


class FlattenSkinsSimpleTask(luigi.Task):
    """
    Luigi task to create a minimal flattened version with just item and price columns.
    
    This creates the simplest possible item-price pairing as requested.
    """
    
    input_file = luigi.Parameter(default="data/Skins_Price.csv")
    output_file = luigi.Parameter(default="output/simple_item_price.csv")
    
    def requires(self):
        """No dependencies for this task."""
        return []
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Execute the simple flattening transformation."""
        # Read the input data
        df = pd.read_csv(self.input_file)
        
        # Define the price columns
        price_columns = [
            'StatTrak Factory New', 'StatTrak Minimal Wear', 'StatTrak Field-Tested',
            'StatTrak Well-Worn', 'StatTrak Battle-Scarred',
            'Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred'
        ]
        
        # Prepare list for simple item-price pairs
        simple_pairs = []
        
        for _, row in df.iterrows():
            # Combine weapon, case, and rarity into base item name
            base_item = f"{row['Weapon']} {row['Case']} {row['Rarity']}"
            
            # Process each price column
            for condition in price_columns:
                price_str = str(row[condition]).strip()
                
                # Skip invalid prices
                if pd.isna(row[condition]) or price_str in ['Not Possible', 'nan', '']:
                    continue
                
                try:
                    # Clean and convert price
                    price = float(price_str.replace('$', '').replace(',', ''))
                    
                    # Create item name with condition
                    item = f"{base_item} {condition}"
                    
                    simple_pairs.append({
                        'item': item,
                        'price': price
                    })
                    
                except (ValueError, TypeError):
                    continue
        
        # Create simple DataFrame
        simple_df = pd.DataFrame(simple_pairs)
        simple_df = simple_df.sort_values('price', ascending=False)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save to CSV
        simple_df.to_csv(self.output_file, index=False)
        
        print(f"Created {len(simple_df)} simple item-price pairs")
        print(f"Output saved to: {self.output_file}")


if __name__ == "__main__":
    # Run both tasks
    luigi.run()