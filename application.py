import os

from flask import Flask, session, render_template, request, redirect, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
import requests

app = Flask(__name__)


if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))




@app.route("/")
def index():
    
    return render_template('index.html')

@app.route("/register",  methods=['POST','GET'])    
def register():
    
    session.clear()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']
        
        if username == '' or password =='' or confirmPassword =='':
            return render_template('register.html', message='Please enter missing username or passwords')
        
        if password != confirmPassword:
            return render_template('register.html', message='Please enter matching passwords')

        userCheck = db.execute("SELECT * FROM users WHERE username = :username",{"username":request.form.get("username")}).fetchone()
        if userCheck:
            return render_template("register.html", message="username already exist")

        hashedPassword = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", {"username":request.form.get("username"), "password":hashedPassword})

        db.commit()

        flash('Account created', 'info')
        
        return render_template('submit.html', value=username)

    else:
        return render_template('register.html')
    
@app.route("/login", methods=['POST','GET'])    
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == '' or password =='':
            return render_template('login.html', message='Please enter missing username or password')
        
        rows = db.execute("SELECT * FROM users WHERE username = :username", {"username": username})
        result = rows.fetchone()

        if result == None or not check_password_hash(result[1], request.form.get("password")):
            return render_template("login.html", message="invalid username and/or password")
        
        session["user_id"] = result[0]
        session["user_name"] = result[2]

        return render_template("search.html")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")

@app.route("/api/<isbn>", methods=['GET'])
def api_call(isbn):

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422
   
    tmp = row.fetchone()

    result = dict(tmp.items())

    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)  


@app.route("/search")
def search():
    if not request.args.get("book"):
        return render_template("search.html", message="You must provide a book.")

    query = "%" + request.args.get("book") + "%"

    query = query.title()
    
    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query LIMIT 15",
                        {"query": query})
    
    if rows.rowcount == 0:
        return render_template("search.html", message="Sorry, we coulnd't find any books with that description.")
    
    books = rows.fetchall()

    return render_template("books.html", books=books)


@app.route("/binfo/<isbn>", methods=['GET','POST'])
def binfo(isbn):
    if request.method == "POST":

        currentUser = session["user_id"]
        
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

        bookId = row.fetchone()
        bookId = bookId[0]

        row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                    {"user_id": currentUser,
                     "book_id": bookId})

        if row2.rowcount == 1:
            
            flash('You already submitted a review for this book')
            return redirect("/binfo/" + isbn)

        rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, comment, rating) VALUES \
                    (:user_id, :book_id, :comment, :rating)",
                    {"user_id": currentUser, 
                    "book_id": bookId, 
                    "comment": comment, 
                    "rating": rating})

        db.commit()

        this_book_url = "/binfo/" + isbn

        return redirect(this_book_url)
    
    else:

        row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})

        bookInfo = row.fetchall()

        key = "DPLKiSQZOWJyeFbnfz3cg"

        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                params={"key": key, "isbns": isbn})

        response = query.json()

        response = response['books'][0]

        bookInfo.append(response)

        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

        book = row.fetchone() 
        book = book[0]

        results = db.execute("SELECT users.username, comment, rating \
                            FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.user_id \
                            WHERE book_id = :book \
                            ORDER BY rating",
                            {"book": book})

        reviews = results.fetchall()

        return render_template("binfo.html", bookInfo=bookInfo, reviews=reviews)


 

        



#import requests
#res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "DPLKiSQZOWJyeFbnfz3cg", "isbns": "9781632168146"})
#print(res.json())