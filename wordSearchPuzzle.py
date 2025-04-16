import sqlite3
import random

def create_empty_grid(size):
    return [['#' for _ in range(size)] for _ in range(size)]

def can_place_word(grid, word, row, col, direction):
    size = len(grid)
    dx, dy = direction
    
    for i in range(len(word)):
        new_row, new_col = row + i * dx, col + i * dy
        if not (0 <= new_row < size and 0 <= new_col < size):
            return False
        if grid[new_row][new_col] not in ('#', word[i]):
            return False
    
    return True

def place_word(grid, word, row, col, direction):
    dx, dy = direction
    for i in range(len(word)):
        grid[row + i * dx][col + i * dy] = word[i]

def fill_remaining_spaces(grid):
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ- '
    for row in range(len(grid)):
        for col in range(len(grid[row])):
            if grid[row][col] == '#':
                grid[row][col] = random.choice(alphabet)

def generate_word_search(words, size=15):
    grid = create_empty_grid(size)
    directions = [(1, 0), (0, 1), (1, 1), (-1, 1), (1, -1), (-1, -1), (0, -1), (-1, 0)]
    random.shuffle(words)
    
    placed_words = []
    for word in words:
        random.shuffle(directions)
        for _ in range(100):
            row, col = random.randint(0, size - 1), random.randint(0, size - 1)
            direction = random.choice(directions)
            if can_place_word(grid, word, row, col, direction):
                place_word(grid, word, row, col, direction)
                placed_words.append(word)
                break
    
    fill_remaining_spaces(grid)  
    return grid, placed_words

def generate_word_search_html(grid, placed_words):
    html = "<table style='border-collapse: collapse;'>"
    for row in grid:
        html += "<tr>"
        for cell in row:
            html += f"<td style='width: 40px; height: 40px; text-align: center; border: 1px solid black;'>{cell}</td>"
        html += "</tr>"
    html += "</table><br>"
    return html

def get_words_from_db(theme):
    with sqlite3.connect('database.db') as con:
        cur = con.cursor()
        if theme == "all":
            cur.execute("SELECT word, definition FROM EnglishDatabase")
            words = [row[0].upper() for row in cur.fetchall()]
        else : 
            cur.execute("SELECT word, definition FROM EnglishDatabase WHERE theme=?", (theme,))
            words = [row[0].upper() for row in cur.fetchall()]
    con.close()
    return words

def get_def_from_db_WSP(placed_words):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    word_definitions = {} 
    
    for word in placed_words:
        for row in cur.execute('SELECT definition FROM EnglishDatabase WHERE word=?', (word.lower(),)):
            word_definitions[word] = row[0]  
    con.close()
    return word_definitions
