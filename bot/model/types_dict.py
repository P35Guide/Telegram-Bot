class SearchTypes:
    """Централізоване сховище всіх типів настроїв і категорій."""
    
    mood_types: dict = {
        "Loud Company 🍻": list((
            "stadium", "dance_hall", "karaoke", "bar", 
            "night_club", "comedy_club", "live_music_venue", "event_venue"
        )),
        "Date Night 🌙": list((
            "restaurant", "cafe", "bakery", "fine_dining_restaurant",
            "italian_restaurant", "french_restaurant", "seafood_restaurant",
            "wine_bar", "cocktail_bar", "sushi_restaurant", "dessert_shop",
            "art_gallery", "movie_theater", "spa"
        )),
        "Need to Work 💻": list((
            "restaurant", "cafe", "coworking_space", "library", "book_store",
            "coffee_shop", "bakery"
        )),
        "Breakfast at 2 PM 🥞": list((
            "cafe", "coffee_shop", "bakery", "breakfast_restaurant",
            "brunch_restaurant", "sandwich_shop", "dessert_shop"
        ))
    }
    
    mood_code_map: dict = {
        "company": "Loud Company 🍻",
        "date": "Date Night 🌙",
        "work": "Need to Work 💻",
        "breakfast": "Breakfast at 2 PM 🥞",
    }
    
    category: dict = {
        "cafe": "coffee_shop",
        "restaurant": "restaurant",
        "bar": "bar",
        "bakery": "bakery",
        "fast_food": "fast_food_restaurant"
    }
