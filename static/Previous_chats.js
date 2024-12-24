// Calling the session_id from flask backend
let currentSessionId = null;

// Get or create session ID when page loads
const InitializeSession = async () => {
    try {
        // First try to get existing session ID from your backend
        const response = await fetch('/get_session_id');
        const data = await response.json();  // converts backend's JSON reponse into a javascript object
        currentSessionId = data.session_id;
    } catch (error) {
        console.error("Could not get session ID: ", error);
    }
}

// Modified Previous Chats structure to work with sessions
const previous_chats = {
    // This will store chat histories by session ID
    sessions: new Map()
};

// Function to add a new chat session
const addChatSession = (sessionID) => {
    if(!previous_chats.sessions.has(sessionID)) {
        previous_chats.set(sessionID, {
            id: sessionID,
            name: `Chat Session ${sessionID}`,
            chats: []
        });
    }
    return previous_chats.sessions.get(sessionID);
};

// Function to get or create a chat session
const getOrCreateChatSession = (sessionId) => {
    if (!previous_chats.sessions.has(sessionId)) {
        return addChatSession(sessionId);
    }
    return previous_chats.sessions.get(sessionId);
};



// Modified render function to show all sessions
const renderPreviousChats = () => {
    summaryList.innerHTML = "";
    previous_chats.sessions.forEach((session) => {
        const li = document.createElement("li");
        li.textContent = session.name;
        li.addEventListener("click", () => loadChat(session.id));
        summaryList.appendChild(li);
    });
};

// Modified load chat function
const loadChat = (sessionId) => {
    chatList.innerHTML = "";
    const session = previous_chats.sessions.get(sessionId);
    
    if (session && session.chats) {
        session.chats.forEach((chatMessage) => {
            const messageDiv = document.createElement("div");
            messageDiv.classList.add("message", chatMessage.role === "user" ? "outgoing" : "incoming");
            
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

// Initialize everything
const initialize = async () => {
    await initializeSession();
    const currentSession = getOrCreateChatSession(currentSessionId);
    // If you have an existing chat array, add it to the current session
    if (chat && chat.length > 0) {
        currentSession.chats = chat;
    }
    renderPreviousChats();
};

// Start the initialization
initialize();

// Sample summaries data
const summaries = [
    { 
        id: 1, 
        name: "Chat History", 
        chats: chat  // This will reference the chat array from Interact_script.js
    }
];