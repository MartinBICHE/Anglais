import sqlite3
from flask import *

def get_crossword_stats(user_id=None):
    con = sqlite3.connect('database.db')
    cur = con.cursor()

    # Global stats
    if user_id:
        cur.execute('''
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as wins,
                MIN(attempts),
                MAX(attempts),
                ROUND(AVG(attempts), 2)
            FROM crossword_stats
            WHERE user_id = ?
        ''', (user_id,))
    else:
        cur.execute('''
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as wins,
                MIN(attempts),
                MAX(attempts),
                ROUND(AVG(attempts), 2)
            FROM crossword_stats
        ''')
    global_stats = cur.fetchone()

    # Stats by theme
    if user_id:
        cur.execute('''
            SELECT theme, COUNT(*) as total, 
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as wins,
                   ROUND(AVG(attempts), 2)
            FROM crossword_stats
            WHERE user_id = ?
            GROUP BY theme
        ''', (user_id,))
    else:
        cur.execute('''
            SELECT theme, COUNT(*) as total, 
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as wins,
                   ROUND(AVG(attempts), 2)
            FROM crossword_stats
            GROUP BY theme
        ''')
    theme_stats = cur.fetchall()

    con.close()

    return {
        "global": global_stats,
        "by_theme": theme_stats
    }

def get_word_search_stats(user_id):
    con = sqlite3.connect('database.db')
    cur = con.cursor()

    # --- Stats globales (somme sur tous les thèmes) ---
    cur.execute('''
        SELECT 
            SUM(grid_attempted)    AS total_attempted,
            SUM(grid_successful)   AS total_successful,
            MIN(time_min)          AS time_min,
            MAX(time_max)          AS time_max,
            ROUND(AVG(time_avg),2) AS time_avg
        FROM word_search_stats
        WHERE user_id = ?
    ''', (user_id,))
    global_stats = cur.fetchone()

    # --- Stats par thème ---
    cur.execute('''
        SELECT 
            theme,
            grid_attempted,
            grid_successful,
            time_min,
            time_max,
            time_avg
        FROM word_search_stats
        WHERE user_id = ?
    ''', (user_id,))
    theme_stats = cur.fetchall()

    con.close()
    return {
        "global": global_stats,
        "by_theme": theme_stats
    }

def get_memory_stats(user_id):
    con = sqlite3.connect('database.db')
    cur = con.cursor()

    # Statistiques globales
    cur.execute('''
        SELECT
            SUM(total_games),
            SUM(victories),
            MIN(CASE WHEN victories > 0 THEN min_attempts ELSE NULL END),
            MAX(max_attempts),
            SUM(total_attempts),
            NULL -- on recalculera avg_attempts manuellement
        FROM memory_stats
        WHERE user_id = ?
    ''', (user_id,))
    global_stats = cur.fetchone()

    # Recalcul de la moyenne sur les parties gagnées
    if global_stats[1] and global_stats[1] > 0:
        avg_attempts_global = global_stats[4] / global_stats[1]
    else:
        avg_attempts_global = None

    # Statistiques par thème
    cur.execute('''
        SELECT
            theme,
            total_games,
            victories,
            min_attempts,
            max_attempts,
            total_attempts
        FROM memory_stats
        WHERE user_id = ?
    ''', (user_id,))
    raw_theme_stats = cur.fetchall()
    con.close()

    theme_stats = []
    for row in raw_theme_stats:
        theme, total_games, victories, min_attempts, max_attempts, total_attempts = row
        if victories > 0:
            avg_attempts = total_attempts / victories
        else:
            avg_attempts = None
        theme_stats.append([
            theme,
            total_games,
            victories,
            min_attempts,
            max_attempts,
            total_attempts,
            avg_attempts
        ])

    # Valeurs par défaut si aucune stat globale
    if not global_stats or global_stats[0] is None:
        global_stats = [0, 0, None, None, 0, None]
        avg_attempts_global = None

    # Retourner les données au template
    return {
        "global": [
            global_stats[0],  # total_played
            global_stats[1],  # total_won
            global_stats[2],  # min_attempts
            global_stats[3],  # max_attempts
            global_stats[4],  # total_attempts
            avg_attempts_global
        ],
        "by_theme": theme_stats
    }
