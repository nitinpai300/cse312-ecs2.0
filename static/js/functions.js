
function likeMessage(postID) {
    console.log("Here's your post: " + postID);
    socket.emit('likePost', {postID:postID});
}


function displayText() {
    document.getElementById("description").innerHTML += "<br/>If you are seeing this, then displayText() in functions.js is doing it's job! 😀";
}
