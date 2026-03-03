class SearchTypes:
    """Централізоване сховище всіх типів настроїв і категорій."""
    
    mood_types: dict = {
        "Loud Company 🍻": list((
            "stadium", "dance_hall", "karaoke", "bar", 
            "night_club", "comedy_club", "live_music_venue", "event_venue"
        )),
        "Date Night 🌙": list((
            "restaurant", "cafe", "bakery", "fine_dining_restaurant",
            "italian_restaurant", "french_restaurant", "seafood_restaurant"
        )),
        "Need to Work 💻": list((
            "restaurant", "cafe", "coworking_space", "library", "book_store"
        ))
    }
    
    category: dict = {
        "cafe": "coffee_shop",
        "restaurant": "restaurant",
        "bar": "bar",
        "bakery": "bakery",
        "fast_food": "fast_food_restaurant"
    }
