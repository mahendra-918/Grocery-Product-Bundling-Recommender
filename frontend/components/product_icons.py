"""
Grocery SKU icons and category classifier.
Provides visual iconography and department groupings for all 169 catalog products.
"""

from typing import Tuple

CATEGORY_ICONS = {
    "Dairy & Eggs": "🥛",
    "Fresh Produce": "🥦",
    "Bakery & Grains": "🍞",
    "Meat & Seafood": "🥩",
    "Beverages": "🥤",
    "Pantry & Cooking": "🧂",
    "Snacks & Sweets": "🍪",
    "Personal & Home": "🧼",
}

PRODUCT_MAPPINGS = {
    # Dairy
    "whole milk": ("Dairy & Eggs", "🥛"),
    "yogurt": ("Dairy & Eggs", "🥣"),
    "butter": ("Dairy & Eggs", "🧈"),
    "curd": ("Dairy & Eggs", "🥣"),
    "other vegetables": ("Fresh Produce", "🥦"),
    "root vegetables": ("Fresh Produce", "🥕"),
    "tropical fruit": ("Fresh Produce", "🍍"),
    "citrus fruit": ("Fresh Produce", "🍊"),
    "pip fruit": ("Fresh Produce", "🍎"),
    "berries": ("Fresh Produce", "🍓"),
    "grapes": ("Fresh Produce", "🍇"),
    "onions": ("Fresh Produce", "🧅"),
    "rolls/buns": ("Bakery & Grains", "🥖"),
    "pastry": ("Bakery & Grains", "🥐"),
    "brown bread": ("Bakery & Grains", "🍞"),
    "white bread": ("Bakery & Grains", "🍞"),
    "semi-finished bread": ("Bakery & Grains", "🥖"),
    "soda": ("Beverages", "🥤"),
    "bottled water": ("Beverages", "💧"),
    "bottled beer": ("Beverages", "🍺"),
    "canned beer": ("Beverages", "🍻"),
    "fruit/vegetable juice": ("Beverages", "🧃"),
    "coffee": ("Beverages", "☕"),
    "sausage": ("Meat & Seafood", "🌭"),
    "beef": ("Meat & Seafood", "🥩"),
    "pork": ("Meat & Seafood", "🍖"),
    "chicken": ("Meat & Seafood", "🍗"),
    "frankfurter": ("Meat & Seafood", "🌭"),
    "ham": ("Meat & Seafood", "🍖"),
    "frozen vegetables": ("Fresh Produce", "🧊"),
    "ice cream": ("Dairy & Eggs", "🍨"),
    "chocolate": ("Snacks & Sweets", "🍫"),
    "candy": ("Snacks & Sweets", "🍬"),
    "salty snack": ("Snacks & Sweets", "🥨"),
    "waffles": ("Bakery & Grains", "🧇"),
    "packaged fruit/vegetables": ("Fresh Produce", "🥗"),
    "pasta": ("Pantry & Cooking", "🍝"),
    "rice": ("Pantry & Cooking", "🍚"),
    "oil": ("Pantry & Cooking", "🫒"),
    "margarine": ("Dairy & Eggs", "🧈"),
    "sugar": ("Pantry & Cooking", "🍬"),
    "domestic eggs": ("Dairy & Eggs", "🥚"),
    "hygiene articles": ("Personal & Home", "🧼"),
    "shopping bags": ("Personal & Home", "🛍️"),
    "napkins": ("Personal & Home", "🧻"),
}


def get_product_meta(product_name: str) -> Tuple[str, str]:
    """
    Returns (category_name, emoji_icon) for any grocery product.
    Defaults to ('General Grocery', '🛒') if not explicitly classified.
    """
    cleaned = str(product_name).strip().lower()
    if cleaned in PRODUCT_MAPPINGS:
        return PRODUCT_MAPPINGS[cleaned]

    # Keyword heuristics
    if any(k in cleaned for k in ["fruit", "berry", "melon", "vegetable", "salad", "potato", "onion"]):
        return ("Fresh Produce", "🥗")
    elif any(k in cleaned for k in ["milk", "cheese", "cream", "butter", "curd"]):
        return ("Dairy & Eggs", "🧀")
    elif any(k in cleaned for k in ["bread", "roll", "bun", "cake", "biscuit", "flour"]):
        return ("Bakery & Grains", "🍞")
    elif any(k in cleaned for k in ["meat", "beef", "chicken", "pork", "fish", "sausage"]):
        return ("Meat & Seafood", "🥩")
    elif any(k in cleaned for k in ["beer", "wine", "water", "juice", "soda", "drink", "coffee", "tea"]):
        return ("Beverages", "🥤")
    elif any(k in cleaned for k in ["clean", "detergent", "soap", "bag"]):
        return ("Personal & Home", "🧼")

    return ("General Grocery", "🛒")
