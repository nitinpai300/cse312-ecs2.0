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
app.secret_key = 'a'  # tbh i'm not sure what this is for again -chris


# routing index.html
@app.route('/', methods=["GET", "POST"])
def index():
    authenticationTOKEN = request.cookies.get("authenticationTOKEN", "none")
    auth, usr, xsrf = authenticate(authenticationTOKEN)
    if auth:
        return render_template("index.html", username=usr)

    return render_template("index.html")

@app.route('/functions.js', methods=["GET"])
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
    # if user exists
    authorized = bcrypt.checkpw(password, userDB.get("password").encode('utf-8'))
    if authorized:
        print("access granted")
        # form token here
        token = str(uuid.uuid1().int)
        tokenHASHED = bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode('utf-8')
        tokens.insert_one({"username": username, "authenticationTOKEN": f"{tokenHASHED}"})
        # send 204
        response = make_response(redirect(url_for('index')))
        response.set_cookie("authenticationTOKEN", token, httponly=True, max_age=3600)

        return response
    else:
        print("wrong password")
        response = make_response(
            "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nInvalid username or password")
        response.status_code = 400
        return response


@app.route('/signup', methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"].encode('utf-8')
    confirm_password = request.form['confirm-password'].encode('utf-8')
    # please fix name for confirmed_password
    if users.find_one({"username": username}):
        response = make_response("HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nUsername already in use")
        response.status_code = 400
        return response
    if password != confirm_password:
        response = make_response(
            "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\Passwords do not match, please re-enter")
        response.status_code = 400
        return response
    salt = bcrypt.gensalt()
    passwordHASHED = bcrypt.hashpw(password, salt)
    users.insert_one({"username": username, "password": f"{passwordHASHED.decode()}"})
    # send 204, flask method
    response = make_response("HTTP/1.1 204 No Content\r\n\r\n")
    response.status_code = 204
    return response



def authenticate(token, xsrf=None):
    # Set default values for a guest
    usr = "Guest"
    users = tokens.find()
    token = token.encode()
    XS = str(uuid.uuid1())
    for user in users:
        # loop through authenticated users and check the hash of their passwd
        auth_token = user.get("authenticationTOKEN", "").encode()
        auth = bcrypt.checkpw(token, auth_token)
        if auth:
            # Grab username from the authenticated user
            usr = user.get("username")
            # If xsrf is set to None, return a new token
            if xsrf is None:
                print("was:", user.get("xsrf"), "is now:", XS)
                tokens.update_one({"username": usr}, {"$set": {"xsrf": XS}})
            # Evaluate the token
            else:
                XS = xsrf == user.get("xsrf")
            print("\nauthorized: ", usr)
            return auth, usr, XS

    print("---Guest not authorized---")
    return False, usr, XS


@app.route('/signup.html', methods=['GET'])
def signup_page():
    return render_template('signup.html')


@app.route('/login.html', methods=['GET'])
def login_p():
    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    authenticationTOKEN = request.cookies.get("authenticationTOKEN", "none")
    auth, usr, xsrf = authenticate(authenticationTOKEN)
    if auth:
        tokens.delete_one({"username": usr})
    response = make_response(redirect('/'))
    return response


# post feed
@app.route("/feed", methods=['POST', 'GET'])
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


if __name__ == '__main__':
    app.run(port=8080, host="0.0.0.0")
#


