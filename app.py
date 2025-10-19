from flask import Flask,render_template,request,session
from sqlalchemy import create_engine

# Path to your .mdf file
db_path = r"D:\Java\JavaProject\Database\EvTracker.mdf"

app=Flask(__name__)

@app.route('/')
def login():
    return render_template("index.html")

@app.route('/request')
def request():
    pass