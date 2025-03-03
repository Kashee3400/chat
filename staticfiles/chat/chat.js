$(document).ready(function () {
    $("#chat_header_content").hide()
    $(".send-request-btn").click(function () {
        let requestId = $(this).data("receiver-id");
        $.ajax({
            url: "/chatroom/send-friend-request/",
            type: "POST",
            data: {
                request_id: requestId
            },
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            success: function (response) {
                showMessage(response.message, "success");
            },
            error: function (xhr) {
                let errorMessage = "An unexpected error occurred!";
                if (xhr.status === 400) {
                    errorMessage = xhr.responseJSON?.error || "Bad Request: Please check the input and try again.";
                } else if (xhr.status === 403) {
                    errorMessage = "Forbidden: You don't have permission to perform this action.";
                } else if (xhr.status === 404) {
                    errorMessage = "Error: The requested user was not found.";
                } else if (xhr.status === 500) {
                    errorMessage = "Server Error: Something went wrong on our end. Please try again later.";
                }
                showMessage(errorMessage, "danger");
            }
        });
    });



    $(".update-friend-status").click(function () {
        let status = $(this).data("status");
        let requestId = $(this).data("request-id");
        $.ajax({
            url: "/chatroom/update-friend-request/",
            type: "POST",
            data: {
                status: status,
                request_id: requestId
            },
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            success: function (response) {
                showMessage(response.message, "success");
                window.location.reload()
            },
            error: function (xhr) {
                let errorMessage = "An unexpected error occurred!";
                if (xhr.status === 400) {
                    errorMessage = xhr.responseJSON?.error || "Bad Request: Please check the input and try again.";
                } else if (xhr.status === 403) {
                    errorMessage = "Forbidden: You don't have permission to perform this action.";
                } else if (xhr.status === 404) {
                    errorMessage = "Error: The requested user was not found.";
                } else if (xhr.status === 500) {
                    errorMessage = "Server Error: Something went wrong on our end. Please try again later.";
                }

                showMessage(errorMessage, "danger");
            }
        });

    });


    // Function to display success/error messages dynamically
    function showMessage(message, type) {
        let messageContainer = $("#message-container");
        messageContainer.html(`
            <div class="alert m-4 alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);
    }
    $(".chat-link").on("click", function (e) {
        e.preventDefault();
        let slug = $(this).data("slug");
    
        $.ajax({
            url: `/chatroom/load-chat/discover/${slug}/`,
            type: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            success: function (data) {
                $("#chat_header_content").show();
                $(".chat-footer").show();
                $(".chat-header").html(data.chat_header_html);
                $("#chat-messages").html(data.messages_html);
                $("#chat-message-input").val("").focus();
                // If mobile, apply chat-container class
                if ($(window).width() < 768) {
                    $("main").addClass("is-visible");
                }
                $.getScript("/static/chat/one_to_one_chat.js");
                scrollToBottom();
                // ✅ Reattach event listener for #toggle-chat after updating chat-header
                $("#toggle-chat").off("click").on("click", function () {
                    console.log("Toggle chat");
                    $("main").toggleClass("is-visible");
                    disconnectChatSocket()
                });
            },
            error: function (xhr, status, error) {
                console.error("Error loading chat:", error);
            }
        });
    });
    function disconnectChatSocket() {
        if (window.chatSocket && window.chatSocket.readyState === WebSocket.OPEN) {
            console.log("Closing WebSocket connection...");
            window.chatSocket.close();
            window.chatSocket = null; // Optional: Remove reference
        } else {
            console.log("WebSocket is already closed or not initialized.");
        }
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

});

function getCSRFToken() {
    let csrfToken = null;
    const cookies = document.cookie.split(';');

    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith("csrftoken=")) {
            csrfToken = cookie.split("=")[1];
            break;
        }
    }

    return csrfToken;
}
