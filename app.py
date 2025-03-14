from flask import *
import sqlite3
import random
from crossword import *
from wordSearchPuzzle import *

app = Flask(__name__)
app.secret_key = "crossword_secret_key"

@app.route('/crossword/<string:theme>')
def crossword(theme:str):
    if "grid" not in session or "placed_words" not in session or "word_directions" not in session:
        with sqlite3.connect('words.db') as con:
            cur = con.cursor()
            if theme == "all":
                cur.execute("SELECT word, def FROM words")
                words = [{'word': row[0], 'def': row[1]} for row in cur.fetchall()]
                print("all")
            else : 
                cur.execute("SELECT word, def FROM words WHERE theme=?", (theme,))
                words = [{'word': row[0], 'def': row[1]} for row in cur.fetchall()]
                print("other")
        grid, placed_words, word_directions = generate_crossword(words, theme, size=20)

        session["theme"] = theme
        session["grid"] = grid
        session["placed_words"] = placed_words
        session["word_directions"] = word_directions
    else:
        theme = session["theme"]
        grid = session["grid"]
        placed_words = session["placed_words"]
        word_directions = session["word_directions"]

    html_grid = generate_html(grid)

    definitions = get_def_from_db_C(placed_words,theme)

    definitions_h, definitions_v = {}, {}
    for index, word in enumerate(placed_words, start=1):
        if word in word_directions:
            if word_directions[word] == 'H':
                definitions_h[f"{index}."] = definitions.get(word, "Définition non trouvée")
            else:
                definitions_v[f"{index}."] = definitions.get(word, "Définition non trouvée")

    return render_template("crossword.html", crossword=html_grid, definitions_h=definitions_h, definitions_v=definitions_v)


@app.route('/validate', methods=['POST'])
def validate():
    if "grid" not in session or "placed_words" not in session or "word_directions" not in session or "theme" not in session:
        return redirect('/')

    grid = session["grid"]
    placed_words = session["placed_words"]
    word_directions = session["word_directions"]
    theme = session["theme"] 

    user_answers = {key: value for key, value in request.form.items()}

    all_correct = True
    feedback_grid = []

    for row in range(len(grid)):
        feedback_row = []
        for col in range(len(grid[row])):
            cell_value = grid[row][col]
            cell_id = f"cell_{row}_{col}"

            user_value = user_answers.get(cell_id, '')

            if cell_value != ' ' and not cell_value.isdigit():
                if user_value.isalpha():
                    if user_value.lower() == cell_value.lower():
                        feedback_row.append('correct')
                    else:
                        feedback_row.append('incorrect')
                        all_correct = False
                else:
                    feedback_row.append('incorrect')
                    all_correct = False
            else:
                feedback_row.append('')

        feedback_grid.append(feedback_row)

    if all_correct:
        message = "<h2 style='color: green;'>Congratulations! All answers are correct 🎉</h2>"
        show_new_grid_button = True
    else:
        message = "<h2 style='color: red;'>Some answers are incorrect. Try again!</h2>"
        show_new_grid_button = False

    html_grid = generate_html(grid, user_answers, feedback_grid) if not all_correct else ""

    definitions = get_def_from_db(placed_words, theme) 

    definitions_h, definitions_v = {}, {}
    for index, word in enumerate(placed_words, start=1):
        if word in word_directions:
            (definitions_h if word_directions[word] == 'H' else definitions_v)[f"{index}."] = definitions.get(word, "Definition not found")

    return render_template(
        "crossword.html",
        crossword=html_grid,
        message=message,
        definitions_h=definitions_h,
        definitions_v=definitions_v,
        show_new_grid_button=show_new_grid_button
    )

@app.route('/new_grid')
def new_grid():
    session.pop("grid", None)
    session.pop("placed_words", None)
    session.pop("word_directions", None)
    return redirect('/')

@app.route('/theme')
def choix_theme():
    session.pop("grid", None)
    session.pop("placed_words", None)
    session.pop("word_directions", None)
    con = sqlite3.connect('words.db')
    cur = con.cursor()
    themes = []
    for row in cur.execute('SELECT DISTINCT theme FROM words;'):
        themes.append(row[0])
    return render_template('theme.html',themes=themes)

@app.route('/word_search_puzzle')
def word_search_puzzle():
    if "word_search_grid" not in session or "word_search_words" not in session:
        words = get_words_from_db()
        grid, placed_words = generate_word_search(words, size=15)

        session["word_search_grid"] = grid
        session["word_search_words"] = placed_words
    else:
        grid = session["word_search_grid"]
        placed_words = session["word_search_words"]

    definitions = get_def_from_db_WSP(placed_words)
    html_grid = generate_word_search_html(grid, placed_words)
    return render_template("wordSearch.html", mot_mele=html_grid, definitions=definitions)

@app.route('/new_word_search_puzzle')
def new_word_search_puzzle():
    session.pop("word_search_grid", None)
    session.pop("word_search_words", None)
    return redirect('/word_search_puzzle')

@app.route('/')
def menu():
    return render_template('menu.html')

if __name__ == "__main__":
    app.run(debug=True)
