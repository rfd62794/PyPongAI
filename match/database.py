import json
import os
from core import config
from typing import List, Dict, Optional

MATCH_INDEX_FILE = os.path.join(config.DATA_DIR, "match_index.json")

def load_index() -> Dict:
    """Load the match index from disk."""
    if not os.path.exists(MATCH_INDEX_FILE):
        return {"matches": [], "version": "1.0"}
    
    try:
        with open(MATCH_INDEX_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading match index: {e}")
        return {"matches": [], "version": "1.0"}

def save_index(index: Dict):
    """Save the match index to disk."""
    try:
        with open(MATCH_INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)
    except Exception as e:
        print(f"Error saving match index: {e}")

def index_match(match_metadata: Dict):
    """
    Add a match to the index.
    
    Args:
        match_metadata: Dictionary with match info (returned from MatchRecorder.save())
    """
    if not match_metadata:
        return
    
    index = load_index()
    
    # Check if match already exists (by match_id)
    existing = [m for m in index["matches"] if m.get("match_id") == match_metadata.get("match_id")]
    if existing:
        print(f"Match {match_metadata.get('match_id')} already in index")
        return
    
    index["matches"].append(match_metadata)
    save_index(index)
    print(f"Indexed match: {match_metadata.get('match_id')}")

def get_matches_for_model(model_name: str) -> List[Dict]:
    """
    Get all matches involving a specific model.
    
    Args:
        model_name: Name of the model (filename)
    
    Returns:
        List of match metadata dictionaries
    """
    index = load_index()
    matches = []
    
    for match in index["matches"]:
        if match.get("p1") == model_name or match.get("p2") == model_name:
            matches.append(match)
    
    # Sort by timestamp (most recent first)
    matches.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return matches

def get_recent_matches(limit: int = 10, match_type: Optional[str] = None) -> List[Dict]:
    """
    Get the N most recent matches.
    
    Args:
        limit: Maximum number of matches to return
        match_type: Optional filter by match type
    
    Returns:
        List of match metadata dictionaries
    """
    index = load_index()
    matches = index["matches"]
    
    # Filter by type if specified
    if match_type:
        matches = [m for m in matches if m.get("match_type") == match_type]
    
    # Sort by timestamp (most recent first)
    matches.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return matches[:limit]

def search_matches(filters: Dict) -> List[Dict]:
    """
    Search matches with flexible filters.
    
    Args:
        filters: Dictionary of filter criteria
            - "match_type": str
            - "min_timestamp": float
            - "max_timestamp": float
            - "winner": str (model name)
            - "participant": str (either p1 or p2)
    
    Returns:
        List of matching matches
    """
    index = load_index()
    matches = index["matches"]
    
    # Apply filters
    if "match_type" in filters:
        matches = [m for m in matches if m.get("match_type") == filters["match_type"]]
    
    if "min_timestamp" in filters:
        matches = [m for m in matches if m.get("timestamp", 0) >= filters["min_timestamp"]]
    
    if "max_timestamp" in filters:
        matches = [m for m in matches if m.get("timestamp", 0) <= filters["max_timestamp"]]
    
    if "winner" in filters:
        winner_name = filters["winner"]
        matches = [m for m in matches if 
                   (m.get("winner") == "p1" and m.get("p1") == winner_name) or
                   (m.get("winner") == "p2" and m.get("p2") == winner_name)]
    
    if "participant" in filters:
        participant = filters["participant"]
        matches = [m for m in matches if m.get("p1") == participant or m.get("p2") == participant]
    
    # Sort by timestamp (most recent first)
    matches.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return matches

def get_head_to_head(model_a: str, model_b: str) -> Dict:
    """
    Get head-to-head statistics between two models.
    
    Args:
        model_a: Name of first model
        model_b: Name of second model
    
    Returns:
        Dictionary with h2h stats
    """
    index = load_index()
    h2h_matches = []
    
    for match in index["matches"]:
        p1, p2 = match.get("p1"), match.get("p2")
        if (p1 == model_a and p2 == model_b) or (p1 == model_b and p2 == model_a):
            h2h_matches.append(match)
    
    # Calculate stats
    a_wins = 0
    b_wins = 0
    
    for match in h2h_matches:
        winner = match.get("winner")
        if match.get("p1") == model_a:
            if winner == "p1":
                a_wins += 1
            else:
                b_wins += 1
        else:  # model_a is p2
            if winner == "p2":
                a_wins += 1
            else:
                b_wins += 1
    
    return {
        "model_a": model_a,
        "model_b": model_b,
        "total_matches": len(h2h_matches),
        "a_wins": a_wins,
        "b_wins": b_wins,
        "matches": h2h_matches
    }

def rebuild_index():
    """
    Rebuild the match index from scratch by scanning all match files.
    """
    print("Rebuilding match index...")
    index = {"matches": [], "version": "1.0"}
    
    if not os.path.exists(config.LOGS_MATCHES_DIR):
        save_index(index)
        return
    
    for filename in os.listdir(config.LOGS_MATCHES_DIR):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(config.LOGS_MATCHES_DIR, filename)
        try:
            with open(filepath, "r") as f:
                match_data = json.load(f)
            
            # Extract metadata
            metadata = {
                "match_id": match_data.get("match_id", filename),
                "timestamp": match_data.get("timestamp", 0),
                "p1": match_data.get("p1"),
                "p2": match_data.get("p2"),
                "match_type": match_data.get("match_type", "unknown"),
                "winner": match_data.get("winner"),
                "final_score": match_data.get("final_score", [0, 0]),
                "duration_frames": match_data.get("total_frames", 0),
                "file_path": filepath
            }
            
            # Add metadata fields if present
            if "metadata" in match_data:
                metadata.update(match_data["metadata"])
            
            index["matches"].append(metadata)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    save_index(index)
    print(f"Rebuild complete. Indexed {len(index['matches'])} matches.")

def get_total_match_count() -> int:
    """Get the total number of recorded matches."""
    index = load_index()
    return len(index["matches"])
