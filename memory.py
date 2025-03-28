import random
import sqlite3

def get_random_synonyms():
    conn = sqlite3.connect('memory_test.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, word, synonym FROM synonyms ORDER BY RANDOM() LIMIT 18")
    pairs = cursor.fetchall()
    conn.close()
    
    cards = []
    for pair_id, word, synonym in pairs:
        cards.append({'word': word, 'pair_id': pair_id, 'type': 'word'})
        cards.append({'word': synonym, 'pair_id': pair_id, 'type': 'synonym'})
    
    random.shuffle(cards)
    return cards