const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('validLOGIN', function (data) {
});


socket.on('invalidLOGIN', function (data) {
});


socket.on('userLIST', function (userList) {
});

socket.on('postINFO', function (data) {
});

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


