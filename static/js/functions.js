f// Emit a WebSocket event to create a new post
function createPost() {
    const postContent = document.getElementById("post-content").value;
    const uploadInput = document.getElementById("upload");
    const file = uploadInput.files[0];

    if (!postContent && !file) {
        alert("You need to provide some content or an image!");
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        const imageData = e.target.result; // Base64 encoded image data
        socket.emit('newPost', { post_content: postContent, upload: imageData });
    };

    if (file) {
        reader.readAsArrayBuffer(file);
    } else {
        // Send the post content without an image
        socket.emit('newPost', { post_content: postContent });
    }

    // Clear the input fields
    document.getElementById("post-content").value = "";
    document.getElementById("upload").value = null;
}

// Update the feed UI dynamically
function updateFeedUI(posts) {
    const feedContainer = document.getElementById("feed-container");
    feedContainer.innerHTML = ""; // Clear the current feed

    posts.forEach(post => {
        const postElement = document.createElement("div");
        postElement.className = "post";
        postElement.id = post.postID;

        // Post content
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

// Emit a WebSocket event to like a post
function likeMessage(postID) {
    console.log("Here's your post: " + postID);
    socket.emit('likePost', { postID: postID });
}