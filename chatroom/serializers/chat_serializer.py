# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth import get_user_model
# from chatroom.models.category import CallLog,TextMessage,ChatRoomModel
# CustomUser = get_user_model()

# class CustomUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['id', 'username', 'email', 'is_astrologer', 'is_client']
#         read_only_fields = ['id']

#     def validate_username(self, value):
#         """Custom validation for the username."""
#         if not value.isalnum():
#             raise serializers.ValidationError("Username must be alphanumeric.")
#         return value

#     def validate_email(self, value):
#         """Custom validation for the email."""
#         if CustomUser.objects.filter(email=value).exists():
#             raise serializers.ValidationError("Email is already in use.")
#         return value

# from rest_framework import serializers


# class CallMessageSerializer(serializers.ModelSerializer):
#     """_summary_

#     Args:
#         serializers (_type_): _description_

#     Returns:
#         {
#             "id": 1,
#             "chat_room": 3,
#             "sender_username": "alice",
#             "call": 5,
#             "call_details": {
#                 "id": 5,
#                 "start_time": "2024-10-27T12:34:56Z",
#                 "duration": 300,  // Duration in seconds
#                 "participants": ["alice", "bob", "charlie"]
#             },
#             "sent_at": "2024-10-27T12:35:45Z",
#             "delivered_at": null,
#             "seen_at": null
#         }

#     """
#     sender_username = serializers.ReadOnlyField(source='sender.username')
#     call_details = serializers.SerializerMethodField()

#     class Meta:
#         model = CallLog
#         fields = ['id','chat_room__id', 'caller__email', 'receiver__email', 'started_at', 'ended_at', 'call_type', 'status']
#         read_only_fields = ['id', 'sender_username', 'sent_at', 'delivered_at', 'seen_at']



# class TextMessageSerializer(serializers.ModelSerializer):
    
#     """_summary_

#     Raises:
#         serializers.ValidationError: _description_

#     Returns:
#         {
#             "id": 1,
#             "chat_room": 3,
#             "sender_username": "alice",
#             "msg": "Hello!",
#             "is_edited": false,
#             "old_msg": null,
#             "reply_to": {
#                 "id": 2,
#                 "msg": "Hey, how are you?",
#                 "sender": "bob",
#                 "sent_at": "2024-10-27T12:34:56Z"
#             },
#             "sent_at": "2024-10-27T12:35:45Z",
#             "delivered_at": null,
#             "seen_at": null
#         }

#     """
#     # chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoomModel.objects.all())
#     chat_room = serializers.StringRelatedField()
#     reply_to = serializers.SerializerMethodField()
#     class Meta:
#         model = TextMessage
#         fields = ['id',
#                 'slug',
#                 'chat_room',
#                 'sender',
#                 'msg', 
#                 'is_edited',
#                 'old_msg', 
#                 'reply_to',
#                 'sent_at',
#                 'image_paths',
#                 'message_type', 
#                 'delivered_at', 
#                 'seen_at',
#                 'created_at',
#                 'updated_at',
#                 'synced',
#                 'local_path',
#                 'status',
#                 ]
#         read_only_fields = ['id', 'sender', 'sent_at', 'delivered_at', 'seen_at','is_me','created_at']
    
#     def get_reply_to(self, obj):
#         """
#         Returns a summarized version of the message being replied to, if applicable.
#         Includes the ID and message text of the replied-to message.
#         """
#         if obj.reply_to:
#             return obj.slug
#         return None

#     def validate_msg(self, value):
#         """Custom validation for message content."""
#         if not value.strip():
#             raise serializers.ValidationError("Message cannot be empty.")
#         return value


# class ChatRoomSerializer(serializers.ModelSerializer):
#     messages = serializers.SerializerMethodField()
#     calls = serializers.SerializerMethodField()

#     class Meta:
#         model = ChatRoomModel
#         fields = ['id', 'room_name', 'room_type', 'created','participants','messages','calls']
#         read_only_fields = ['messages','calls']

#     def get_messages(self, obj):
#         """Serialize and combine text, media, and reply messages."""
#         combined_data = self.context.get('combined_data', {})

#         # Serialize text, media, and reply messages
#         text_serializer = TextMessageSerializer(combined_data.get('text_messages'), many=True)

#         # Combine and sort messages by 'sent_at'
#         combined_messages = self.combine_and_sort_messages(
#             text_serializer.data,
#         )

#         return combined_messages

#     def get_calls(self, obj):
#         """Serialize the call data."""
#         combined_data = self.context.get('combined_data', {})

#         call_serializer = CallMessageSerializer(combined_data.get('calls'), many=True)
#         return call_serializer.data

#     def combine_and_sort_messages(self, *message_sets):
#         """Helper function to combine and sort messages by 'sent_at'."""
#         combined_messages = []
#         for messages in message_sets:
#             combined_messages.extend(messages)
#         return sorted(combined_messages, key=lambda x: x['sent_at'])


#     def validate(self, attrs):
#         """Custom validation for chat room attributes if needed."""
#         if 'messages' in attrs and len(attrs['messages']) > 100:
#             raise serializers.ValidationError("A chat room cannot have more than 100 messages at a time.")
#         return attrs


