document.addEventListener("DOMContentLoaded", function () {
    const roomName = JSON.parse(document.getElementById("json-roomid").textContent);
    const createdAt = JSON.parse(document.getElementById("created_at").textContent);
    const userName = JSON.parse(document.getElementById("json-email").textContent);

    // Define WebSocket connection
    let chatSocket;
    function connectWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        // Construct WebSocket URL
        const wsUrl = protocol + window.location.host + "/ws/chat/" + receiver_id + "/";
        console.log(wsUrl)
        chatSocket = new WebSocket(wsUrl);
        chatSocket.onopen = function () {
            console.log("WebSocket Connected");
        };

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            if (data.message) {
                appendMessage(data);
                scrollToBottom();
            } else {
                alert("The message was empty!");
            }
        };

        chatSocket.onerror = function (error) {
            console.error("WebSocket Error:", error);
        };

        chatSocket.onclose = function (e) {
            console.warn("WebSocket Closed. Attempting to reconnect...");
            setTimeout(connectWebSocket, 3000);
        };
    }

    // Establish WebSocket connection when page loads
    connectWebSocket();

    // Function to send message
    function sendMessage() {
        const messageInputDom = document.querySelector("#chat-message-input");
        const message = messageInputDom.value.trim();

        if (message === "") {
            return;
        }

        const data = JSON.stringify({
            action: "send_message",
            roomId:ROOM,
            message: message,
            email: userName,
            room: roomName,
            receiver: receiver_id,
            date: createdAt,
        });

        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(data);
        } else {
            connectWebSocket();
        }
        messageInputDom.value = "";
    }

    // Send Message on Button Click
    document.querySelector("#chat-message-submit").onclick = function (e) {
        e.preventDefault();
        sendMessage();
    };

    // Send Message on Enter Key Press (without Shift)
    document.querySelector("#chat-message-input").addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();  // Prevents new line in input
            sendMessage();
        }
    });

    function scrollToBottom() {
        console.log("scrollToBottom function called");
        const chatMessages = document.querySelector("#chat-body");
    
        if (!chatMessages) {
            console.error("Chat messages container not found!");
            return;
        }
        requestAnimationFrame(() => {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight + 100, // Scroll to bottom with offset
                behavior: 'smooth' // Optional: Smooth scrolling
            });
        });
    }
    

    function appendMessage(data) {
        const chatMessages = document.querySelector("#chat-messages");
        const isSender = data.email === userEmail;
        const messageClass = isSender ? "message-out" : "message-in";
        const profileUrl = isSender ? userProfileUrl : receiverProfileUrl;

        // Create message container
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", messageClass);

        messageDiv.innerHTML = `
            <a href="#" data-bs-toggle="modal" data-bs-target="#modal-profile" class="avatar avatar-responsive">
                <img class="avatar-img" src="${profileUrl}" alt="">
            </a>
            <div class="message-inner">
                <div class="message-body">
                    <div class="message-content">
                        <div class="message-text"><p>${data.message}</p></div>
                        <div class="message-action">
                            <div class="dropdown">
                                <a class="icon text-muted" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-more-vertical">
                                        <circle cx="12" cy="12" r="1"></circle>
                                        <circle cx="12" cy="5" r="1"></circle>
                                        <circle cx="12" cy="19" r="1"></circle>
                                    </svg>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a class="dropdown-item d-flex align-items-center" href="#"> <span class="me-auto">Edit</span></a></li>
                                    <li><a class="dropdown-item d-flex align-items-center" href="#"> <span class="me-auto">Reply</span></a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item d-flex align-items-center text-danger" href="#"> <span class="me-auto">Delete</span></a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="message-footer"><span class="extra-small text-muted">${data.created_at}</span></div>
            </div>`;
        chatMessages.appendChild(messageDiv);
    }

    function markMessagesAsRead(chatPartnerId) {
        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                type: "mark_read",
                roomId:ROOM,
                partner_id: chatPartnerId
            }));
        } else {
            console.error("WebSocket not connected");
        }
    }
    
});
