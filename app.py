from flask import *
import sqlite3
import random
from flask_login import *
from flask_bcrypt import *
from crossword import *
from wordSearchPuzzle import *
from memory import *
from statistiques import *

app = Flask(__name__)
app.config['SECRET_KEY'] = "MySuperSecretKey"
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get_user_by_username(username):
        conn = sqlite3.connect('database.db')
        user_data = conn.execute('''
            SELECT id, username, password FROM users WHERE username=?''',
            (username,)).fetchone()
        conn.close()
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        return None

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, username, password FROM users WHERE id = ?", (user_id,))
    user_data = cur.fetchone()
    conn.close()
    if user_data:
        return User(*user_data)
    return None

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = sqlite3.connect('database.db')
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()

            cur = conn.cursor()
            cur.execute('SELECT id FROM users WHERE username = ?', (username,))
            user_id = cur.fetchone()[0]
            session['user_id'] = user_id 
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("menu.html", isauth=False, usernameExists=True)
        conn.close()
        return redirect('/')
    return render_template("menu.html", isauth=False)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_user_by_username(username)
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)

            session['user_id'] = user.id

            return redirect('/')
        else:
            return render_template('menu.html', isauth=False, badCredentials=True)
    return render_template('menu.html', isauth=False)

@app.route('/profile/')
@login_required
def profile():
    user_id = session.get('user_id')
    
    cw_stats = get_crossword_stats(user_id)
    wsp_stats = get_word_search_stats(user_id)
    memory_stats = get_memory_stats(user_id)
    ftb_stats = get_fill_the_blanks_stats(user_id)

    return render_template(
        "profile.html",
        username=current_user.username,
        stats=cw_stats,
        wsp_stats=wsp_stats,
        memory_stats=memory_stats,
        ftb_stats=ftb_stats,
        user_id=user_id
    )

@app.route('/logout/', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/footer/', methods=['GET'])
def footer():
    return render_template("footer.html")

@app.route('/crossword/<string:theme>')
def crossword(theme:str):
    if "grid" not in session or "placed_words" not in session or "word_directions" not in session:
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            if theme == "all":
                cur.execute("SELECT word, definition FROM EnglishDatabase")
                words = [{'word': row[0], 'def': row[1]} for row in cur.fetchall()]
            else : 
                cur.execute("SELECT word, definition FROM EnglishDatabase WHERE theme=?", (theme,))
                words = [{'word': row[0], 'def': row[1]} for row in cur.fetchall()]
        grid, placed_words, word_directions = generate_crossword(words, theme, size=20)

        session["theme"] = theme
        session["grid"] = grid
        session["placed_words"] = placed_words
        session["word_directions"] = word_directions

        user_id = session.get('user_id')  
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute('''
            INSERT INTO crossword_stats (user_id, theme, success, attempts)
            VALUES (?, ?, NULL, 0)
        ''', (user_id, theme))
        session['current_game_id'] = cur.lastrowid  
        con.commit()
        con.close()
    else:
        theme = session["theme"]
        grid = session["grid"]
        placed_words = session["placed_words"]
        word_directions = session["word_directions"]

        user_id = session.get('user_id') 
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute('''
            INSERT INTO crossword_stats (user_id, theme, success, attempts)
            VALUES (?, ?, NULL, 0)
        ''', (user_id, theme))
        session['current_game_id'] = cur.lastrowid
        con.commit()
        con.close()

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
    session['attempts'] = session.get('attempts', 0) + 1

    user_answers = {key: value for key, value in request.form.items()}

    all_correct = True
    feedback_grid = []

    for row in range(len(grid)):
        feedback_row = []
        for col in range(len(grid[row])):
            cell_value = grid[row][col]
            cell_id = f"cell_{row}_{col}"
            user_value = user_answers.get(cell_id, '').strip()

            if cell_value.isalpha():
                if user_value.lower() == cell_value.lower():
                    feedback_row.append('correct')
                else:
                    feedback_row.append('incorrect')
                    all_correct = False
            else:
                feedback_row.append('')
        feedback_row.append('')
        feedback_grid.append(feedback_row)

    if all_correct:
        flash("Congratulations! You solved the crossword!")
    else:
        flash("There are still some errors, try again.")


    game_id = session.get('current_game_id')
    user_id = session.get('user_id') or None
    attempts = session.get('attempts', 1)
    success = all_correct 

    if game_id:
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute('''
            UPDATE crossword_stats
            SET success = ?, attempts = ?
            WHERE id = ?
        ''', (success, attempts, game_id))
        con.commit()
        con.close()

    html_grid = generate_html(grid, user_answers, feedback_grid)

    definitions = get_def_from_db_C(placed_words, theme) 
    definitions_h, definitions_v = {}, {}

    for index, word in enumerate(placed_words, start=1):
        if word in word_directions:
            (definitions_h if word_directions[word] == 'H' else definitions_v)[f"{index}."] = definitions.get(word, "Definition not found")

    
    return render_template(
        "crossword.html",
        crossword=html_grid,
        definitions_h=definitions_h,
        definitions_v=definitions_v,
    )


@app.route('/new_grid')
def new_grid():
    session['attempts'] = 0
    session.pop("grid", None)
    session.pop("placed_words", None)
    session.pop("word_directions", None)
    return redirect('/')

@app.route('/theme')
def choix_theme():
    session.pop("grid", None)
    session.pop("placed_words", None)
    session.pop("word_directions", None)
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    themes = []
    for row in cur.execute('SELECT DISTINCT theme FROM EnglishDatabase;'):
        themes.append(row[0])
    return render_template('theme.html',themes=themes)

@app.route('/word_search_puzzle/<string:theme>')
def word_search_puzzle(theme: str):
    is_new = False
    if "word_search_grid" not in session or "word_search_words" not in session:
        is_new = True
        words = get_words_from_db(theme)
        grid, placed_words = generate_word_search(words, size=15)

        user_id = session.get('user_id')
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute('''
            SELECT id, grid_attempted 
              FROM word_search_stats 
             WHERE user_id = ? AND theme = ?
        ''', (user_id, theme))
        row = cur.fetchone()

        if row:
            stat_id, attempted = row
            cur.execute('''
                UPDATE word_search_stats
                   SET grid_attempted = ?
                 WHERE id = ?
            ''', (attempted + 1, stat_id))
        else:
            cur.execute('''
                INSERT INTO word_search_stats
                    (user_id, theme, grid_attempted, grid_successful, time_min, time_max, time_avg)
                VALUES (?, ?, 1, 0, NULL, NULL, NULL)
            ''', (user_id, theme))

        con.commit()
        con.close()

        session["word_search_grid"] = grid
        session["word_search_words"] = placed_words
    else:
        is_new = True
        grid = session["word_search_grid"]
        placed_words = session["word_search_words"]

    definitions = get_def_from_db_WSP(placed_words)
    html_grid = generate_word_search_html(grid, placed_words)
    
    return render_template("wordSearch.html", mot_mele=html_grid, definitions=definitions, theme=theme)

@app.route('/new_word_search_puzzle')
def new_word_search_puzzle():
    session.pop("word_search_grid", None)
    session.pop("word_search_words", None)
    return redirect('/theme')

@app.route('/clear_word_search_session', methods=['POST'])
def clear_word_search_session():
    session.pop("word_search_grid", None)
    session.pop("word_search_words", None)
    return '', 204 

@app.route('/', methods=['GET'])
def menu():
    if current_user.is_authenticated:
        return render_template("menu.html", current_user=current_user, isauth=True)
    else:
        return render_template("menu.html", current_user=current_user, isauth=False)

@app.route('/get_cards/<string:theme>')
def get_cards(theme:str):
    cards = get_random_synonyms(theme)
    return jsonify(cards)

@app.route('/memory/<string:theme>')
def memory(theme: str):
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))
    
    con = sqlite3.connect('database.db')
    cur = con.cursor()

    cur.execute('''
        SELECT user_id, theme FROM memory_stats WHERE user_id = ? AND theme = ?
    ''', (user_id, theme))
    row = cur.fetchone()

    if row:
        cur.execute('''
            UPDATE memory_stats
            SET total_games = total_games + 1
            WHERE user_id = ? AND theme = ?
        ''', (user_id, theme))
    else:
        cur.execute('''
            INSERT INTO memory_stats (
                user_id, theme, total_games, victories, 
                min_attempts, max_attempts, total_attempts, avg_attempts
            ) VALUES (?, ?, 1, 0, NULL, NULL, 0, NULL)
        ''', (user_id, theme))

    con.commit()
    con.close()

    return render_template('memory.html', theme=theme, user_id=user_id)

@app.route('/flashcards/<theme>')
def show_flashcards(theme):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    if theme == "all":
        cur.execute('SELECT word, definition FROM EnglishDatabase ORDER BY RANDOM()')
    else:
        cur.execute('SELECT word, definition FROM EnglishDatabase WHERE theme = ? ORDER BY RANDOM()', (theme,))
    
    cards = cur.fetchall()
    conn.close()
    return render_template('flashcards.html', theme=theme, cards=cards)

@app.route('/fill_the_blanks/<theme>')
def start_game(theme):
    session['theme'] = theme
    session['current_questionftb'] = 0
    session['correct'] = 0
    session['incorrect'] = 0
    session['history'] = []  
    session['used_sentences'] = [] 

    return redirect(url_for('next_questionftb'))

@app.route('/next_questionftb')
def next_questionftb():
    theme = session.get('theme')
    current_q = session.get('current_questionftb', 0)
    used_sentences = session.get('used_sentences', [])

    if current_q >= 10:
        return redirect(url_for('resultsftb'))

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    placeholders = ','.join('?' for _ in used_sentences)
    query = f'''
        SELECT sentence, answer 
        FROM sentences 
        WHERE theme = ? 
        {'AND sentence NOT IN ({})'.format(placeholders) if used_sentences else ''} 
        ORDER BY RANDOM() 
        LIMIT 1
    '''

    params = [theme] + used_sentences if used_sentences else [theme]
    cur.execute(query, params)
    row = cur.fetchone()

    if not row:
        return "No more unique questions available for this theme."

    sentence, correct_answer = row

    cur.execute('''
        SELECT word 
        FROM EnglishDatabase 
        WHERE theme = ? AND word != ? 
        ORDER BY RANDOM() 
        LIMIT 3
    ''', (theme, correct_answer))
    distractors = [r[0] for r in cur.fetchall()]

    options = distractors + [correct_answer]
    random.shuffle(options)

    if isinstance(sentence, str) and sentence.strip():
        used_sentences.append(sentence)
    session['used_sentences'] = used_sentences

    session['current_sentence'] = sentence
    session['current_answer'] = correct_answer

    conn.close()

    return render_template('fill_the_blanks.html',
                           sentence=sentence,
                           options=options,
                           answer=correct_answer,
                           theme=theme,
                           progress=f"{current_q + 1}/10")

@app.route('/check_answer', methods=['POST'])
def check_answer():
    user_guess = request.form['guess']
    correct_answer = session.get('current_answer')
    sentence = session.get('current_sentence')

    correct = user_guess.strip().lower() == correct_answer.strip().lower()
    if correct:
        session['correct'] += 1
        result = "Correct!"
    else:
        session['incorrect'] += 1
        result = f"Oops! The correct answer was: {correct_answer}"

    session['history'].append({
        'sentence': sentence,
        'user_guess': user_guess,
        'correct_answer': correct_answer
    })

    session['current_questionftb'] += 1

    return redirect(url_for('next_questionftb'))

@app.route('/resultsftb')
def resultsftb():
    correct = session.get('correct', 0)
    incorrect = session.get('incorrect', 0)
    history = session.get('history', [])
    all_correct = correct == 10

    user_id = current_user.id  

    con = sqlite3.connect('database.db')
    cur = con.cursor()

    cur.execute('''
        SELECT min_score, max_score, total_score, games_played
        FROM fill_the_blanks_stats
        WHERE user_id = ? AND theme = ?
    ''', (user_id, session.get('theme')))
    row = cur.fetchone()

    if row:
        min_score = min(row[0], correct) if row[0] is not None else correct
        max_score = max(row[1], correct)
        total_score = row[2] + correct
        games_played = row[3] + 1
        avg_score = total_score / games_played

        cur.execute('''
            UPDATE fill_the_blanks_stats
            SET min_score = ?, max_score = ?, total_score = ?, games_played = ?, avg_score = ?
            WHERE user_id = ? AND theme = ?
        ''', (min_score, max_score, total_score, games_played, avg_score, user_id, session.get('theme')))
    else:
        cur.execute('''
            INSERT INTO fill_the_blanks_stats (user_id, theme, min_score, max_score, total_score, games_played, avg_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, session.get('theme'), correct, correct, correct, 1, correct))

    con.commit()
    con.close()

    return render_template('resultsftb.html',
                           correct=correct,
                           incorrect=incorrect,
                           history=history,
                           all_correct=all_correct)

@app.route('/update_word_search_stats', methods=['POST'])
@login_required
def update_word_search_stats():
    user_id = session.get('user_id')
    data = request.get_json()
    theme   = data['theme']
    elapsed = data['time'] 
    success = data.get('success', True)

    con = sqlite3.connect('database.db')
    cur = con.cursor()
    
    cur.execute('''
        SELECT id, grid_attempted, grid_successful, time_min, time_max, time_avg
          FROM word_search_stats
         WHERE user_id=? AND theme=?
    ''', (user_id, theme))
    row = cur.fetchone()

    if row:
        stat_id, att, succ, tmin, tmax, tavg = row
        att += 1
        if success:
            succ += 1
            tmin = elapsed if tmin is None or elapsed < tmin else tmin
            tmax = elapsed if tmax is None or elapsed > tmax else tmax
            tavg = ((tavg * (succ - 1)) + elapsed) / succ if tavg is not None else elapsed

        cur.execute('''
            UPDATE word_search_stats
               SET grid_attempted=?, grid_successful=?, time_min=?, time_max=?, time_avg=?
             WHERE id=?
        ''', (att, succ, tmin, tmax, tavg, stat_id))
    else:
        cur.execute('''
            INSERT INTO word_search_stats
                (user_id, theme, grid_attempted, grid_successful, time_min, time_max, time_avg)
            VALUES (?, ?, 1, ?, ?, ?, ?)
        ''', (user_id, theme, 1 if success else 0, elapsed, elapsed, elapsed))

    con.commit()
    con.close()
    return jsonify({'status': 'success'})

@app.route('/save_memory_stats', methods=['POST'])
def save_memory_stats():
    data = request.get_json()

    user_id = data.get('user_id')
    theme = data.get('theme')
    attempts = data.get('attempts')

    if not all([user_id, theme, attempts]):
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    con = sqlite3.connect('database.db')
    cur = con.cursor()

    cur.execute('''
        SELECT total_games, victories, min_attempts, max_attempts, total_attempts
          FROM memory_stats
         WHERE user_id = ? AND theme = ?
    ''', (user_id, theme))
    row = cur.fetchone()

    if row:
        total_games, victories, min_a, max_a, total_a = row
        victories += 1
        min_a = min(min_a, attempts) if min_a is not None else attempts
        max_a = max(max_a, attempts) if max_a is not None else attempts
        total_a += attempts
        avg_a = total_a / total_games

        cur.execute('''
            UPDATE memory_stats
               SET victories = ?, min_attempts = ?, max_attempts = ?, total_attempts = ?, avg_attempts = ?
             WHERE user_id = ? AND theme = ?
        ''', (victories, min_a, max_a, total_a, avg_a, user_id, theme))
    else:
        cur.execute('''
            INSERT INTO memory_stats (
                user_id, theme, total_games, victories,
                min_attempts, max_attempts, total_attempts, avg_attempts
            ) VALUES (?, ?, 1, 1, ?, ?, ?, ?)
        ''', (user_id, theme, attempts, attempts, attempts, attempts))

    con.commit()
    con.close()

    return jsonify({'status': 'success'})

if __name__ == "__main__":
    app.run(debug=True)
