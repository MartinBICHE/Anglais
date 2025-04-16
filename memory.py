import random
import sqlite3

def get_random_synonyms(theme):
    conn = sqlite3.connect('database_final_real.db')
    cursor = conn.cursor()
    
    if theme == "all":
        cursor.execute("""
            SELECT id, word, synonym 
            FROM EnglishDatabase 
            WHERE synonym IS NOT NULL AND synonym != '' 
            ORDER BY RANDOM() 
            LIMIT 18
        """)
    else:
        cursor.execute("""
            SELECT id, word, synonym 
            FROM EnglishDatabase 
            WHERE theme=? AND synonym IS NOT NULL AND synonym != '' 
            ORDER BY RANDOM() 
            LIMIT 18
        """, (theme,))
    
    pairs = cursor.fetchall()
    conn.close()

    cards = []
    for pair_id, word, synonym in pairs:
        if '/' in synonym:
            synonym_options = [s.strip() for s in synonym.split('/')]
            synonym = random.choice(synonym_options)
        
        cards.append({'word': word, 'pair_id': pair_id, 'type': 'word'})
        cards.append({'word': synonym, 'pair_id': pair_id, 'type': 'synonym'})
    
    random.shuffle(cards)
    return cards
