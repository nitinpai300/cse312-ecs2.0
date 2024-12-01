const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('validLOGIN', function (data) {
});


socket.on('invalidLOGIN', function (data) {
});


socket.on('userLIST', function (data) {
});

socket.on('postINFO', function (data) {
});

socket.on('updateLikeCount', function (data) {
});


socket.on('directMessage', function (data) {
});





function likeMessage(postID) {
    console.log("Here's your post: " + postID);
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    };
    request.open("POST", "/like");
    request.setRequestHeader("Content-Type", "application/json");
    request.send(JSON.stringify({postID: postID}));
}

function displayText() {
    document.getElementById("description").innerHTML += "<br/>If you are seeing this, then displayText() in functions.js is doing it's job! 😀";
}


