#!/usr/bin/env python3
"""
Split untranslated words by priority
"""
import json
import csv
from pathlib import Path

DATA_DIR = Path("app/data")

print("Loading untranslated_unique.csv...")
words_by_difficulty = {
    'easy': [],
    'medium': [],
    'hard': []
}

with open(DATA_DIR / "untranslated_unique.csv", 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        diff = row['difficulty']
        if diff in words_by_difficulty:
            words_by_difficulty[diff].append(row['word'])

# Priority 1: Easy words (most common)
print(f"\nCreating priority files...")
with open(DATA_DIR / "to_translate_1_EASY.csv", 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['word', 'translation'])
    for word in words_by_difficulty['easy']:
        writer.writerow([word, ''])

print(f"✓ Priority 1: {len(words_by_difficulty['easy'])} easy words")

# Priority 2: Medium words
with open(DATA_DIR / "to_translate_2_MEDIUM.csv", 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['word', 'translation'])
    for word in words_by_difficulty['medium']:
        writer.writerow([word, ''])

print(f"✓ Priority 2: {len(words_by_difficulty['medium'])} medium words")

# Priority 3: Hard words (least common)
with open(DATA_DIR / "to_translate_3_HARD.csv", 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['word', 'translation'])
    for word in words_by_difficulty['hard']:
        writer.writerow([word, ''])

print(f"✓ Priority 3: {len(words_by_difficulty['hard'])} hard words")

print(f"\n📝 RECOMMENDATION:")
print(f"Start with: to_translate_1_EASY.csv (most important)")
print(f"Then: to_translate_2_MEDIUM.csv")
print(f"Finally: to_translate_3_HARD.csv (rare words)")
print(f"\nAfter translating, merge them back with:")
print(f"  python merge_translations.py")
