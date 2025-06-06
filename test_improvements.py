#!/usr/bin/env python3
"""
Test script to demonstrate the improvements made to the CSV special character filter.
"""

import pandas as pd
import os
import sys
import tempfile

# Add the main module to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import contains_special_characters

def test_special_character_detection():
    """Test the improved special character detection function."""
    print("Testing special character detection...")
    
    # Test cases
    test_cases = [
        ("Normal text", False),
        ("Text with émojis 😀", True),
        ("Café", True),
        ("Price: $50", False),
        ("", False),
        (None, False),
        (float('nan'), False),
        (123, False),
        ("Résumé", True),
        ("Hello\tWorld", False),  # Tab is within ASCII range
        ("Hello\nWorld", False),  # Newline is within ASCII range
        ("Tést", True),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for text, expected in test_cases:
        result = contains_special_characters(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{text}' -> {result} (expected: {expected})")
        if result == expected:
            passed += 1
    
    print(f"\nTest Results: {passed}/{total} passed")
    return passed == total

def create_sample_csv():
    """Create a sample CSV file for testing."""
    data = {
        'Title': [
            'Normal Game Title',
            'Café Adventure',
            'Simple Puzzle',
            'Pokémon Quest',
            'Test Game'
        ],
        'Developer': [
            'Normal Studio',
            'Gaming Inc',
            'Tést Studios', 
            'Regular Dev',
            'Émoji Games 😀'
        ],
        'Price': [9.99, 14.99, 4.99, 19.99, 0.99]
    }
    
    df = pd.DataFrame(data)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    print(f"Sample CSV created: {temp_file.name}")
    print("Rows with special characters should be:")
    print("- Row 2: 'Café Adventure' (Title)")
    print("- Row 4: 'Tést Studios' (Developer)")
    print("- Row 5: 'Émoji Games 😀' (Developer)")
    
    return temp_file.name

def main():
    """Run the test suite."""
    print("=" * 50)
    print("CSV Special Character Filter - Improvement Tests")
    print("=" * 50)
    
    # Test 1: Special character detection
    if test_special_character_detection():
        print("\n✓ Special character detection tests passed!")
    else:
        print("\n✗ Special character detection tests failed!")
        return False
    
    # Test 2: Create sample CSV for manual testing
    print("\n" + "-" * 30)
    print("Creating sample CSV for manual testing...")
    sample_file = create_sample_csv()
    
    print(f"\n📁 Sample CSV file created at: {sample_file}")
    print("\nYou can now run the main application and test with this file:")
    print("python main.py")
    
    return True

if __name__ == "__main__":
    main()
