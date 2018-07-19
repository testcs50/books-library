import csv
import os
import psycopg2
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session

app = Flask(__name__)

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine('postgres://jqqgftklpvyvks:f0d8fd573dd2bdd30d67a1df3e0e9f05240895a0ccb133e014d357a6ef624ece@ec2-23-23-247-222.compute-1.amazonaws.com:5432/d8irej1rchakkk')
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():

    #если пользователь не авторизован, отправляем его на страницу авторизации
    if 'username' not in session:
        return render_template('login.html', title='Авторизация', color='#00ccff', isNotNeedNavigationAndForm=True)
    else:
        #Иначе, если пользоваетель авторизован:

        #берем его id из таблицы пользователей
        user_id = db.execute('SELECT id FROM users WHERE username = :username', {'username': session['username']}).fetchone()
        #берем из таблицы комментариев id всех книг, к которым он оставлял комментарий и оценку
        book_id = db.execute('SELECT book_id FROM comments WHERE user_id = :user_id', {'user_id': user_id[0]}).fetchall()

        #создаем список
        doesYet = []

        #перебираем ранее запрошенные нами id всех книг, к которым текущий пользователь оставлял комментарий и оценку
        for element in book_id:
            #делаем запрос в базу на название книги по ее id
            tmp = db.execute('SELECT title FROM books WHERE id = :book_id', {'book_id': element[0]}).fetchone()
            #создаем словарь и добавляем в него id книги (чтобы построить ссылкуна книгу) и название книги
            dict = {
            'id': element[0],
            'name': tmp[0]
            }
            #добавляем словарь в конец массива
            doesYet.append(dict)

        #направляем пользователя на главную страницу, передавая туда имя пользователя и наш список
        return render_template('index.html', title='Главная', color='#63008f', username=session['username'], doesYet=doesYet, isNotNeedHeadlink=True)

@app.route("/registration", methods=["GET", "POST"])
def registration():
    #Данная функция принимает 2 метода GET и POST
    #Если метод запроса POST (т.е., если человек уже был на странице регистрации и отправил оттуда форму):
    if request.method == "POST":

        #вводим булеан-переменную, чтобы при успешной и провальной регистрации показать разный контент
        isReg = False
        #достаем из формы запроса логин и пароль, введенный регистрирующимся
        username = request.form.get("username")
        password = request.form.get("password")

        #если в форме отправки присутствуют и логин, и пароль, т.е. они не None
        if username and password:

            #вводим переменную, в которой будет хранится начальное нулевое значение активности (активность - это то, сколько книг уже закомментил пользователь) пользователя
            activity = 0
            #добавляем нового пользователя в базу добавив в SQL-запрос логин, пароль и нулевое значение активности нового пользователя
            db.execute("INSERT INTO users (username, password, activity) VALUES (:username, :password, :activity)", {"username": username, "password": password, "activity": activity})
            #изменяем значение ранее введенной булеан-переменной, чтобы показать на странице answer.html, что регистрация прошла успешно
            isReg = True
            #сохраняем внесенные в базу изменения
            db.commit()
            #возвращаем страницу, которая покажет, что пользователь успешно зарегистрировался
            return render_template('answer.html', title='Успешно', color='#00ff00', isReg=isReg, username=username, isNotNeedNavigationAndForm=True)

        #иначе, если в строке логина или пароля или в обеих строках нет текста, то возвращаем страницу, которая покажет, что пользователь совершил ошибку
        return render_template('answer.html', title='Провал', color='#ff0000', isReg=isReg, isNotNeedNavigationAndForm=True)

    #иначе, если метод запроста GET, отправляем его на страницу с формой для регистрации
    return render_template('registration.html', title='Регистрация', color='#ffd700', isNotNeedNavigationAndForm=True)

@app.route("/login", methods=['POST'])
def login():
    #когда пользователь входит на свою страницу, если он заполнил оба поля (логин и пароль)
    if request.form['username'] and request.form['password']:

        #запрашиваем все из таблицы users и перебираем все это в for-цикле, чтобы посмотреть есть ли среди значений нашей таблицы значения заполненных пользователем форм
        users = db.execute("SELECT * FROM users").fetchall()
        for user in users:

            #если среди запрошенных нами значений таблицы под ключом #1 (username) есть значение поля username отправленной нам формы
            if request.form.get('username') in user[1]:

                #если среди запрошенных нами значений таблицы под ключом #2 (password) есть значение поля password отправленной нам формы
                if request.form.get('password') in user[2]:
                    #добавляем в сессию под ключами username и password значения полей username и password отправленной нам формы
                    session['username'] = request.form.get('username')
                    session['password'] = request.form.get('password')
                    #редиректируем пользователя в index()
                    return redirect(url_for('index'))

                #иначе, если среди запрошенных нами значений таблицы под ключом #2 (password) нет значения поля password отправленной нам формы, то выходим из цикла
                break

            #если логин не нашли на текущей итерации, переходим к слудующей, пока не проверятся все логины на совпадение
            continue

        #иначе, если среди запрошенных нами значений таблицы под ключом #1 (username) нет значения поля username отправленной нам формы, то отправляем пользователя на страницу, уведомляющую об ошибке
        return render_template('error.html', text='Неправильный логин или пароль', title='Ошибка!', color='#ff0000', isNotNeedNavigationAndForm=True)

    #иначе, если пользователь не заполнил оба поля, то отправляем его на страницу, уведомляющую об ошибке
    return render_template('error.html', text='Что то пошло не так', title='Ошибка!', color='#ff0000', isNotNeedNavigationAndForm=True)

@app.route('/books', methods=['POST'])
def books():
    #Достаем из поля формы поиска книги значение
    book = request.form.get('book-name')

    #ищем по этому значению книги в нашей таблице books и возвращаем все найденные совпадения
    #books = db.execute("SELECT * FROM books WHERE to_tsvector(author) || to_tsvector(title) @@ plainto_tsquery(:book)", {"book": book}).fetchall()
    books = db.execute("SELECT * FROM books WHERE title LIKE (:book) OR isbn LIKE (:book) OR author LIKE (:book)", {"book": '%' + book + '%'}).fetchall()

    #отправляем пользователя на страницу, в которой мы покажем список всех найденных нами совпадений, и, соответственно, передаем туда этот список найденных нами совпадений
    return render_template('books.html', title='Результат поиска', color='#000000', books=books)

@app.route('/book/<int:book_id>')
def book(book_id):
    #достаем из таблицы books книгу по id, переданному нам со ссылкой
    book = db.execute('SELECT * FROM books WHERE id = :book_id', {'book_id': book_id}).fetchone()

    #если по такому id нет книги, то отправляем пользователя на страницу, уведомляющую об ошибке
    if book is None:
        return render_template('error.html', text='Неправильно сконструированный запрос', title='Ошибка!', color='#ff0000')

    #достаем из таблицы comments все где есть id, переданный нам со ссылкой
    comments = db.execute('SELECT * FROM comments WHERE book_id = :book_id', {'book_id': book_id}).fetchall()

    #делаем API-запрос на сайт goodreads и в качестве параметров передаем туда наш API-ключ и isbn книги
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "UXKCfl5pVL8RpH8FSDeg", "isbns": book.isbn})
    #достаем JSON-объект из ответа на наш запрос
    data = res.json()

    #вводим две переменные, чтобы подсчитать количество оценок для данной книги, оставленных пользователями на нашем сайте и суммы этих оценок
    ourRatingQuentity = 0
    ourRatingSum = 0

    #создаем две переменные-массива, чтобы добавить в первую - информацию, которую мы будем отображать в блоке комментария, а во вторую - информацию о рейтинге
    commentComplex = []
    ratingInfo = []

    #вводим булеан-переменную для проверки добавил ли пользователь уже на эту книгу комментарий
    isWriteYet = False

    #перебираем записи комментариев, которые мы ранее добыли
    for comment in comments:

        #со значением #2 (user_id) каждой перебираемой записи, ищем никнейм пользователя, оставившего данный комментарий, из таблицы users
        commentator = db.execute('SELECT username FROM users WHERE id = :user_id', {'user_id': comment[2]}).fetchone()
        commentMaker = commentator[0]

        #если пользователь, оставивший данный комментарий сейчас в сессии:
        if commentMaker == session['username']:

            #вместо имени пользователя выводим текст "Вы"
            commentMaker = 'Вы'
            #изменяем значение boolean-переменной, чтобы пользователь не смог писать больше комментариев
            isWriteYet = True

        #создаем словарь и добавляем автора, поставленную им оценку и текст данного комментария
        commentDict = {
        'author': commentMaker,
        'text': comment[1],
        'rating': comment[4]
        }
        #добавляем этот словарь в конец массива
        commentComplex.append(commentDict)

        #прибавляем к переменной суммы оценок оценку, оставленную с данным комментарием
        ourRatingSum += comment[4]
        #прибавляем к переменной количества оценок единицу
        ourRatingQuentity += 1

    #--------------------------------------------------------------------------------------------
    #РАБОТА С API goodreads
    #МЫ НЕ БУДЕМ ПОКАЗЫВАТЬ НА САЙТЕ КОЛИЧЕСТВО ОЦЕНОК И СРЕДНЮЮ ОЦЕНКУ НАШЕГО САЙТА И САЙТА GOODREADS ПО ОТДЕЛЬНОСТИ
    #МЫ БУДЕМ ПОКАЗЫВАТЬ ОБЩЕЕ КОЛИЧЕСТВО ОЦЕНОК И ОБЩУЮ СРЕДНЮЮ ОЦЕНКУ
    #---------------------------------------------------------------------------------------------
    #
    #извлекаем из JSON-объекта, сделанного выше API-запроса, среднюю оценку goodreads и количество оценок goodreads
    average_rating = float(data['books'][0]['average_rating'])
    work_ratings_count = int(data['books'][0]['work_ratings_count'])

    #вводим переменную для общего среднего рейтинга и сначала задаем ему в значение произведение средней оценки goodreads и количества оценок goodreads
    total_rating = average_rating * work_ratings_count
    #добавляем к ней сумму рейтингов оставленных для данной книги на нашем сайте
    total_rating += ourRatingSum

    #вводим переменную для общего количества оценок и ставим ему в значение сумму количества оценок goodreads и количества оценок на нашем сайте
    total_ratings_count = work_ratings_count + ourRatingQuentity

    #обновляем значение переменной для общего среднего рейтинга, поделив его на общее количество оценок
    total_rating /= total_ratings_count

    #находим процент общего среднего рейтинга от максимально возможного среднего рейтинга. Нам он понадобится для линейного градиента
    percentOfRating = round((total_rating / 5) * 100)

    #округляем общее среднее значение до десятых
    total_rating = round(total_rating, 1)

    #добавляем общее количество голосов, общее среднее значение и процентное представление общего среднего рейтинга в массив
    ratingInfo.append(total_ratings_count)
    ratingInfo.append(total_rating)
    ratingInfo.append(percentOfRating)

    #---------------------------------------------------------------------------------------------------

    #отправляем пользователя на страницу информации о книге и передем ему оба массива и информацию о данной книге
    return render_template('book.html', book=book, comments=commentComplex, ratingInfo=ratingInfo, title=book.title, isWriteYet=isWriteYet, color='#a9a9a9')

@app.route('/addcomment/<int:book_id>', methods=['POST'])
def addcomment(book_id):
    #берем присланные нам по форме добавления комментария значение оценки и текст комментария
    comment = str(request.form['comment'])
    rating = int(request.form['rating'])

    #берем id и значение активности текущего пользователя на сайте
    user_info = db.execute('SELECT id, activity FROM users WHERE username = :username', {'username': session['username']}).fetchone()
    activity = user_info[1]

    #увеличиваем значение активности пользователя на единицу
    activity += 1

    #вставляем в таблицу comments новые данные
    db.execute('INSERT INTO comments (comment, user_id, book_id, rating) VALUES (:comment, :user_id, :book_id, :rating)', {'comment': comment, 'user_id': user_info[0], 'book_id': book_id, 'rating': rating})

    #обновляем значение активности текущего пользователя в таблице users
    db.execute('UPDATE users SET activity = :activity WHERE username = :username', {'activity': activity, 'username': session['username']})

    #сохраняем изменения в базе данных
    db.commit()

    #редиректируем пользователя в book(), передав соответствующий id текущей книги
    return redirect(url_for('book', book_id=book_id))

@app.route('/logout')
def logout():

    #удаляем из сессии логин и пароль пользователя
    session.pop('username', None)
    session.pop('password', None)

    #редиректируем его в index()
    return redirect(url_for('index'))


@app.route('/api/<string:isbn>')
def api(isbn):

    #запрашиваем книгу по указанному isbn
    book = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn}).fetchone()

    #если под таким isbn в нашей базе нет книги:
    if book is None:

        #то возвращаем JSON-объект, уведомляющий об ошибке и заголовок ошибки 404 (Not Found)
        return jsonify({'error': 'Invalid isbn'}), 404

    #создаем массив, чтобы добавить туда комментарии
    comments = []

    #вводим переменные суммы оценок, оставленных на данном сайте и их количества
    ratingSum = 0
    ratingQuentity = 0

    #вводим переменную средней величины оценок
    averageRating = 0

    #достаем из таблицы comments все комментарии и оценки для данной книги
    comms = db.execute('SELECT comment, rating FROM comments WHERE book_id = :book_id', {'book_id': book[0]}).fetchall()

    #return "{}".format(comms[0].comment)

    #для каждого элемента в возвращенном нам массиве комментариев и оценок
    for com in comms:

        #добавляем комментарий в конец массива comments
        comments.append({'comment': com.comment})

        #увеличиваем переменные суммы оценок и их количества на на оценку в текущем элементе и единицу соответственно
        ratingSum += com[1]
        ratingQuentity += 1

    #находим среднюю величину оценок
    averageRating = round(ratingSum / ratingQuentity, 1)

    #возвращаем JSON-объект с нужными нам значениями
    return jsonify({
    'isbn': book.isbn,
    'title': book[2],
    'author': book.author,
    'year': book[4],
    'ratings_count': ratingQuentity,
    'average_rating': averageRating,
    'comments': comments
    })

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
