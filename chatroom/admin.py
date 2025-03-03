from django.contrib import admin
import json
from django.contrib import messages
from chatroom.models.country import * 
from chatroom.models.contact import *
from chatroom.models.category import *

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug']



def populate_states_from_json(modeladmin, request, queryset):
    """Admin action to populate states from a JSON file based on country_id."""
    try:
        with open("dashboard/states.json", encoding="utf-8") as f:
            data = json.load(f)

        counter = 0
        for state in data:
            state_name = state["name"]
            country_id = state.get("country_id")  # Get country_id from JSON

            try:
                # Fetch country by its ID
                country = models.Country.objects.get(pk=country_id)
                
                # Create the state only if the country exists
                state_obj, created = models.State.objects.get_or_create(
                    country=country,
                    name=state_name
                )
                counter += 1

            except models.Country.DoesNotExist:
                messages.warning(request, f"Skipping {state_name}: Country with ID {country_id} not found.")

        messages.success(request, f"Successfully added/updated {counter} states.")

    except Exception as e:
        messages.error(request, f"Error loading states: {str(e)}")

populate_states_from_json.short_description = "Populate States from JSON"

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'country', 'created_at', 'updated_at']
    list_filter = ['country']
    actions = [populate_states_from_json]  # Add the action here



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'country', 'category_type', 'fee_status', 'ordering',
        'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['category_type', 'fee_status', 'is_active']
    search_fields = ['name']


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'category', 'name', 'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name']


@admin.register(ChatRoomUser)
class ChatRoomUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'user', 'created_at', 'updated_at']


@admin.register(DirectMessageUser)
class DirectmessageUserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'me', 'friends', 'friend_type', 'created_at', 'updated_at'
    ]


@admin.register(RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'user', 'created_at', 'updated_at']


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'sender_user', 'receiver_user', 'created_at', 'updated_at'
    ]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'created_at', 'updated_at']



class ChatRoomModelAdmin(admin.ModelAdmin):
    list_display = ('id','room_name', 'room_type', 'created_at','created_by','updated_by','deleted_at')
    search_fields = ('room_name',)
    list_filter = ('room_type','created_at','deleted_at')
    fields = ('room_name','room_type','is_deleted','participants')
    filter_horizontal = ('participants',)
    readonly_fields = ('created_by','updated_by','slug')


class MediaTypeAdmin(admin.ModelAdmin):
    list_display = ('type', 'description', 'icon')
    search_fields = ('type',)
    list_filter = ('type',)

    fieldsets = (
        (None, {
            'fields': ('type', 'description', 'icon', 'allowed_extensions')
        }),
    )

class MediaSettingsAdmin(admin.ModelAdmin):
    list_display = ('media_type', 'max_size', 'max_length', 'max_files')
    search_fields = ('media_type__type',)
    list_filter = ('media_type',)

    fieldsets = (
        (None, {
            'fields': ('media_type', 'max_size', 'max_length', 'max_files', 'additional_fields')
        }),
    )
    
class ReportUserModelAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reported_user', 'reason', 'created_at')
    search_fields = ('reporter__username', 'reported_user__username', 'reason')
    list_filter = ('reason',)

class UserStatusModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_online', 'last_online', 'scheduled_start', 'scheduled_end')
    search_fields = ('user__username',)

class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('chat_room', 'blocked_user')
    search_fields = ('chat_room__room_name', 'blocked_user__username')
    list_filter = ('chat_room',)

class ChatModelAdmin(admin.ModelAdmin):
    list_display = ('chat_room','msg', 'sender', 'is_deleted', 'created_at','delivered_at','seen_at')
    search_fields = ('sender__username', 'msg')
    list_filter = ('is_deleted',)


admin.site.register(MediaType, MediaTypeAdmin)
admin.site.register(MediaSettings, MediaSettingsAdmin)
admin.site.register(ChatRoomModel, ChatRoomModelAdmin)
admin.site.register(ReportUserModel, ReportUserModelAdmin)
admin.site.register(UserStatusModel, UserStatusModelAdmin)
admin.site.register(TextMessage, ChatModelAdmin)
admin.site.register(BlockedUser, BlockedUserAdmin)
