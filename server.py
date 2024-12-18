from flask import Flask, render_template, make_response, request, flash, redirect, url_for, session
from pymongo import MongoClient
import bcrypt
import secrets
import uuid
import os
import hashlib
import eventlet
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
from datetime import datetime

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
profiles = db["profiles"]
app.secret_key = 'a'  # tbh i'm not sure what this is for again -chris

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
rooms_users = defaultdict(set)
currentUSERLST = {}
userActive = {}


#====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED
@socketio.on('newPost')
def handle_new_post(data):
    user_authtoken = request.cookies.get("authenticationTOKEN")
    auth, user, xsrf = authenticate(user_authtoken)
    if auth:
        post_content = data.get('post_content', '')
        filename = ""
        if 'upload' in data:
            image_data = data['upload']
            filename = f"static/images/{str(uuid.uuid4())}.jpg"
            with open(filename, "wb") as f:
                f.write(image_data)
        post_id = str(uuid.uuid4())
        posts.insert_one({
            "postID": post_id,
            "author": user,
            "post_content": post_content,
            "filename": filename,
            "likes": 0,
            "likedBy": []
        })
        updated_posts = list(posts.find())
        for post in updated_posts:
            post['_id'] = str(post['_id'])
        socketio.emit('updateFeed', {"posts": updated_posts}, namespace="/")
    else:
        emit('error', {'message': 'Authentication failed'})


@socketio.on('requestFeed')
def send_feed():
    get_posts = list(posts.find())
    for post in get_posts:
        post['_id'] = str(post['_id'])
    emit('updateFeed', {"posts": get_posts})


@socketio.on('likePost')
def likePost(data):
    postID = data.get('postID')
    user_authtoken = request.cookies.get("authenticationTOKEN")
    auth, usr, xsrf = authenticate(user_authtoken)
    if auth:
        user = users.find_one({"username": usr})
        liked_posts = user.get("liked_posts", [])
        #copy and pasted if postID ...
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


#====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED====WEBSOCKET FEED

#====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE
@socketio.on('connect')
def on_connect():
    authenticationTOKEN = request.cookies.get("authenticationTOKEN", "")
    auth, usr, xsrf = authenticate(authenticationTOKEN)

    if auth:
        userActive[request.sid] = {
            "username": usr,
            "last_active": datetime.now(),
            "active_time": 0,
            "inactive_time": 0,
            "inactive": False
        }
        emit('my response', {'message': f'{usr} has joined'})
        #start timer
        if not hasattr(backgroundTIMER, "_task_started"):
            backgroundTIMER._task_started = True
            socketio.start_background_task(target=backgroundTIMER)


@socketio.on('userActive')
def on_userActive():
    if request.sid in userActive:
        user_data = userActive[request.sid]
        if user_data["inactive"]:
            #make inactive user "active"
            inactive_duration = (datetime.now() - user_data["last_active"]).total_seconds()
            user_data["inactive_time"] += inactive_duration
        user_data["inactive"] = False
        user_data["last_active"] = datetime.now()  # Reset last active time


@socketio.on('userInactive')
def on_userInactive():
    if request.sid in userActive:
        user_data = userActive[request.sid]
        if not user_data["inactive"]:  #if user active but check inactive bc checking active errors
            #make active user "inactive"
            active_duration = (datetime.now() - user_data["last_active"]).total_seconds()
            user_data["active_time"] += active_duration
        user_data["inactive"] = True
        user_data["last_active"] = datetime.now()


def backgroundTIMER():
    while True:
        for user_sid, data in userActive.items():
            if not data["inactive"]:
                active_duration = (datetime.now() - data["last_active"]).total_seconds()
                data["active_time"] += active_duration
                data["last_active"] = datetime.now()
            else:
                inactive_duration = (datetime.now() - data["last_active"]).total_seconds()
                data["inactive_time"] += inactive_duration
                data["last_active"] = datetime.now()

        #ws emit times 
        active_inactive_times = {
            data["username"]: {
                "active_time": round(data["active_time"], 2),
                "inactive_time": round(data["inactive_time"], 2)
            }
            for user_sid, data in userActive.items()
        }
        socketio.emit('updateUserActivity', active_inactive_times)
        eventlet.sleep(1)


@socketio.on('disconnect')
def on_disconnect():
    if request.sid in userActive:
        del userActive[request.sid]


#====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE====ACTIVE/INACTIVE


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
    profiles.insert_one({"username": username, "profile_picture": "/static/images/Default.jpg"})
    # send 204, flask method
    response = make_response("HTTP/1.1 204 No Content\r\n\r\n")
    response.status_code = 204
    return response


@app.route("/feed", methods=["GET"])
def feed():
    user_authtoken = request.cookies.get("authenticationTOKEN")
    auth, user, xsrf = authenticate(user_authtoken)
    if auth:
        getPosts = posts.find()
        pfp = profiles.find_one({"username": user}).get("profile_picture")
        return render_template('feed.html', posts=getPosts, username=user, pfp=pfp)
    else:
        return redirect(url_for('login_p'))


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


# ----- Profile ---------

@app.route('/profile', methods=["GET", "POST"])
def profile():
    user_authtoken = request.cookies.get("authenticationTOKEN")
    auth, usr, xsrf = authenticate(user_authtoken)
    # Set the profile picture
    if auth:
        # Change the profile picture
        if request.method == "POST":
            pfp = profiles.find_one({"username": usr}).get("profile_picture")
            if "upload" in request.files:
                if pfp != "/static/images/Default.jpg":
                    os.remove(pfp)
                file = request.files["upload"]
                pfp = f"static/images/{str(uuid.uuid4())}.jpg"
                with open(pfp, "wb") as f:
                    f.write(file.read())
                profiles.update_one({"username": usr}, {"$set": {"profile_picture": pfp}})
        # Get the old one
        else:
            pfp = profiles.find_one({"username": usr}).get("profile_picture")
        usr_posts = posts.find({"author": usr})
    else:
        pfp = "/static/images/Default.jpg"
        usr_posts = {}
    return render_template("profile.html", username=usr, auth=auth, posts=usr_posts, pfp=pfp)

# -----------------------


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    authenticationTOKEN = request.cookies.get("authenticationTOKEN", "none")
    auth, usr, xsrf = authenticate(authenticationTOKEN)
    if auth:
        tokens.delete_one({"username": usr})
    response = make_response(redirect('/'))
    return response


@app.after_request
def set_response_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


socketio.run(app, host='0.0.0.0', port=8080, debug=True)

#
