//For activity timer and inactivity timer
let inactivityTimeout = null; // Timeout to track inactivity
let isUserInactive = false;   // Flag to track if the user is inactive

function notifyActive() {
    if (isUserInactive) {
        socket.emit('userActive');
        isUserInactive = false;
    }
    resetInactivityTimeout();
}
function notifyInactive() {
    if (!isUserInactive) {
        socket.emit('userInactive');
        isUserInactive = true;
    }
}

//10 seconds
function resetInactivityTimeout() {
    clearTimeout(inactivityTimeout);
    inactivityTimeout = setTimeout(() => {
       notifyInactive();
       //THIS IS THE VALUE FOR HOW LONG A USER IS CONSIDERED INACTIVE 10000 is 10 SECONDS, change THIS ONLY NOTHING ELSE
    }, 10000);
}

document.addEventListener('mousemove', notifyActive);
document.addEventListener('keydown', notifyActive);
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        notifyInactive();
    } else {
        notifyActive();
    }
});
window.addEventListener('load', () => {
    notifyActive();
});

//----------------------------------------------------------------------------------------
//feed with websockets

function createPost() {
    const postContent = document.getElementById("post-content").value;
    const uploadInput = document.getElementById("upload");
    const file = uploadInput.files[0];

    if (!postContent && !file) {
        alert("Must have: messege of media");
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        const imageData = e.target.result;
        socket.emit('newPost', { post_content: postContent, upload: imageData });
    };
    if (file) {
        reader.readAsArrayBuffer(file);
    } else {
        socket.emit('newPost', { post_content: postContent });
    }
    document.getElementById("post-content").value = "";
    document.getElementById("upload").value = null;
}

function updateFeedUI(posts) {
    const feedContainer = document.getElementById("feed-container");
    feedContainer.innerHTML = "";
    posts.forEach(post => {
        const postElement = document.createElement("div");
        postElement.className = "post";
        postElement.id = post.postID;

        postElement.innerHTML = `
            <p><strong>${post.author}:</strong> ${post.post_content}</p>
            ${post.filename ? `<img src="${post.filename}" alt="Post image" />` : ""}
            <p class="likes">Likes: ${post.likes}</p>
            <p class="likedBy">Liked by: ${post.likedBy.join(", ")}</p>
            <div class="post-actions">
                <button class="like" onclick="likeMessage('${post.postID}')">Like</button>
                <button class="share">Share</button>
                <button class="comment">Comment</button>
            </div>
        `;
        feedContainer.appendChild(postElement);
    });
}

function likeMessage(postID) {
    console.log("Here's your post: " + postID);
    socket.emit('likePost', { postID: postID });
}