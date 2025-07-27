#!/usr/bin/env python3
"""
Test data loading without GUI to isolate issues
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_simple_logging():
    """Setup simple logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('DataTest')

def test_data_loading():
    logger = setup_simple_logging()
    logger.info("Starting data loading test...")
    
    # Test test_cards.json loading
    logger.info("Testing test_cards.json loading...")
    try:
        with open('data/test_cards.json', 'r') as f:
            test_data = json.load(f)
        
        countries = list(test_data.keys())
        total_cards = sum(
            len(card_list) 
            for country_data in test_data.values() 
            if 'debitcard' in country_data
            for card_list in country_data['debitcard'].values()
        )
        
        logger.info(f"✅ Successfully loaded test data: {len(countries)} countries, {total_cards} total cards")
        logger.info(f"Countries: {countries}")
        
        # Test card population logic
        cards = []
        for country, data in test_data.items():
            if 'debitcard' in data:
                for card_type, card_list in data['debitcard'].items():
                    for card in card_list:
                        display_name = f"{country} - {card['description']}"
                        cards.append(display_name)
        
        logger.info(f"✅ Card selector would have {len(cards)} options")
        logger.info(f"First 3 cards: {cards[:3]}")
        
    except Exception as e:
        logger.error(f"❌ Error loading test_cards.json: {e}")
        return False
    
    # Test PTP list loading
    logger.info("Testing ptp-list.txt loading...")
    try:
        with open('data/ptp-list.txt', 'r') as f:
            ptp_list = [line.strip() for line in f.readlines() if line.strip()]
        
        logger.info(f"✅ Successfully loaded {len(ptp_list)} PTPs")
        logger.info(f"First 3 PTPs: {ptp_list[:3]}")
        logger.info(f"Last 3 PTPs: {ptp_list[-3:]}")
        
    except Exception as e:
        logger.error(f"❌ Error loading ptp-list.txt: {e}")
        return False
    
    logger.info("✅ All data loading tests passed!")
    return True

def test_logging_system():
    """Test if our logging system works without GUI"""
    logger = setup_simple_logging()
    logger.info("Testing logging system...")
    
    try:
        # Import our logging setup
        from gui.main_window import setup_logging
        
        app_logger = setup_logging()
        app_logger.info("Application logging system test")
        app_logger.warning("This is a warning")
        app_logger.error("This is an error (test)")
        
        logger.info("✅ Application logging system works")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error with application logging: {e}")
        return False

def main():
    print("="*60)
    print("EBANX PTP Tester - Data Loading Test")
    print("="*60)
    
    # Test 1: Data loading
    if not test_data_loading():
        print("❌ Data loading failed - check data files")
        return False
    
    # Test 2: Logging system
    if not test_logging_system():
        print("❌ Logging system failed")
        return False
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("✅ Data loading works correctly")
    print("✅ Logging system works correctly")
    print("The issue is likely with tkinter/GUI display, not data loading")
    print("="*60)
    
    return True

if __name__ == "__main__":
    main() 