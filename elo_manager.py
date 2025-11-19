import json
import os
import config

ELO_FILE = os.path.join(config.MODEL_DIR, "elo_ratings.json")

def load_elo_ratings():
    """Loads ELO ratings from JSON file."""
    if not os.path.exists(ELO_FILE):
        return {}
    try:
        with open(ELO_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading ELO ratings: {e}")
        return {}

def save_elo_ratings(ratings):
    """Saves ELO ratings to JSON file."""
    try:
        with open(ELO_FILE, "w") as f:
            json.dump(ratings, f, indent=4)
    except Exception as e:
        print(f"Error saving ELO ratings: {e}")

def get_elo(filename):
    """Gets ELO for a specific file, defaulting to 1200."""
    ratings = load_elo_ratings()
    return ratings.get(filename, config.ELO_INITIAL_RATING)

def update_elo(filename, new_elo):
    """Updates ELO for a specific file and saves."""
    ratings = load_elo_ratings()
    ratings[filename] = new_elo
    save_elo_ratings(ratings)

def update_bulk_elo(updates):
    """Updates multiple ELO ratings at once. updates = {filename: new_elo}"""
    ratings = load_elo_ratings()
    for filename, elo in updates.items():
        ratings[filename] = elo
    save_elo_ratings(ratings)

def remove_elo(filename):
    """Removes ELO entry for a file."""
    ratings = load_elo_ratings()
    if filename in ratings:
        del ratings[filename]
        save_elo_ratings(ratings)
