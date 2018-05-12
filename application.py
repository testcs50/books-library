import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if 'username' not in session:
        return render_template('login.html', title='Авторизация', color='#00ccff', no=True)
    else:
        user_id = db.execute('SELECT id FROM users WHERE username = :username', {'username': session['username']}).fetchone()
        book_id = db.execute('SELECT book_id FROM comments WHERE user_id = :user_id', {'user_id': str(user_id[0])}).fetchall()
        isDoYet = []
        for element in book_id:
            tmp = db.execute('SELECT title FROM books WHERE id = :book_id', {'book_id': element[0]}).fetchone()
            dict = {
            'id': element[0],
            'name': tmp[0]
            }
            isDoYet.append(dict)
        return render_template('index.html', title='Главная', color='#63008f', isDoYet=isDoYet, username=session['username'])

@app.route("/reg", methods=["GET", "POST"])
def reg():
    if request.method == "POST":
        isReg = False
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
            isReg = True
            db.commit()
            return render_template('askreg.html', isReg=isReg, username=username, title='Успешно', color='#00ff00', no=True)
        return render_template('askreg.html', isReg=isReg, title='Провал', color='#ff0000', no=True)
    return render_template('reg.html', title='Регистрация', color='#ffd700', no=True)


#@app.route("/login", methods=['POST'])
#def login():
#    if request.form.get('username') in db.execute("SELECT username FROM users").fetchall() and request.form.get('password') == db.execute("SELECT passsword FROM users WHERE username = :username", {"username": request.form.get('username')}).fetchone():
#        session['username'] = request.form.get('username')
#        session['password'] = request.form.get('password')
#        return redirect(url_for('index'))
#    return render_template('error.html', text='Неправильный логин или пароль', title='Ошибка!')


@app.route("/login", methods=['POST'])
def login():
    users = db.execute("SELECT * FROM users").fetchall()
    for user in users:
        if request.form['username'] in user[1]:
            if request.form['password'] in user[2]:
                session['username'] = request.form['username']
                session['password'] = request.form['password']
                return redirect(url_for('index'))
            return render_template('error.html', text='Неправильный логин или пароль', title='Ошибка!', color='#ff0000', no=True)
        return render_template('error.html', text='Неправильный логин или пароль', title='Ошибка!', color='#ff0000', no=True)
    return render_template('error.html', text='Что то пошло не так', title='Ошибка!', color='#ff0000', no=True)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('index'))

@app.route('/books', methods=['POST'])
def books():
    book = request.form['name']
    #books = db.execute("SELECT * FROM books WHERE to_tsvector(author) || to_tsvector(title) @@ plainto_tsquery(:book)", {"book": book}).fetchall()
    books = db.execute("SELECT * FROM books WHERE title LIKE (:book) OR isbn LIKE (:book) OR author LIKE (:book)", {"book": '%' + book + '%'}).fetchall()
    return render_template('books.html', books=books, title='Результат поиска', color='#000000')

@app.route('/books/<int:book_id>')
def book(book_id):
    book = db.execute('SELECT * FROM books WHERE id = :book_id', {'book_id': book_id}).fetchone()
    if book is None:
        return render_template('error.html', text='Неправильно сконструированный запрос', title='Ошибка!', color='#ff0000')
    bookname = db.execute('SELECT title FROM books WHERE id = :book_id', {'book_id': book_id}).fetchone()
    comments = db.execute('SELECT comment FROM comments WHERE book_id = :book_id', {'book_id': book_id}).fetchall()
    return render_template('book.html', book=book, comments=comments, title=bookname, color='#a9a9a9')

@app.route('/addcomment/<int:book_id>', methods=['POST'])
def addcomment(book_id):
    com = request.form['name']
    comment = str(com)
    user_id = db.execute('SELECT id FROM users WHERE username = :username', {'username': session['username']}).fetchone()
    db.execute('INSERT INTO comments (comment, user_id, book_id) VALUES (:comment, :user_id, :book_id)', {'comment': comment, 'user_id': user_id[0], 'book_id': book_id})
    db.commit()
    return redirect(url_for('book', book_id=book_id))

#   SNIPPET FOR CAESH   #
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
#   SNIPPET FOR CAESH   #
