from flask import Flask, render_template, make_response, request, flash, redirect, url_for, session
from pymongo import MongoClient
import bcrypt
import hashlib
import secrets
import uuid

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
    print("index detected")
    return render_template("index.html")

@app.route('/functions.js', methods = ["GET"])
def js():
    return render_template("/static/js/functions.js")

@app.route('/images.jpeg', methods=['GET'])
def render():
    return render_template("/static/images/images.jpeg")

@app.route('/login', methods=["GET", "POST"])
def login():
    pass

@app.route('/signup', methods=["POST"])
def signup():
    pass

@app.route('/signup.html', methods=['GET'])
def signup_page():
    return render_template('signup.html')


@app.route('/login.html', methods=['GET'])
def login_p():
    return render_template('login.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    pass

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
