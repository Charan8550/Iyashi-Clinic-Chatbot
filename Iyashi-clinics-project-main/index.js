const launcher = document.getElementById("chatbot-launcher");
const container = document.getElementById("chatbot-container");
const closeBtn = document.getElementById("close-chat");
const chatBody = document.getElementById("chat-body");
const userInput = document.getElementById("user-input");

launcher.onclick = () => {
    container.classList.toggle("hidden");
    if (!container.classList.contains("hidden") && chatBody.innerHTML.trim() === "") {
        addMessage("Hello 👋 Welcome to Iyashi Clinics! How can we assist you with our wellness or surgical services today?", "bot-msg");
    }
};

closeBtn.onclick = () => container.classList.add("hidden");

function addMessage(text, className) {
    const msgDiv = document.createElement("div");
    msgDiv.className = className;
    msgDiv.innerText = text;
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, "user-msg");
    userInput.value = "";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        addMessage(data.reply, "bot-msg");
    } catch (error) {
        addMessage("I'm having trouble connecting. Please try again later.", "bot-msg");
    }
}

function quickReply(label) {
    userInput.value = label;
    sendMessage();
}

userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});