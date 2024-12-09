
import os
from flask import Flask,render_template, make_response, request, flash, redirect, url_for, session, jsonify, abort
import bcrypt
from pymongo import MongoClient
from time import time
import uuid
from collections import defaultdict
from flask_socketio import SocketIO, emit

app = Flask(__name__)
docker_db = os.environ.get("DOCKER_DB", "false")
if docker_db == "true":
    print("Using docker database")
    mongo_client = MongoClient("mongo")
else:
    print("Using local database")
    mongo_client = MongoClient("localhost")

db = mongo_client["ECS"]
users = db["users"]
tokens = db["tokens"]
posts = db["posts"]
app.secret_key = 'a'  # tbh i'm not sure what this is for again -chris

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
rooms_users = defaultdict(set)
currentUSERLST = {}


# ----------WEBSOCKET--------------------------------------------------------------

@app.route("/feed", methods=['POST', 'GET'])
def feed():
    if request.method == 'POST':
        user_authtoken = request.cookies.get("authenticationTOKEN")
        auth, user, xsrf = authenticate(user_authtoken)
        post_content = request.form['post_content']
        # save image to disk - by chris j
        filename = ""
        if "upload" in request.files:
            file = request.files["upload"]
            filename = f"static/images/{str(uuid.uuid4())}.jpg"
            with open(filename, "wb") as f:
                f.write(file.read())
        posts.insert_one(
            {"postID": str(uuid.uuid4()), "author": user, "post_content": post_content, "filename": filename,
             "likes": 0, "likedBy": []})
        return redirect(url_for('feed'))
    else:
        getPosts = posts.find()
        return render_template('feed.html', posts=getPosts)


@socketio.on('connect')
def on_connect():
    authenticationTOKEN = request.cookies.get("authenticationTOKEN", "")
    auth, usr, xsrf = authenticate(authenticationTOKEN)
    print("authed", usr)
    if auth:
        session['username'] = usr
        currentUSERLST[usr] = request.sid
        emit('my response',
             {'message': '{0} has joined'.format(usr)})


@socketio.on('likePost')
def likePost(data):
    postID = data.get('postID')
    user_authtoken = request.cookies.get("authenticationTOKEN")
    auth, usr, xsrf = authenticate(user_authtoken)
    if auth:
        user = users.find_one({"username": usr})
        liked_posts = user.get("liked_posts", [])
        # copy and pasted if postID ...
        if postID not in liked_posts:
            posts.update_one({"postID": postID}, {"$inc": {"likes": 1}})
            posts.update_one({"postID": postID}, {"$push": {"likedBy": usr}})
            users.update_one({"username": usr}, {"$push": {"liked_posts": postID}})
        else:
            posts.update_one({"postID": postID}, {"$inc": {"likes": -1}})
            posts.update_one({"postID": postID}, {"$pull": {"likedBy": usr}})
            users.update_one({"username": usr}, {"$pull": {"liked_posts": postID}})

        post = posts.find_one({"postID": postID})
        postVALUES = {
            'postID': postID,
            'likes': post.get('likes', 0),
            'likedBy': post.get('likedBy', [])
        }
        postVALUES["likedBy"] = "Liked by: " + " ".join(postVALUES["likedBy"])
        postVALUES["likes"] = "Likes: " + f'{postVALUES["likes"]}'
        print(postVALUES)
        socketio.emit("updateLikeCount", postVALUES)


@socketio.on('disconnect')
def on_disconnect():
    username = session.get('username')
    if username:
        currentUSERLST.pop(username)
        emit("userLIST", list(currentUSERLST.keys()), broadcast=True)


# --------------------------------------------------------------------------------------

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


@app.route('/images.jpg', methods=['GET'])
def render():
    return render_template("/static/images/images.jpg")


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
    authorized = bcrypt.checkpw(password, userDB.get("password"))
    if authorized:
        print("access granted")
        # form token here
        token = str(uuid.uuid1().int)
        tokenHASHED = bcrypt.hashpw(token.encode(), bcrypt.gensalt())
        tokens.insert_one({"username": username, "authenticationTOKEN": tokenHASHED})
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
    users.insert_one({"username": username, "password": passwordHASHED, "liked_posts": []})
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
        auth_token = user.get("authenticationTOKEN", "")
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


# DDOS PROT CODE BELOW
request_timestamps = defaultdict(list)
blocked_ips = defaultdict(float)

def get_ip():
    if 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For'].split(',')[0]
    return request.remote_addr

# Prevent DoS attacks basic -Will
@app.before_request
def ip_requests():
    if request.path != "/get_user_times":
        clip = get_ip()
        current_time = time()

        if clip in blocked_ips and current_time - blocked_ips[clip] > 30:
            del blocked_ips[clip]

        if clip in blocked_ips:
            abort(429, 'Too Many Requests: Please try again later.')

        updated_timestamps = []
        for i in request_timestamps[clip]:
            if current_time - i < 10:
                updated_timestamps.append(i)
        request_timestamps[clip] = updated_timestamps

        request_timestamps[clip].append(current_time)

        if len(request_timestamps[clip]) > 50:
            blocked_ips[clip] = current_time
            abort(429, 'Too Many Requests: Please try again later.')

@app.after_request
def decrease_req(response):
    clip = request.remote_addr
    current_time = time()
    updated_timestamps = []
    for i in request_timestamps[clip]:
        if current_time - i < 10:
            updated_timestamps.append(i)
    request_timestamps[clip] = updated_timestamps
    return response

@app.after_request
def set_response_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response 

socketio.run(app, host='0.0.0.0', port=8080, debug=True)

#


