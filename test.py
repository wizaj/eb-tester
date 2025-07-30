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

def create_dummy_test_data():
    """Create dummy test data for first-time users."""
    return {
        "NG": {
            "customer_data": {
                "name": "Test User",
                "email": "test+ng@ebanx.com",
                "phone_number": "+2348089895495",
                "birth_date": "01/01/1990",
                "country": "ng",
                "currency_code": "NGN",
                "default_amount": 100
            },
            "debitcard": {
                "visa": [
                    {
                        "card_number": "4111111111111111",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "NG - Test Visa Card - NGN",
                        "custom_payload": {
                            "integration_key": "{integration_key}",
                            "operation": "request",
                            "payment": {
                                "amount_total": 100,
                                "currency_code": "NGN",
                                "name": "Test User",
                                "email": "test+ng@ebanx.com",
                                "birth_date": "01/01/1990",
                                "country": "ng",
                                "phone_number": "+2348089895495",
                                "card": {
                                    "card_number": "4111111111111111",
                                    "card_name": "Test User",
                                    "card_due_date": "12/2025",
                                    "card_cvv": "123",
                                    "auto_capture": True,
                                    "threeds_force": False
                                }
                            }
                        }
                    }
                ],
                "mastercard": [
                    {
                        "card_number": "5555555555554444",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "NG - Test Mastercard - NGN"
                    }
                ]
            }
        },
        "KE": {
            "customer_data": {
                "name": "Test User",
                "email": "test+ke@ebanx.com",
                "phone_number": "+254708663158",
                "birth_date": "01/01/1990",
                "country": "ke",
                "currency_code": "KES",
                "default_amount": 75
            },
            "debitcard": {
                "visa": [
                    {
                        "card_number": "4111111111111111",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "KE - Test Visa Card - KES"
                    }
                ]
            },
            "mobile_money": {
                "mpesa": {
                    "phone_number": "254708663158",
                    "description": "KE - MPESA Test Number"
                }
            }
        },
        "ZA": {
            "customer_data": {
                "name": "Test User",
                "email": "test+za@ebanx.com",
                "phone_number": "+27123456789",
                "birth_date": "01/01/1990",
                "country": "za",
                "currency_code": "ZAR",
                "default_amount": 10
            },
            "debitcard": {
                "mastercard": [
                    {
                        "card_number": "5555555555554444",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "ZA - Test Mastercard - ZAR"
                    }
                ]
            }
        },
        "EG": {
            "customer_data": {
                "name": "Test User",
                "email": "test+eg@ebanx.com",
                "phone_number": "+201234567890",
                "birth_date": "01/01/1990",
                "country": "eg",
                "currency_code": "EGP",
                "default_amount": 50
            },
            "debitcard": {
                "visa": [
                    {
                        "card_number": "4111111111111111",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "EG - Test Visa Card - EGP"
                    }
                ]
            }
        }
    }

def load_json(path: str):
    """Load JSON file, creating dummy data if test-cards.json doesn't exist."""
    if not os.path.exists(path):
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # If this is the test-cards.json file, create it with dummy data
        if path.endswith("test-cards.json"):
            dummy_data = create_dummy_test_data()
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(dummy_data, fh, indent=2)
            return dummy_data
        else:
            raise FileNotFoundError(path)
    
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def test_data_loading():
    logger = setup_simple_logging()
    logger.info("Starting data loading test...")
    
    # Test test-cards.json loading
    logger.info("Testing test-cards.json loading...")
    try:
        test_data = load_json('data/test-cards.json')
        
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
        logger.error(f"❌ Error loading test-cards.json: {e}")
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
        from qt_gui import setup_logging
        
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