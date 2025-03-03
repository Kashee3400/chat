$(document).ready(function () {
    const createdAt = JSON.parse($("#created_at").text());
    const userName = JSON.parse($("#json-email").text());
    // WebSocket connection
    function updateChatVars() {
        const chatVars = $("#chat-vars");
        if (chatVars.length) {
            window.ROOM = chatVars.attr("data-room-id");
            window.RECEIVER_ID = chatVars.attr("data-receiver-id");
            window.userProfileUrl = chatVars.attr("data-sender-profile");
            window.receiverProfileUrl = chatVars.attr("data-receiver-profile");
        }
    }
    updateChatVars();
    let chatSocket = connectWebSocket();
    function connectWebSocket() {
        if (window.chatSocket) {
            window.chatSocket.close();
        }

        const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const wsUrl = `${protocol}${window.location.host}/ws/one-to-one-chat/${RECEIVER_ID}/${ROOM}/`;
        window.chatSocket = new WebSocket(wsUrl);
        window.chatSocket.onopen = function () {

        };

        window.chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            if (data.message) {
                if (data.type === "chat_message") {
                    appendMessage(data);
                }
            }
            else if (data.type === "update_message_status") {
                updateMessageStatus(data);
            }
        };
        window.chatSocket.onerror = function (error) {
        };
        window.chatSocket.onclose = function () {
        };
        return window.chatSocket;
    }

    function sendMessage() {
        const messageInputDom = $("#chat-message-input");
        const message = messageInputDom.val().trim();
        if (message === "") {
            return;
        }
        const data = JSON.stringify({
            action: "send_message",
            roomId: ROOM,
            message: message,
            email: userName,
            receiver: RECEIVER_ID,
            date: createdAt,
        });

        if (window.chatSocket && window.chatSocket.readyState === WebSocket.OPEN) {
            window.chatSocket.send(data);
            messageInputDom.val("").focus(); 
        } else {
            window.chatSocket = connectWebSocket();
        }

        messageInputDom.val(""); // Clear input field
    }

    function scrollToBottom() {
        const chatMessages = document.querySelector(".chat-body");
        if (!chatMessages) {
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
        const chatMessages = $("#chat-messages");
        window.SENDER = data.email === userEmail;
        const messageClass = window.SENDER ? "message-out" : "message-in";
        const profileUrl = window.SENDER ? userProfileUrl : receiverProfileUrl;
        let messageStatus = "";
        if (window.SENDER) {
            messageStatus = getMessageStatusIcon(data);
        }
        // .message[data-id='${messageId}'] .message-status
        let messageDiv = `
            <div class="message ${messageClass}" data-id="${data.id}">
                <a href="#" data-bs-toggle="modal" data-bs-target="#modal-profile" class="avatar avatar-responsive">
                    <img class="avatar-img" src="${profileUrl}" alt="">
                </a>
                <div class="message-inner">
                    <div class="message-body">
                        <div class="message-content">
                            <div class="message-text"><p>${data.message}</p></div>
                        </div>
                    </div>
                    <div class="message-footer">
                        <span class="extra-small text-muted">${data.created_at}</span>
                        ${window.SENDER ? `<span class="extra-small text-muted message-status">${messageStatus}</span>` : ""}
                    </div>
                </div>
            </div>`;

        chatMessages.append(messageDiv);
        scrollToBottom();
        if (!window.SENDER) {
            markMessageAsSeen(data.id)
        }
    }

    // Function to get message status icon
    function getMessageStatusIcon(data) {
        let iconPath = "/static/chat/icons/";
        if (data.seen_at) {
            iconPath += "seen.svg";
        } else if (data.delivered_at) {
            iconPath += "delivered.svg";
        } else {
            iconPath += "sent.svg";
        }
        return `<img src="${iconPath}" width="20" height="20" alt="Message Status">`;
    }

    // Event Delegation for dynamic elements
    $(document).on("keydown", "#chat-message-input", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    $(document).on("click", "#chat-message-submit", function (e) {
        e.preventDefault();
        sendMessage();
    });
    $(document).on("visibilitychange", function () {
        if (!document.hidden) {
            let lastMessageId = getLastUnreadMessageId(); // Implement this function
            if (lastMessageId && !window.SENDER) {
                markMessageAsSeen(lastMessageId);
            }
        }
    });

    // Detect when the user scrolls to the bottom of the chat
    $("#chat-body").on("scroll", function () {
        if (isChatScrolledToBottom()) {
            let lastMessageId = getLastUnreadMessageId();
            if (lastMessageId && !window.SENDER) {
                markMessageAsSeen(lastMessageId);
            }
        }
    });

    // Function to check if chat is scrolled to bottom
    function isChatScrolledToBottom() {
        let chatContainer = $("#chat-body");
        return chatContainer[0].scrollHeight - chatContainer.scrollTop() <= chatContainer.outerHeight() + 10;
    }

    // Function to send "seen" status
    function markMessageAsSeen(messageId) {
        if (window.chatSocket.readyState === WebSocket.OPEN) {
            window.chatSocket.send(JSON.stringify({
                type: "seen",
                id: messageId,
                action: "seen",
                receiverId: window.RECEIVER_ID,
            }));
        }
    }

    // Function to send "delivered" status to the server
    function markMessageAsDelivered(messageId) {
        if (window.chatSocket.readyState === WebSocket.OPEN) {
            window.chatSocket.send(JSON.stringify({
                type: "delivered",
                action: "delivered",
                id: messageId
            }));
        }
    }
    // Function to update message status based on WebSocket event
    function updateMessageStatus(data) {
        let messageElement = $(`.message[data-id='${data.id}'] .message-status`);
        if (messageElement.length > 0) {
            messageElement.html(getMessageStatusIcon(data));
            messageElement.fadeOut(200, function () { // Step 1: Fade Out
                $(this).html(getMessageStatusIcon(data)).fadeIn(200); // Step 2: Change & Fade In
            });
        }
    }

    function getLastUnreadMessageId() {
        let unreadMessages = $(".message.unread");
        if (unreadMessages.length > 0) {
            let lastMessage = unreadMessages.last();
            let messageId = lastMessage.data("id");
            return messageId ? messageId : null; // Ensure messageId is valid
        }
        return null;
    }
});
