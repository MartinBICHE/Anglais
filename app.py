from flask import Flask, render_template
import sqlite3
import random

app = Flask(__name__)

def create_empty_grid(size):
    return [[' ' for _ in range(size)] for _ in range(size)]

def is_valid_position_for_word(grid, word, row, col, direction, crossing_positions):
    size = len(grid)

    for i in range(len(word)):
        if direction == 'H':
            current_pos = (row, col + i)

            if current_pos not in crossing_positions:
                # Vérifier les voisins au-dessus et en-dessous
                if row - 1 >= 0 and grid[row - 1][col + i] != ' ':
                    print(1)
                    return False  # Voisin au-dessus
                if row + 1 < size and grid[row + 1][col + i] != ' ':
                    print(2)
                    return False  # Voisin en-dessous
        elif direction == 'V':
            current_pos = (row + i, col)

            if current_pos not in crossing_positions:
                # Vérifier les voisins à gauche et à droite
                if col - 1 >= 0 and grid[row + i][col - 1] != ' ':
                    print(5)
                    return False  # Voisin à gauche
                if col + 1 < size and grid[row + i][col + 1] != ' ':
                    print(6)
                    return False  # Voisin à droite

    return True

def find_valid_intersections(grid, word):
    intersections = []
    size = len(grid)

    for row in range(1, size - 1):
        for col in range(1, size - 1):
            if grid[row][col] in word:
                char_index = word.index(grid[row][col])
                
                # Vérifier la position horizontale possible
                start_col = col - char_index
                if start_col > 0 and start_col + len(word) < size - 1:
                    crossing_positions = []
                    if all(grid[row][start_col + i] in (' ', word[i]) for i in range(len(word))):
                        if grid[row][start_col - 1] == ' ' and grid[row][start_col + len(word)] == ' ':
                            for i in range(len(word)):
                                if grid[row][start_col + i] == word[i]:
                                    crossing_positions.append((row, start_col + i))
                            intersections.append((row, start_col, 'H', crossing_positions))

                # Vérifier la position verticale possible
                start_row = row - char_index
                if start_row > 0 and start_row + len(word) < size - 1:
                    crossing_positions = []
                    if all(grid[start_row + i][col] in (' ', word[i]) for i in range(len(word))):
                        if grid[start_row - 1][col] == ' ' and grid[start_row + len(word)][col] == ' ':
                            for i in range(len(word)):
                                if grid[start_row + i][col] == word[i]:
                                    crossing_positions.append((start_row + i, col))
                            intersections.append((start_row, col, 'V', crossing_positions))

    return intersections

def place_word_with_number(grid, word, row, col, direction, number):
    """Place un mot dans la grille avec un numéro à la première case."""
    if direction == 'H':
        # Placer le mot horizontalement
        grid[row][col - 1] = str(number)
        for i in range(len(word)):
            grid[row][col + i] = word[i]
    else:
        # Placer le mot verticalement
        grid[row - 1][col] = str(number)
        for i in range(len(word)):
            grid[row + i][col] = word[i]

def generate_crossword(words, size=10):
    grid = create_empty_grid(size)
    placed_words = []
    word_directions = {}
    word_count = 1  # Compteur pour l'ordre des mots
    
    # Mélanger les mots à chaque exécution
    random.shuffle(words)
    
    # Trouver un mot avec au moins 6 lettres
    first_word = None
    for word_data in words:
        if len(word_data['word']) >= 6:
            first_word = words.pop(words.index(word_data))  # Retirer le mot de la liste
            break
    
    if not first_word:
        return grid, placed_words, word_directions  # Si aucun mot de 6 lettres n'est trouvé, retourne une grille vide
    
    first_word_length = len(first_word['word'])
    
    # Choisir aléatoirement entre horizontal (H) ou vertical (V)
    direction = random.choice(['H', 'V'])
    
    # Calculer la position de départ en fonction de l'orientation
    if direction == 'H':
        start_col = (size - first_word_length) // 2  # Positionnement centré horizontalement
        row, col = size // 2, start_col
    else:
        start_row = (size - first_word_length) // 2  # Positionnement centré verticalement
        row, col = start_row, size // 2

    # Vérifier si la position est valide avant de placer le mot
    if is_valid_position_for_word(grid, first_word['word'], row, col, direction, []):
        place_word_with_number(grid, first_word['word'], row, col, direction, word_count)
        placed_words.append(first_word['word'])
        word_directions[first_word['word']] = direction
        word_count += 1  # Incrémenter le compteur
    else:
        # Si la position n'est pas valide, on peut essayer une autre position ou ignorer ce mot
        pass  # Tu pourrais ici essayer une autre position aléatoire ou simplement ignorer ce mot

    # Pour les mots suivants, vérifie leur position avant de les placer
    for word_data in words:
        word = word_data['word']
        intersections = find_valid_intersections(grid, word)
        if intersections:
            # Vérifier les intersections disponibles et leur validité
            for row, col, direction, crossing_positions in intersections:
                if is_valid_position_for_word(grid, word, row, col, direction, crossing_positions):
                    place_word_with_number(grid, word, row, col, direction, word_count)
                    placed_words.append(word)
                    word_directions[word] = direction
                    word_count += 1  # Incrémenter le compteur
                    break  # On peut arrêter dès qu'un mot valide est placé
    
    return grid, placed_words, word_directions

def generate_html(grid):
    html = "<table style='border-collapse: collapse; text-align: center;'>"
    
    # Parcours de la grille pour ajouter les bordures
    for row in range(len(grid)):
        html += "<tr>"
        for col in range(len(grid[row])):
            cell = grid[row][col]
            # Ajouter une bordure si la case contient une lettre (non vide)
            if cell != ' ' and not cell.isdigit():
                html += f"<td style='width: 40px; height: 40px; font-size: 20px; border: 1px solid black; background-color: lightgray;'>{cell}</td>"
            elif cell.isdigit():  # Si la case contient un numéro, ne pas ajouter de bordure
                html += f"<td style='width: 40px; height: 40px; font-size: 20px; border: none;'>{cell}</td>"
            else:
                # Si la case est vide, ne pas ajouter de bordure
                html += f"<td style='width: 40px; height: 40px; font-size: 20px;'>{cell if cell != ' ' else '&nbsp;'}</td>"
        html += "</tr>"
    
    html += "</table>"
    return html

def get_def_from_db(placed_words):
    definitions = {}
    if placed_words:
        con = sqlite3.connect('crossword_words.db')
        cur = con.cursor()
        query = f"SELECT word, def FROM words WHERE word IN ({','.join(['?'] * len(placed_words))})"
        cur.execute(query, placed_words)
        definitions = {row[0]: row[1] for row in cur.fetchall()}
        con.close()
    
    return definitions

@app.route('/')
def crossword():
    con = sqlite3.connect('crossword_words.db')
    cur = con.cursor()
    cur.execute("SELECT word, def FROM words")
    words = [{'word': row[0], 'def': row[1]} for row in cur.fetchall()]
    con.close()
    
    grid, placed_words, word_directions = generate_crossword(words, size=20)
    html_grid = generate_html(grid)
    definitions = get_def_from_db(placed_words)
    
    definitions_h = {word: definitions[word] for word in placed_words if word in definitions and word_directions[word] == 'H'}
    definitions_v = {word: definitions[word] for word in placed_words if word in definitions and word_directions[word] == 'V'}
    
    return render_template("crossword.html", crossword=html_grid, definitions_h=definitions_h, definitions_v=definitions_v)

if __name__ == "__main__":
    app.run(debug=True)
