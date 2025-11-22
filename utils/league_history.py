"""
League History Manager

Manages league history data including tournament results, player statistics,
and historical records.
"""

import json
import os
import datetime
from core import config


LEAGUE_HISTORY_FILE = os.path.join(config.DATA_DIR, "league_history.json")


def load_league_history():
    """Loads league history from persistent storage.
    
    Returns:
        dict: Dictionary with 'all_time_leader' and 'season_champions' keys.
    """
    if not os.path.exists(LEAGUE_HISTORY_FILE):
        return {
            "all_time_leader": None,
            "season_champions": []
        }
    
    try:
        with open(LEAGUE_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "all_time_leader": None,
            "season_champions": []
        }


def save_league_history(history):
    """Saves league history to persistent storage.
    
    Args:
        history: Dictionary containing league history data.
    """
    with open(LEAGUE_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def update_all_time_leader(model_name, elo_rating):
    """Updates the all-time ELO leader if necessary.
    
    Args:
        model_name: Name of the model.
        elo_rating: Current ELO rating of the model.
    
    Returns:
        bool: True if a new all-time leader was set.
    """
    history = load_league_history()
    
    current_leader = history.get("all_time_leader")
    
    if current_leader is None or elo_rating > current_leader.get("elo", 0):
        history["all_time_leader"] = {
            "model": model_name,
            "elo": elo_rating,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_league_history(history)
        return True
    
    return False


def add_season_champion(model_name, elo_rating, tournament_date=None):
    """Adds a season champion to the history.
    
    Args:
        model_name: Name of the champion model.
        elo_rating: ELO rating at championship.
        tournament_date: Optional date string. Uses current time if None.
    """
    history = load_league_history()
    
    if tournament_date is None:
        tournament_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    champion = {
        "model": model_name,
        "elo": elo_rating,
        "date": tournament_date
    }
    
    history["season_champions"].append(champion)
    
    # Keep only last 20 seasons to prevent file bloat
    if len(history["season_champions"]) > 20:
        history["season_champions"] = history["season_champions"][-20:]
    
    save_league_history(history)
    
    # Also check if this is a new all-time leader
    update_all_time_leader(model_name, elo_rating)


def get_all_time_leader():
    """Gets the all-time ELO leader.
    
    Returns:
        dict or None: Leader info with 'model', 'elo', 'date' keys, or None.
    """
    history = load_league_history()
    return history.get("all_time_leader")


def get_season_champions():
    """Gets the list of past season champions.
    
    Returns:
        list: List of champion dictionaries, most recent last.
    """
    history = load_league_history()
    return history.get("season_champions", [])
