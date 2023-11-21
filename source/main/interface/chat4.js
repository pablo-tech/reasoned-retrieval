document.getElementById('send-button').addEventListener('click', function() {
    var input = document.getElementById('chat-input');
    var message = input.value.trim();

    if (message) {
        addToChatWindow(message, "my-message", "user-avatar-url.png");
        input.value = '';

        // Simulate an API call
        apiCall(message, function(response) {
            addToChatWindow(response.reply, "bot-message", "bot-avatar-url.png");
            addToTraceWindow(response.traces, "bot-message", "thought-tracer.png");
        });
    }
});

function addToChatWindow(text, className, avatarUrl) {
    var chatWindow = document.getElementById('chat-window');
    var messageDiv = document.createElement('div');
    messageDiv.classList.add("message", className);

    var avatar = document.createElement('img');
    avatar.src = avatarUrl;
    avatar.classList.add("avatar");

    var messageText = document.createElement('div');
    messageText.classList.add("message-text");
    messageText.textContent = text;

    if (className === "my-message") {
        messageDiv.appendChild(messageText);
        messageDiv.appendChild(avatar);
    } else {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageText);
    }

    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to latest message
}

function addToTraceWindow(text, className, avatarUrl) {
    var traceWindow = document.getElementById('trace-window');
    var messageDiv = document.createElement('div');
    messageDiv.classList.add("message", className);

    var avatar = document.createElement('img');
    avatar.src = avatarUrl;
    avatar.classList.add("avatar");

    var messageText = document.createElement('div');
    messageText.classList.add("message-text");
    messageText.textContent = text;

    // if (className === "my-message") {
    //     messageDiv.appendChild(messageText);
    //     messageDiv.appendChild(avatar);
    // } else {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageText);
    // }

    traceWindow.appendChild(messageDiv);
    traceWindow.scrollTop = traceWindow.scrollHeight; // Auto-scroll to latest message
}

// function apiCall(message, callback) {
//     // Simulate an API response after 1 second
//     setTimeout(function() {
//         var response = "Response to '" + message + "'";
//         callback(response);
//     }, 1000);
// }

// ... existing code ...

function apiCall(message, callback) {
    fetch('http://localhost:5001/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        setTimeout(function() {
            // var response = "Response to '" + message + "'";
            callback(data);
            console.log("TRACES :",data.traces);
        }, 1000);
        
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
