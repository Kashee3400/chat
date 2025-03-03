document.addEventListener("DOMContentLoaded", function () {
    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    // Construct WebSocket URL
    const wsUrl = protocol + window.location.host + "/ws/friends/" + CURRENT_USER_ID + "/";
    let socket = new WebSocket(wsUrl);

    connectFriendWebSocket();
    function connectFriendWebSocket() {
        socket.onopen = function () {
        };
        socket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.action === "friend_update") {
                updateFriendList(data);
            } else if (data.action === "unread_count") {
                updateUnreadBadge(data.user_id, data.unread_count);
            }
            if (data.action === "friend_request") {
                incrementRequestCount()
                alert(`🔔 Notification: ${data.message}`);
            }
        };

        socket.onerror = function (error) {
            console.error("WebSocket Error:", error);
        };

        socket.onclose = function () {
            console.warn("Friend WebSocket Closed. Attempting to reconnect...");
            setTimeout(() => connectFriendWebSocket(), 3000);
        };

        return socket;
    }

    function updateFriendList(data) {
        const userId = data.sender_id;
        const message = data.last_message;
        const time = data.time;
        const unreadCount = data.unread_count;
        let friendList = document.getElementById("friends-list");
        if (!friendList) {
            return;
        }
        let userCard = document.querySelector(`#user_card_${userId}`);
        if (userCard) {
            // ✅ Move the existing card to the top without duplication
            let lastMessageElement = document.getElementById(`friend-last-message-${userId}`);
            let lastMessageTimeElement = document.getElementById(`friend-last-message-time-${userId}`);
            if (lastMessageElement) {
                lastMessageElement.textContent = message;
            }
            if (lastMessageTimeElement) {
                lastMessageTimeElement.textContent = time;
            }
            updateUnreadBadge(userId, unreadCount);
            friendList.prepend(userCard);

        } else {
            console.warn(`User card for ${userId} not found!`);
        }
    }


    function updateUnreadBadge(userId, count) {
        let badge = document.getElementById(`friend-unread-badge-${userId}`);
        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = "flex";
            } else {
                badge.style.display = "none";
            }
        }
    }
    function incrementRequestCount() {
        const requestCountElement = document.getElementById("request_count");

        if (requestCountElement) {
            let currentCount = parseInt(requestCountElement.textContent) || 0; // Get current count, default to 0
            let newCount = currentCount + 1; // Increment by 1
            requestCountElement.textContent = newCount;
            requestCountElement.style.display = newCount > 0 ? "inline-block" : "none";
        }
    }

});
