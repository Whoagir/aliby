#!/usr/bin/env python3
"""
Rebuild words_alias.json using ONLY user-translated words for Easy/Medium.
All other words go to Hard.
"""
import json
import pandas as pd
from pathlib import Path

# Paths
EASY_XLSX = Path("app/data/translate/easy.xlsx")
MEDIUM_XLSX = Path("app/data/translate/middle.xlsx")
OLD_JSON = Path("app/data/words_alias.json")
NEW_JSON = Path("app/data/words_alias_new.json")

def read_excel_translations(filepath):
    """Read Excel file and extract word->translation mapping"""
    print(f"\nReading {filepath}...")
    df = pd.read_excel(filepath)
    
    translations = {}
    
    for idx, row in df.iterrows():
        # Get first column value
        cell_value = str(row.iloc[0]).strip()
        
        # Check if it's "word,translation" format (single column)
        if ',' in cell_value:
            parts = cell_value.split(',', 1)
            if len(parts) == 2:
                word = parts[0].strip()
                translation = parts[1].strip()
            else:
                continue
        else:
            # Assume separate columns
            if len(row) >= 2:
                word = str(row.iloc[0]).strip()
                translation = str(row.iloc[1]).strip()
            else:
                continue
        
        # Validate
        if word and translation and word != 'nan' and translation != 'nan' and translation != '':
            translations[word.lower()] = translation
    
    print(f"Loaded {len(translations)} translations from {filepath.name}")
    return translations

def main():
    # Read user translations
    print("=" * 60)
    print("REBUILDING words_alias.json with user translations")
    print("=" * 60)
    
    easy_translations = read_excel_translations(EASY_XLSX)
    medium_translations = read_excel_translations(MEDIUM_XLSX)
    
    print(f"\n✅ Easy words: {len(easy_translations)}")
    print(f"✅ Medium words: {len(medium_translations)}")
    
    # Read old JSON to get ALL words
    with open(OLD_JSON, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    total_old = sum(len(old_data[cat]) for cat in ['easy', 'medium', 'hard'])
    print(f"\n📊 Old JSON total words: {total_old}")
    
    # Create sets for quick lookup
    easy_words_set = set(easy_translations.keys())
    medium_words_set = set(medium_translations.keys())
    translated_words_set = easy_words_set | medium_words_set
    
    # Build new structure
    new_data = {
        "easy": [],
        "medium": [],
        "hard": []
    }
    
    # Add Easy words (only from user's file)
    for word, translation in easy_translations.items():
        new_data["easy"].append({
            "word": word,
            "translation": translation
        })
    
    # Add Medium words (only from user's file)
    for word, translation in medium_translations.items():
        new_data["medium"].append({
            "word": word,
            "translation": translation
        })
    
    # Collect all words from old JSON that are NOT in user's translated lists
    hard_words_set = set()
    for category in ['easy', 'medium', 'hard']:
        for word_obj in old_data[category]:
            word_lower = word_obj['word'].lower()
            if word_lower not in translated_words_set:
                hard_words_set.add(word_lower)
    
    # Add all untranslated words to Hard
    for category in ['easy', 'medium', 'hard']:
        for word_obj in old_data[category]:
            word_lower = word_obj['word'].lower()
            if word_lower in hard_words_set:
                # Add to hard (only once)
                if not any(w['word'] == word_obj['word'] for w in new_data['hard']):
                    new_data['hard'].append({
                        "word": word_obj['word'],
                        "translation": word_obj.get('translation', '')
                    })
    
    print(f"\n📦 NEW JSON structure:")
    print(f"   Easy: {len(new_data['easy'])} words (100% translated)")
    print(f"   Medium: {len(new_data['medium'])} words (100% translated)")
    print(f"   Hard: {len(new_data['hard'])} words (not translated)")
    
    total_new = sum(len(new_data[cat]) for cat in ['easy', 'medium', 'hard'])
    print(f"   TOTAL: {total_new} words")
    
    # Save new JSON
    with open(NEW_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ New JSON saved to: {NEW_JSON}")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Review the new JSON file")
    print("2. Replace old JSON: mv words_alias_new.json words_alias.json")
    print("3. Restart backend container")
    print("=" * 60)

if __name__ == "__main__":
    main()
