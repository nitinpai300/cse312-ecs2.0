from flask import Flask, render_template, make_response, request, flash, redirect, url_for, session
from pymongo import MongoClient
import bcrypt
import hashlib
import secrets
import uuid
import os
import hashlib

app = Flask(__name__)
mongo_client = MongoClient("mongo")
db = mongo_client["ECS"]
users = db["users"]
tokens = db["tokens"]
posts = db["posts"]
app.secret_key = 'a' # tbh i'm not sure what this is for again -chris

# routing index.html
@app.route('/', methods = ["GET", "POST"])
def index():
    authenticationTOKEN = request.cookies.get("authenticationTOKEN")
    username = None
    if authenticationTOKEN:
        tokenHASHED = hashlib.sha256(authenticationTOKEN.encode()).hexdigest()
        user = users.find_one({"authenticationTOKEN": tokenHASHED})
        if user:
            username = user["username"]
        return render_template("index.html", username=username)


@app.route('/functions.js', methods = ["GET"])
def js():
    return render_template("/static/js/functions.js")

@app.route('/images.jpeg', methods=['GET'])
def render():
    return render_template("/static/images/images.jpeg")

@app.route('/login', methods=["GET", "POST"])
def login():
    username = request.form["username"]
    password = request.form["password"].encode('utf-8')
    userDB = users.find_one({"username": username})
    if not userDB:
        print("user not found")
        response = make_response("HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nUsername does not exist")
        response.status_code = 400
        return response
    #if user exists
    salt = userDB.get("salt")
    passwordHASHED = bcrypt.hashpw(password, salt)
    if passwordHASHED == userDB.get("password"):
        print("access granted")
        #form token here
        token = os.urandom(16).hex()
        tokenHASHED = hashlib.sha256(token.encode()).hexdigest()
        users.update_one({"username": username}, {"$set": {"authenticationTOKEN": tokenHASHED}})

        response = make_response(redirect(url_for('index')))
        response.set_cookie("authenticationTOKEN", token, httponly=True, max_age=3600)
        return response

    else:
        print("wrong password")
        response = make_response("HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nInvalid username or password")
        response.status_code = 400
        return response


@app.route('/signup', methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"].encode('utf-8')
    confirm_password = request.form['confirm-password'].encode('utf-8')
    #please fix name for confirmed_password
    if users.find_one({"username": username}):
        response = make_response("HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nUsername already in use")
        response.status_code = 400
        return response
    if password != confirm_password:
        response = make_response("HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\Passwords do not match, please re-enter")
        response.status_code = 400
        return response
    salt = bcrypt.gensalt()
    passwordHASHED = bcrypt.hashpw(password, salt)
    users.insert_one({"username": username, "password": passwordHASHED, "salt": salt})
    return redirect(url_for('index'))



@app.route('/signup.html', methods=['GET'])
def signup_page():
    return render_template('signup.html')


@app.route('/login.html', methods=['GET'])
def login_p():
    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    authenticationTOKEN = request.cookies.get("authenticationTOKEN")
    if authenticationTOKEN:
        tokenHASHED = hashlib.sha256(authenticationTOKEN.encode()).hexdigest()
        temp = users.find_one({"authenticationTOKEN": tokenHASHED})
        if temp:
            users.update_one({"authenticationTOKEN": tokenHASHED}, {"$unset": {"authenticationTOKEN": ""}})

    #response = make_response(redirect('/'))
    #response.set_cookie('authenticationTOKEN', '', expires=0, httponly=True)
    #return response
    return redirect('/')


# post feed
@app.route("/feed", methods = ['POST','GET'])
def feed():
    pass

@app.route("/like", methods=['POST'])
def likePost():
    # Retrieve the messageId from the request body
    postID = request.json.get('postID')
    # check if post is in user's liked posts database column
    username = session.get("username")
    user = users.find_one({"username": username})
    liked_posts = user.get("liked_posts")
    # if it isnt, increment the post's likes column by 1 and add the post to user's liked posts column
    if postID not in liked_posts:
        posts.update_one({"postID": postID}, {"$inc": {"likes": 1}})
        posts.update_one({"postID": postID}, {"$push": {"likedBy": username}})
        users.update_one({"username": username}, {"$push": {"liked_posts": postID}})

        return redirect(url_for('feed'))
    # else, subtract one like from the post and remove it from user's liked posts data column
    else:
        posts.update_one({"postID": postID}, {"$inc": {"likes": -1}})
        posts.update_one({"postID": postID}, {"$pull": {"likedBy": username}})
        users.update_one({"username": username}, {"$pull": {"liked_posts": postID}})
        return redirect(url_for('feed'))

@app.after_request
def set_response_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

if __name__=='__main__':
    app.run(port= 8080, host="0.0.0.0")
#