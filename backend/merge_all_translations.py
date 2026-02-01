#!/usr/bin/env python3
"""
Merge ALL translation files (EASY + all MEDIUM/HARD parts)
"""
import json
import csv
from pathlib import Path
import glob

DATA_DIR = Path("app/data")

print("Loading translations from ALL files...")
translations = {}

# Load EASY (already translated)
easy_file = DATA_DIR / "to_translate_1_EASY.csv"
if easy_file.exists():
    with open(easy_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            word = row['word']
            translation = row['translation'].strip()
            if translation:
                translations[word] = translation
                count += 1
        print(f"  ✓ EASY: {count} translations")

# Load all MEDIUM parts
for medium_file in sorted(DATA_DIR.glob("translate_MEDIUM_part*.csv")):
    with open(medium_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            word = row['word']
            translation = row['translation'].strip()
            if translation:
                translations[word] = translation
                count += 1
        if count > 0:
            print(f"  ✓ {medium_file.name}: {count} translations")

# Load all HARD parts
for hard_file in sorted(DATA_DIR.glob("translate_HARD_part*.csv")):
    with open(hard_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            word = row['word']
            translation = row['translation'].strip()
            if translation:
                translations[word] = translation
                count += 1
        if count > 0:
            print(f"  ✓ {hard_file.name}: {count} translations")

print(f"\n📊 Total translations loaded: {len(translations)}")

if not translations:
    print("❌ No translations found. Fill the CSV files first!")
    exit(1)

print("\nLoading words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

# Apply translations
applied_count = 0
for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    for word_obj in alias_data[difficulty]:
        word = word_obj['word']
        if word in translations:
            word_obj['translation'] = translations[word]
            applied_count += 1

print(f"Applied {applied_count} translations")

# Backup
import shutil
backup_file = DATA_DIR / "words_alias_backup.json"
print(f"\nCreating backup: {backup_file}")
shutil.copy(DATA_DIR / "words_alias.json", backup_file)

# Save
print("Saving updated words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'w', encoding='utf-8') as f:
    json.dump(alias_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ SUCCESS!")
print(f"  • {len(translations)} unique words translated")
print(f"  • {applied_count} total translations applied")
print(f"  • Backup: {backup_file.name}")
print(f"\n🔄 Next: Restart backend")
print(f"  cd ~/projects/aliby && docker compose restart backend")
