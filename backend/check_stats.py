#!/usr/bin/env python3
import json

with open('app/data/words_alias.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

easy_count = len(data['easy'])
medium_count = len(data['medium'])
hard_count = len(data['hard'])

easy_trans = sum(1 for w in data['easy'] if w.get('translation', ''))
med_trans = sum(1 for w in data['medium'] if w.get('translation', ''))
hard_trans = sum(1 for w in data['hard'] if w.get('translation', ''))

print(f"📊 Statistics:")
print(f"Easy: {easy_count} words ({easy_trans} translated, {easy_trans/easy_count*100:.1f}%)")
print(f"Medium: {medium_count} words ({med_trans} translated, {med_trans/medium_count*100:.1f}%)")
print(f"Hard: {hard_count} words ({hard_trans} translated, {hard_trans/hard_count*100:.1f}%)")
print(f"\nTotal: {easy_count + medium_count + hard_count} words")
print(f"Total translated: {easy_trans + med_trans + hard_trans}")

# Check specific words
test_words = ['fleck', 'debut', 'dove', 'cumbersome', 'evoke', 'deconstruct']
print(f"\n🔍 Test words:")
for word in test_words:
    found = False
    for cat in ['easy', 'medium', 'hard']:
        for w in data[cat]:
            if w['word'] == word:
                trans = w.get('translation', '')
                print(f"  {word}: {cat.upper()} (translation: {'YES' if trans else 'NO'})")
                found = True
                break
        if found:
            break
    if not found:
        print(f"  {word}: NOT FOUND")
