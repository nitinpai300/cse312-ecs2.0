function changeProfile() {
    const uploadInput = document.getElementById("upload");
    const file = uploadInput.files[0];

    if (!file) {
        alert("Must choose an image");
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

}