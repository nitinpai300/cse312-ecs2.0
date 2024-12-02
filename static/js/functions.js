
//
// //if like count exists, set like count equal to the like count from post
// socket.on('updateLikeCount', function (data) {
//     const likeCountHTML = document.getElementById(`likeCount-${data.postID}`);
//     if (likeCountHTML) {
//         likeCountHTML.textContent = data.likes;
//     }
// });
//
//

//button functionality somewhere here


function likeMessage(postID) {
    console.log("Here's your post: " + postID);
    socket.emit('likePost', {postID:postID});

}


function displayText() {
    document.getElementById("description").innerHTML += "<br/>If you are seeing this, then displayText() in functions.js is doing it's job! 😀";
}


function updateLikes(){

}