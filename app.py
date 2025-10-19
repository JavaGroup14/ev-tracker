from flask import Flask,render_template,request,session

app=Flask(__name__)

@app.route('/')
def login():
    return render_template("index.html")

@app.route('/register')
def register():
    return render_template("register.html")