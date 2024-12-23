// Sample summaries data
const summaries = [
    { 
        id: 1, 
        name: "Chat History", 
        chats: chat  // This will reference the chat array from Interact_script.js
    }
];

// Reference to the summary list and chat container
const summaryList = document.getElementById("summary-list");
const chatList = document.querySelector(".chat-list");

// Function to render summaries list
const renderSummaries = () => {
    summaryList.innerHTML = ""; // Clear existing list
    summaries.forEach((summary) => {
        const li = document.createElement("li");
        li.textContent = summary.name;
        li.addEventListener("click", () => loadChat(summary.id));
        summaryList.appendChild(li);
    });
};

// Function to load chat based on selected summary
const loadChat = (summaryId) => {
    // Clear previous chat messages
    chatList.innerHTML = "";

    // Find the selected summary
    const selectedSummary = summaries.find((summary) => summary.id === summaryId);

    if (selectedSummary && selectedSummary.chats) {
        // Load the chats
        selectedSummary.chats.forEach((chatMessage) => {
            const messageDiv = document.createElement("div");
            messageDiv.classList.add("message", chatMessage.role === "user" ? "outgoing" : "incoming");
            
            // Create the message content
            const html = `
                <div class="message-content">
                    <img src="/static/${chatMessage.role === 'user' ? 'user.jpg' : 'Logo.png'}" alt="${chatMessage.role} image" class="avatar">
                    <p class="text">${chatMessage.message}</p>
                </div>
            `;
            messageDiv.innerHTML = html;
            chatList.appendChild(messageDiv);
        });
    }
};

// Initialize
renderSummaries();