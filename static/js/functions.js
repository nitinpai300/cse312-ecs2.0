const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('validLOGIN', function (data) {
    console.log('You are currently logged in as: ' + data.username);
});

socket.on('invalidLOGIN', function (data) {
    console.log('could not login');
});


//need work done
socket.on('postINFO', function (data) {
    //dan this is suppose to get the values form the div where post is handled
    // so getElementbyid(posts) or whatever the name is in feed.html
    //maybe make a new div for every new post?
});

//if like count exists, set like count equal to thelike count from post
socket.on('updateLikeCount', function (data) {
    const likeCountHTML = document.getElementById(`likeCount-${data.postID}`);
    if (likeCountHTML) {
        likeCountHTML.textContent = data.likes;
    }
});


function likeMessage(postID) {
    socket.emit('likePost', {postID:postID});
}

function displayText() {
    document.getElementById("description").innerHTML += "<br/>If you are seeing this, then displayText() in functions.js is doing it's job! 😀";
}


