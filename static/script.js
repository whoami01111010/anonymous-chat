const socket = io("http://192.168.221.31:5000");

let username = "";
const loginScreen = document.getElementById("login-screen");
const chatScreen = document.getElementById("chat-screen");
const messagesDiv = document.getElementById("messages");

function joinChat() {
    username = document.getElementById("username").value;
    if (username.trim() === "") {
        alert("Please enter a username");
        return;
    }

    loginScreen.style.display = "none";
    chatScreen.style.display = "flex";
}

socket.on("message", (msg) => {
    const msgElement = document.createElement("p");
    msgElement.innerHTML = `<strong>${msg.user}:</strong> ${msg.text}`;
    messagesDiv.appendChild(msgElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});

function sendMessage() {
    const message = document.getElementById("message").value;
    if (message.trim() !== "") {
        socket.send({ user: username, text: message });
        document.getElementById("message").value = "";
    }
}
