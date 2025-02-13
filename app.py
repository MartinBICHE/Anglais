from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "crossword_secret_key"

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
                    return False  # Voisin au-dessus
                if row + 1 < size and grid[row + 1][col + i] != ' ':
                    return False  # Voisin en-dessous
        elif direction == 'V':
            current_pos = (row + i, col)

            if current_pos not in crossing_positions:
                # Vérifier les voisins à gauche et à droite
                if col - 1 >= 0 and grid[row + i][col - 1] != ' ':
                    return False  # Voisin à gauche
                if col + 1 < size and grid[row + i][col + 1] != ' ':
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

def generate_html(grid, user_answers=None, feedback_grid=None):
    html = """
    <script>
        function checkInputs() {
            let inputs = document.querySelectorAll("input[type='text']");
            let button = document.getElementById("validateButton");
            let allFilled = true;

            inputs.forEach(input => {
                if (input.value.trim() === "") {
                    allFilled = false;
                }
            });

            button.disabled = !allFilled;
        }

        document.addEventListener("DOMContentLoaded", function() {
            let inputs = document.querySelectorAll("input[type='text']");
            inputs.forEach(input => {
                input.addEventListener("input", checkInputs);
            });
        });
    </script>
    """

    html += "<form method='post' action='/validate'>"
    html += "<table style='border-collapse: collapse; text-align: center;'>"

    for row in range(len(grid)):
        html += "<tr>"
        for col in range(len(grid[row])):
            cell = grid[row][col]
            cell_id = f"cell_{row}_{col}"  # Identifiant unique pour chaque case
            
            # Si des réponses utilisateur sont fournies, on les utilise
            user_value = user_answers.get(cell_id, '') if user_answers else ''
            color = ''
            
            # Appliquer les couleurs de feedback pour les bonnes/mauvaises réponses
            if feedback_grid and feedback_grid[row][col] == 'correct':
                color = 'background-color: lightgreen;'  # Bonne réponse
            elif feedback_grid and feedback_grid[row][col] == 'incorrect':
                color = 'background-color: lightcoral;'  # Mauvaise réponse

            # Si ce n'est pas une case vide ou un numéro
            if cell != ' ' and not cell.isdigit():
                html += f"<td style='width: 40px; height: 40px; font-size: 20px; border: 1px solid black; background-color: lightgray;'>" \
                        f"<input type='text' name='{cell_id}' maxlength='1' value='{user_value}' style='width: 30px; height: 30px; text-align: center; {color}' oninput='checkInputs()' />" \
                        f"</td>"
            elif cell.isdigit():
                html += f"<td style='width: 40px; height: 40px; font-size: 20px; border: none;'>{cell}</td>"
            else:
                html += f"<td style='width: 40px; height: 40px; font-size: 20px;'>{cell if cell != ' ' else '&nbsp;'}</td>"
        html += "</tr>"

    html += "</table>"
    html += "<button id='validateButton' disabled type='submit'>Valider</button>"
    html += "</form>"
    
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
    # Vérifier si une grille existe déjà en session
    if "grid" in session and "placed_words" in session and "word_directions" in session:
        grid = session["grid"]
        placed_words = session["placed_words"]
        word_directions = session["word_directions"]
    else:
        # Récupérer les mots depuis la base de données
        with sqlite3.connect('crossword_words.db') as con:
            cur = con.cursor()
            cur.execute("SELECT word, def FROM words")
            words = [{'word': row[0], 'def': row[1]} for row in cur.fetchall()]

        # Générer une nouvelle grille
        grid, placed_words, word_directions = generate_crossword(words, size=20)

        # Stocker la grille en session
        session["grid"] = grid
        session["placed_words"] = placed_words
        session["word_directions"] = word_directions

    # Générer le HTML de la grille
    html_grid = generate_html(grid)

    # Récupérer les définitions des mots placés
    definitions = get_def_from_db(placed_words)

    # Trier les définitions par orientation
    definitions_h, definitions_v = {}, {}
    for index, word in enumerate(placed_words, start=1):
        if word in word_directions:
            (definitions_h if word_directions[word] == 'H' else definitions_v)[f"{index}."] = definitions.get(word, "Définition non trouvée")

    return render_template("crossword.html", crossword=html_grid, definitions_h=definitions_h, definitions_v=definitions_v)

@app.route('/validate', methods=['POST'])
def validate():
    # Vérifier si la grille existe déjà en session
    if "grid" not in session or "placed_words" not in session or "word_directions" not in session:
        return redirect('/')  # Si la grille n'existe pas, rediriger vers la création

    grid = session["grid"]
    placed_words = session["placed_words"]
    word_directions = session["word_directions"]

    # Récupérer les réponses utilisateur en majuscules
    user_answers = {key: value for key, value in request.form.items()}
    print(user_answers)

    # Vérifier si toutes les réponses sont correctes
    all_correct = True
    feedback_grid = []  # Cette grille contiendra les couleurs à appliquer
    compteur = 0  # Initialisation du compteur pour suivre l'index des réponses utilisateur

    for row in range(len(grid)):
        feedback_row = []  # Liste pour stocker les résultats de chaque ligne
        for col in range(len(grid[row])):
            cell_value = grid[row][col]
            cell_id = f"cell_{row}_{col}"  # Identifiant de chaque case input

            # Vérification de l'entrée utilisateur pour cette case
            user_value = user_answers.get(cell_id, '')

            if cell_value != ' ' and not cell_value.isdigit():  # Si c'est une case à remplir (pas un numéro)
                if user_value.isalpha():  # Si l'entrée est une lettre
                    if user_value == cell_value:
                        feedback_row.append('correct')  # Bonne réponse
                    else:
                        feedback_row.append('incorrect')  # Mauvaise réponse
                        all_correct = False
                else:
                    feedback_row.append('incorrect')  # Si ce n'est pas une lettre, on considère une mauvaise réponse
                    all_correct = False
            else:
                feedback_row.append('')  # Case vide ou numéro, on ne fait rien ici

            compteur += 1  # Incrémentation du compteur pour passer à la case suivante

        feedback_grid.append(feedback_row)  # Ajouter la ligne de feedback à la grille

    # Message de feedback
    if all_correct:
        message = "<h2 style='color: green;'>Bravo ! Toutes les réponses sont correctes 🎉</h2>"
    else:
        message = "<h2 style='color: red;'>Certaines réponses sont incorrectes. Essayez encore !</h2>"

    # Générer une grille avec couleurs (correct ou incorrect)
    html_grid = generate_html(grid, user_answers, feedback_grid)

    # Récupérer les définitions des mots placés
    definitions = get_def_from_db(placed_words)

    # Trier les définitions par orientation
    definitions_h, definitions_v = {}, {}
    for index, word in enumerate(placed_words, start=1):
        if word in word_directions:
            (definitions_h if word_directions[word] == 'H' else definitions_v)[f"{index}."] = definitions.get(word, "Définition non trouvée")

    return render_template("crossword.html", crossword=html_grid, message=message, definitions_h=definitions_h, definitions_v=definitions_v)

if __name__ == "__main__":
    app.run(debug=True)
