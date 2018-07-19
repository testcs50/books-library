import csv
import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session

app = Flask(__name__)

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine('postgres://jqqgftklpvyvks:f0d8fd573dd2bdd30d67a1df3e0e9f05240895a0ccb133e014d357a6ef624ece@ec2-23-23-247-222.compute-1.amazonaws.com:5432/d8irej1rchakkk')
db = scoped_session(sessionmaker(bind=engine))
@app.route('/')
def index():
    num = 0
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, yearr in reader:
        year = int(yearr)
        db.execute('INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)', {'isbn': isbn, 'title': title, 'author': author, 'year': year})
        num = num + 1
    db.commit()
    return 'its ok {}'.format(num)
