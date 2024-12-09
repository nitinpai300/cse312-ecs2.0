function createPost() {
    const postContent = document.getElementById("post-content").value;
    const uploadInput = document.getElementById("upload");
    const file = uploadInput.files[0];

    if (!postContent && !file) {
        alert("Must have: message of media");
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