const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('validLOGIN', function (data) {
    console.log('You are currently logged in as: ' + data.username);
});

socket.on('invalidLOGIN', function (data) {
    console.log('could not login');
});


//i have no clue
socket.on('postINFO', function (data) {
});

//if like count exists, set like count equal to thelike count from post
socket.on('updateLikeCount', function (data) {
    const likeCountHTML = document.getElementById(`likeCount-${data.postID}`);
    if (likeCountHTML) {
        likeCountHTML.textContent = data.likes;
    }
});

socket.on('directMessage', function (data) {
});


//button ufnctionality somehwere here


function likeMessage(postID) {
    console.log("Here's your post: " + postID);
    socket.emit('likePost', {postID:postID});

}


function displayText() {
    document.getElementById("description").innerHTML += "<br/>If you are seeing this, then displayText() in functions.js is doing it's job! 😀";
}


