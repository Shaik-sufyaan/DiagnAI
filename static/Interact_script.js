const typingForm = document.querySelector(".typing-form");
const chatList = document.querySelector(".chat-list");
let userMessage = null;
let API_URL = ""; // Dynamically set later


// Fetch API key securely from Flask backend
const fetchApiKey = async () => {
    try {
        const response = await fetch('/get_api_key');
        const data = await response.json();
        if (data.api_key) {
            return data.api_key;
        } else {
            console.error("API key not returned:", data.error);
            return null;
        }
    } catch (error) {
        console.error("Error fetching API key:", error);
        return null;
    }
};

// Initialize API URL dynamically
const initializeApiUrl = async () => {
    const apiKey = await fetchApiKey();
    if (apiKey) {
        API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
        console.log("API URL initialized:", API_URL);
    } else {
        console.error("Failed to fetch API key");
    }
};

// Call the function to initialize the API URL when the page loads
initializeApiUrl();


// Create a new message element and return it
const createMessageElement = (content, className) => {
    const div = document.createElement("div");
    div.classList.add("message", className);
    div.innerHTML = content;
    return div;
};

// Fetch response from the API based on the user's message
// Update the generateAPIResponse function
const generateAPIResponse = async (incomingMessageDiv) => {
    const textElement = incomingMessageDiv.querySelector(".text");

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
        
        if (data.candidates && data.candidates[0] && data.candidates[0].content) {
            const apiResponse = data.candidates[0].content.parts[0].text;
            textElement.innerHTML = ''; // Clear the "Thinking..." text
            await typeText(textElement, apiResponse);
            scrollToBottom(chatList);
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
// Update the handleOutgoingChat function
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
    scrollToBottom(chatList);

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

// Add these utility functions at the top of your script
const typeText = async (element, text, speed = 40) => {
    element.innerHTML = '';
    let index = 0;
    
    return new Promise((resolve) => {
        function addCharacter() {
            if (index < text.length) {
                element.innerHTML += text.charAt(index);
                index++;
                setTimeout(addCharacter, speed);
            } else {
                resolve();
            }
        }
        addCharacter();
    });
};

const scrollToBottom = (element, smooth = true) => {
    const options = {
        top: element.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
    };
    element.scrollTo(options);
};

// Add styles to maintain smooth animations
const styleSheet = document.createElement("style");

document.head.appendChild(styleSheet);


// Test the API connection when the page loads
testAPIConnection();