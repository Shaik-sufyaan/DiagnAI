const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});

window.addEventListener("beforeunload", function () {
    navigator.sendBeacon("/session-end");
});

function handleGoogleLogin() {
    console.log('Google login button clicked');
    // For Flask template
    window.location.href = '/google-login';
}