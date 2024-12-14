const typingForm = document.querySelector(".typing-form");
const chatList = document.querySelector(".chat-list");
let userMessage = null;

const YOUR_API_KEY = "AIzaSyDmv-PERaSug-_qNCm6pDUcKYZSl3qaqPQ";
const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${YOUR_API_KEY}`;

// Create a new message element and return it
const createMessageElement = (content, className) => {
    const div = document.createElement("div");
    div.classList.add("message", className);
    div.innerHTML = content;
    return div;
};

// Fetch response from the API based on the user's message
const generateAPIResponse = async (incomingMessageDiv) => {
    const textElement = incomingMessageDiv.querySelector(".text");

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                // Updated request format for Gemini
                contents: [{
                    role: "user",
                    parts: [{
                        text: userMessage
                    }]
                }],
                generationConfig: {
                    temperature: 0.7,
                    topK: 40,
                    topP: 0.95,
                    maxOutputTokens: 1024,
                }
            })
        });

        if (!response.ok) {
            throw new Error(`API returned status ${response.status}`);
        }

        const data = await response.json();
        console.log('API Response:', data); // For debugging

        // Updated response parsing for Gemini
        if (data.candidates && data.candidates[0] && data.candidates[0].content) {
            const apiResponse = data.candidates[0].content.parts[0].text;
            textElement.innerText = apiResponse || "No response text received.";
        } else {
            textElement.innerText = "Received unexpected response format from API.";
            console.error('Unexpected response structure:', data);
        }
    } catch (error) {
        console.error("Error:", error);
        textElement.innerText = "An error occurred while fetching the response.";
    } finally {
        incomingMessageDiv.classList.remove("loading");
    }
};

// Show a loading animation while waiting for the API response
const showLoadingAnimation = () => {
    const html = `
        <div class="message-content">
            <img src="/static/Logo.png" alt="Bot image" class="avatar">
            <p class="text">Thinking...</p>
        </div>
    `;
    const incomingMessageDiv = createMessageElement(html, "incoming");
    incomingMessageDiv.classList.add("loading");
    chatList.appendChild(incomingMessageDiv);
    
    generateAPIResponse(incomingMessageDiv);
};

// Handle outgoing chat message
const handleOutgoingChat = () => {
    userMessage = typingForm.querySelector(".typing-input").value.trim();
    if (!userMessage) return;

    const html = `
        <div class="message-content">
            <img src="/static/user.jpg" alt="User image" class="avatar">
            <p class="text">${userMessage}</p>
        </div>
    `;
    
    const outgoingMessageDiv = createMessageElement(html, "outgoing");
    chatList.appendChild(outgoingMessageDiv);

    typingForm.querySelector(".typing-input").value = "";
    showLoadingAnimation();
};

// Event listener for form submission
typingForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleOutgoingChat();
});

// Add this to check if the API key is working
const testAPIConnection = async () => {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: [{
                    role: "user",
                    parts: [{
                        text: "Hello, are you working?"
                    }]
                }],
                generationConfig: {
                    temperature: 0.7,
                    topK: 40,
                    topP: 0.95,
                    maxOutputTokens: 1024,
                }
            })
        });
        const data = await response.json();
        console.log('API Test Response:', data);
    } catch (error) {
        console.error('API Test Error:', error);
    }
};

// Test the API connection when the page loads
testAPIConnection();