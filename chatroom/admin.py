from django.contrib import admin

from chatroom import models


@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug']


import json
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from . import models  # Import your models

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

@admin.register(models.State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'country', 'created_at', 'updated_at']
    list_filter = ['country']
    actions = [populate_states_from_json]  # Add the action here



@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'country', 'category_type', 'fee_status', 'ordering',
        'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['category_type', 'fee_status', 'is_active']
    search_fields = ['name']


@admin.register(models.SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'category', 'name', 'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name']


@admin.register(models.ChatRoomUser)
class ChatRoomUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'user', 'created_at', 'updated_at']


@admin.register(models.DirectmessageUser)
class DirectmessageUserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'me', 'friends', 'friend_type', 'created_at', 'updated_at'
    ]


@admin.register(models.RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'user', 'created_at', 'updated_at']


@admin.register(models.DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'sender_user', 'receiver_user', 'created_at', 'updated_at'
    ]


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'created_at', 'updated_at']
