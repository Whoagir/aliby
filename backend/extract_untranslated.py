#!/usr/bin/env python3
"""
Extract all untranslated words from words_alias.json
Creates a CSV file for manual translation
"""
import json
import csv
from pathlib import Path

DATA_DIR = Path("app/data")

print("Loading words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

# Collect all untranslated words
untranslated = []

for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    words_list = alias_data[difficulty]
    for word_obj in words_list:
        word = word_obj['word']
        translation = word_obj.get('translation', '')
        
        if not translation or translation == '':
            untranslated.append({
                'word': word,
                'difficulty': difficulty
            })

print(f"Found {len(untranslated)} untranslated words")

# Sort by difficulty then alphabetically
untranslated.sort(key=lambda x: (x['difficulty'], x['word']))

# Save as CSV for easy manual translation
csv_file = DATA_DIR / "untranslated_words.csv"
print(f"\nSaving to {csv_file}...")

with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['word', 'difficulty', 'translation'])
    
    for item in untranslated:
        writer.writerow([item['word'], item['difficulty'], ''])

print(f"✓ Created {csv_file}")
print(f"\nInstructions:")
print(f"1. Open {csv_file} in Excel/Google Sheets")
print(f"2. Fill 'translation' column (3rd column)")
print(f"3. Save the file")
print(f"4. Run: python apply_translations.py")

# Also save as simple TXT for quick reference
txt_file = DATA_DIR / "untranslated_words.txt"
with open(txt_file, 'w', encoding='utf-8') as f:
    for item in untranslated:
        f.write(f"{item['word']}\n")

print(f"✓ Created {txt_file} (simple list)")

# Show stats by difficulty
print("\nBreakdown by difficulty:")
for diff in ['easy', 'medium', 'hard', 'mixed']:
    count = sum(1 for x in untranslated if x['difficulty'] == diff)
    print(f"  {diff}: {count} words")
