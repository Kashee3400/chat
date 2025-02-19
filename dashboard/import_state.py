import json
from chatroom.models import Country, State

def loadstate():
    with open('dashboard/states.json', encoding='utf-8') as f:  # Specify UTF-8 encoding
        data = json.load(f)
        counter = 0
        for state in data:
            counter += 1
            state_name = state['name']
            country_name = state['country_name']
            try:
                country = Country.objects.get(name=country_name)
                state_obj, created = State.objects.get_or_create(country=country, name=state_name)
                print(f"{counter} - {'Created' if created else 'Already exists'}: {state_obj}")
            except Country.DoesNotExist:
                print(f"{country_name} is not found in country list")
        print(f"Total States Processed: {counter}")
