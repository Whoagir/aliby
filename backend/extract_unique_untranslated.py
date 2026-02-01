#!/usr/bin/env python3
"""
Extract UNIQUE untranslated words (no duplicates)
"""
import json
import csv
from pathlib import Path

DATA_DIR = Path("app/data")

print("Loading words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

# Collect unique untranslated words
untranslated = {}  # word -> difficulty (keep first occurrence)

for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    words_list = alias_data[difficulty]
    for word_obj in words_list:
        word = word_obj['word']
        translation = word_obj.get('translation', '')
        
        if (not translation or translation == '') and word not in untranslated:
            untranslated[word] = difficulty

print(f"Found {len(untranslated)} UNIQUE untranslated words")

# Sort alphabetically
sorted_words = sorted(untranslated.items())

# Save as CSV
csv_file = DATA_DIR / "untranslated_unique.csv"
print(f"\nSaving to {csv_file}...")

with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['word', 'difficulty', 'translation'])
    
    for word, difficulty in sorted_words:
        writer.writerow([word, difficulty, ''])

print(f"✓ Created {csv_file}")

# Stats
print("\nBreakdown by first occurrence:")
stats = {}
for word, diff in untranslated.items():
    stats[diff] = stats.get(diff, 0) + 1

for diff in ['easy', 'medium', 'hard', 'mixed']:
    count = stats.get(diff, 0)
    print(f"  {diff}: {count} words")

print(f"\n📝 INSTRUCTIONS:")
print(f"1. Open: {csv_file}")
print(f"2. Fill the 'translation' column (3rd column)")
print(f"3. Save as CSV with UTF-8 encoding")
print(f"4. Run: python apply_unique_translations.py")
