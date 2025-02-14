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
                if row - 1 >= 0 and grid[row - 1][col + i] != ' ':
                    return False 
                if row + 1 < size and grid[row + 1][col + i] != ' ':
                    return False 
        elif direction == 'V':
            current_pos = (row + i, col)

            if current_pos not in crossing_positions:
                if col - 1 >= 0 and grid[row + i][col - 1] != ' ':
                    return False
                if col + 1 < size and grid[row + i][col + 1] != ' ':
                    return False 

    return True

def find_valid_intersections(grid, word):
    intersections = []
    size = len(grid)

    for row in range(1, size - 1):
        for col in range(1, size - 1):
            if grid[row][col] in word:
                char_index = word.index(grid[row][col])
                
                start_col = col - char_index
                if start_col > 0 and start_col + len(word) < size - 1:
                    crossing_positions = []
                    if all(grid[row][start_col + i] in (' ', word[i]) for i in range(len(word))):
                        if grid[row][start_col - 1] == ' ' and grid[row][start_col + len(word)] == ' ':
                            for i in range(len(word)):
                                if grid[row][start_col + i] == word[i]:
                                    crossing_positions.append((row, start_col + i))
                            intersections.append((row, start_col, 'H', crossing_positions))

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
        grid[row][col - 1] = str(number)
        for i in range(len(word)):
            grid[row][col + i] = word[i]
    else:
        grid[row - 1][col] = str(number)
        for i in range(len(word)):
            grid[row + i][col] = word[i]

def generate_crossword(words, size=10):
    grid = create_empty_grid(size)
    placed_words = []
    word_directions = {}
    word_count = 1 
    
    random.shuffle(words)
    
    first_word = None
    for word_data in words:
        if len(word_data['word']) >= 6:
            first_word = words.pop(words.index(word_data)) 
            break
    
    if not first_word:
        return grid, placed_words, word_directions
    
    first_word_length = len(first_word['word'])
    
    direction = random.choice(['H', 'V'])
    
    if direction == 'H':
        start_col = (size - first_word_length) // 2
        row, col = size // 2, start_col
    else:
        start_row = (size - first_word_length) // 2
        row, col = start_row, size // 2

    if is_valid_position_for_word(grid, first_word['word'], row, col, direction, []):
        place_word_with_number(grid, first_word['word'], row, col, direction, word_count)
        placed_words.append(first_word['word'])
        word_directions[first_word['word']] = direction
        word_count += 1
    else:
        pass

    for word_data in words:
        word = word_data['word']
        intersections = find_valid_intersections(grid, word)
        if intersections:
            for row, col, direction, crossing_positions in intersections:
                if is_valid_position_for_word(grid, word, row, col, direction, crossing_positions):
                    place_word_with_number(grid, word, row, col, direction, word_count)
                    placed_words.append(word)
                    word_directions[word] = direction
                    word_count += 1
                    break
    
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
            cell_id = f"cell_{row}_{col}"
            
            user_value = user_answers.get(cell_id, '') if user_answers else ''
            color = ''
            
            if feedback_grid and feedback_grid[row][col] == 'correct':
                color = 'background-color: lightgreen;'
            elif feedback_grid and feedback_grid[row][col] == 'incorrect':
                color = 'background-color: lightcoral;'

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
    if "grid" in session and "placed_words" in session and "word_directions" in session:
        grid = session["grid"]
        placed_words = session["placed_words"]
        word_directions = session["word_directions"]
    else:
        with sqlite3.connect('crossword_words.db') as con:
            cur = con.cursor()
            cur.execute("SELECT word, def FROM words")
            words = [{'word': row[0], 'def': row[1]} for row in cur.fetchall()]

        grid, placed_words, word_directions = generate_crossword(words, size=20)

        session["grid"] = grid
        session["placed_words"] = placed_words
        session["word_directions"] = word_directions

    html_grid = generate_html(grid)

    definitions = get_def_from_db(placed_words)

    definitions_h, definitions_v = {}, {}
    for index, word in enumerate(placed_words, start=1):
        if word in word_directions:
            (definitions_h if word_directions[word] == 'H' else definitions_v)[f"{index}."] = definitions.get(word, "Définition non trouvée")

    return render_template("crossword.html", crossword=html_grid, definitions_h=definitions_h, definitions_v=definitions_v)

@app.route('/validate', methods=['POST'])
def validate():
    if "grid" not in session or "placed_words" not in session or "word_directions" not in session:
        return redirect('/')

    grid = session["grid"]
    placed_words = session["placed_words"]
    word_directions = session["word_directions"]

    user_answers = {key: value for key, value in request.form.items()}
    print(user_answers)

    all_correct = True
    feedback_grid = []
    compteur = 0

    for row in range(len(grid)):
        feedback_row = []
        for col in range(len(grid[row])):
            cell_value = grid[row][col]
            cell_id = f"cell_{row}_{col}"

            user_value = user_answers.get(cell_id, '')

            if cell_value != ' ' and not cell_value.isdigit():
                if user_value.isalpha():
                    if user_value == cell_value:
                        feedback_row.append('correct')
                    else:
                        feedback_row.append('incorrect')
                        all_correct = False
                else:
                    feedback_row.append('incorrect')
                    all_correct = False
            else:
                feedback_row.append('')

            compteur += 1

        feedback_grid.append(feedback_row)  

    if all_correct:
        message = "<h2 style='color: green;'>Bravo ! Toutes les réponses sont correctes 🎉</h2>"
    else:
        message = "<h2 style='color: red;'>Certaines réponses sont incorrectes. Essayez encore !</h2>"

    html_grid = generate_html(grid, user_answers, feedback_grid)

    definitions = get_def_from_db(placed_words)

    definitions_h, definitions_v = {}, {}
    for index, word in enumerate(placed_words, start=1):
        if word in word_directions:
            (definitions_h if word_directions[word] == 'H' else definitions_v)[f"{index}."] = definitions.get(word, "Définition non trouvée")

    return render_template("crossword.html", crossword=html_grid, message=message, definitions_h=definitions_h, definitions_v=definitions_v)

if __name__ == "__main__":
    app.run(debug=True)
