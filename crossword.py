import sqlite3
import random

def create_empty_grid(size):
    return [['#' for _ in range(size)] for _ in range(size)]

def is_valid_position_for_word(grid, word, row, col, direction, crossing_positions):
    size = len(grid)

    for i in range(len(word)):
        if direction == 'H':
            current_pos = (row, col + i)

            if current_pos not in crossing_positions:
                if row - 1 >= 0 and grid[row - 1][col + i] != '#':
                    return False 
                if row + 1 < size and grid[row + 1][col + i] != '#':
                    return False 
        elif direction == 'V':
            current_pos = (row + i, col)

            if current_pos not in crossing_positions:
                if col - 1 >= 0 and grid[row + i][col - 1] != '#':
                    return False
                if col + 1 < size and grid[row + i][col + 1] != '#':
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
                    if all(grid[row][start_col + i] in ('#', word[i]) for i in range(len(word))):
                        if grid[row][start_col - 1] == '#' and grid[row][start_col + len(word)] == '#':
                            for i in range(len(word)):
                                if grid[row][start_col + i] == word[i]:
                                    crossing_positions.append((row, start_col + i))
                            intersections.append((row, start_col, 'H', crossing_positions))

                start_row = row - char_index
                if start_row > 0 and start_row + len(word) < size - 1:
                    crossing_positions = []
                    if all(grid[start_row + i][col] in ('#', word[i]) for i in range(len(word))):
                        if grid[start_row - 1][col] == '#' and grid[start_row + len(word)][col] == '#':
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

def generate_crossword(words,theme, size=20):
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

    grid = clean_grid(grid)

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

            if cell == ' ':
                html += f"<td style='width: 40px; height: 40px; border: 1px solid black; background-color: lightgray;'>&nbsp;</td>"
            elif cell == '#':
                html += "<td style='width: 40px; height: 40px; border: none; background-color: transparent;'></td>"
            elif cell == '-':
                html += f"<td style='width: 40px; height: 40px; font-size: 20px; background-color: lightgray; border: 1px solid black;'>{cell}</td>"
            elif cell != ' ' and not cell.isdigit():
                html += f"<td style='width: 40px; height: 40px; font-size: 20px; border: 1px solid black; background-color: lightgray;'>" \
                        f"<input type='text' name='{cell_id}' maxlength='1' value='{user_value}' style='width: 30px; height: 30px; text-align: center; {color} font-size: 20px;' oninput='checkInputs()' />" \
                        f"</td>"
            elif cell.isdigit():
                html += f"<td style='width: 40px; height: 40px; font-size: 20px; border: none;'>{cell}</td>"
            else:
                html += f"<td style='width: 40px; height: 40px; font-size: 20px;'>{cell if cell != ' ' else '&nbsp;'}</td>"
        html += "</tr>"

    html += "</table>"
    html += "<button id='validateButton' disabled type='submit'>Validate</button>"
    html += "</form>"
    
    return html

def get_def_from_db_C(placed_words, theme):
    definitions = {}
    if placed_words:
        con = sqlite3.connect('database_final_real.db')
        cur = con.cursor()
        
        if theme != "all":
            query = f"SELECT word, definition FROM EnglishDatabase WHERE theme = ? AND word IN ({','.join(['?'] * len(placed_words))})"
            cur.execute(query, (theme, *placed_words))
        else:
            query = f"SELECT word, definition FROM EnglishDatabase WHERE word IN ({','.join(['?'] * len(placed_words))})"
            cur.execute(query, tuple(placed_words))

        definitions = {row[0]: row[1] for row in cur.fetchall()}
        con.close()
    
    return definitions



def clean_grid(grid):
    while grid and all(cell == ' ' for cell in grid[0]):
        grid.pop(0)

    if grid:
        empty_cols_left = set()
        empty_cols_right = set()

        for col in range(len(grid[0])):
            if all(row[col] == ' ' for row in grid):
                empty_cols_left.add(col)

        for col in range(len(grid[0]) - 1, -1, -1):
            if all(row[col] == ' ' for row in grid):
                empty_cols_right.add(col)

        grid = [
            [cell for col, cell in enumerate(row) if col not in empty_cols_left and col not in empty_cols_right]
            for row in grid
        ]

    while grid and all(cell == ' ' for cell in grid[-1]):
        grid.pop()

    return grid
