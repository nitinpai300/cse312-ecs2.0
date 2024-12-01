const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('validLOGIN', function (data) {
    console.log('You are currently logged in as: ' + data.username);
});

socket.on('invalidLOGIN', function (data) {
    console.log('could not login');
});
//if userlist exists, empty it so it tecnically is a refresh, and add every user from userlist in list form li
socket.on('userLIST', function (userLIST) {
    console.log("User List: ", userLIST);
    const userLISTHTML = document.getElementById('userLIST');
    if (userLISTHTML) {
        userLISTHTML.innerHTML ="";
        for (let i = 0; i < userLIST.length; i++) {
            const aUser = document.createElement('li');
            aUser.textContent = userLIST[i];
            userLISTHTML.appendChild(aUser);
        }
    }
});

//i have no clue
socket.on('postINFO', function (data) {
});

//if like count exists, set like count equal to thelike count from post
socket.on('updateLikeCount', function (data) {
});

socket.on('directMessage', function (data) {
});


//button ufnctionality somehwere here


function likeMessage(postID) {
    console.log("Here's your post: " + postID);
    socket.emit('likePost', {postID:postID});

}

function sendDirectMessage(recipient, message) {
    socket.emit('directMessage', "notsure");
}


function displayText() {
    document.getElementById("description").innerHTML += "<br/>If you are seeing this, then displayText() in functions.js is doing it's job! 😀";
}


