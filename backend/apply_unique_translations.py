#!/usr/bin/env python3
"""
Apply unique translations to ALL occurrences in words_alias.json
"""
import json
import csv
from pathlib import Path

DATA_DIR = Path("app/data")

print("Loading untranslated_unique.csv...")
translations = {}

try:
    with open(DATA_DIR / "untranslated_unique.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row['word']
            translation = row['translation'].strip()
            if translation:
                translations[word] = translation
    
    print(f"Loaded {len(translations)} translations from CSV")
except FileNotFoundError:
    print("ERROR: untranslated_unique.csv not found!")
    exit(1)

if not translations:
    print("No translations found. Please fill the CSV first.")
    exit(1)

print("\nLoading words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

# Apply translations to ALL occurrences (including duplicates in mixed)
applied_count = 0
for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    for word_obj in alias_data[difficulty]:
        word = word_obj['word']
        if word in translations:
            word_obj['translation'] = translations[word]
            applied_count += 1

print(f"Applied {applied_count} translations (including duplicates)")

# Backup
backup_file = DATA_DIR / "words_alias_backup.json"
print(f"\nCreating backup: {backup_file}")
import shutil
shutil.copy(DATA_DIR / "words_alias.json", backup_file)

# Save
print("Saving updated words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'w', encoding='utf-8') as f:
    json.dump(alias_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done! Applied {applied_count} translations")
print(f"✓ {len(translations)} unique words translated")
print(f"✓ Backup: {backup_file}")
