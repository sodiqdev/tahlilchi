# utils/data_manager.py - YANGILANGAN
import json
import os
from datetime import datetime
from app.profile_manager import ProfileManager

profile_manager = ProfileManager()

def load_students_data(profile_id: str = "default"):
    """Backward compatibility: Load from profile"""
    profile = profile_manager.get_profile(profile_id)
    if profile and "data" in profile:
        return {
            "classes": profile["data"].get("classes", {}),
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    return {"classes": {}, "last_updated": None}

def save_students_data(data: dict, profile_id: str = "default"):
    """Backward compatibility: Save to profile"""
    profile_manager.update_profile_data(profile_id, "classes", data.get("classes", {}))

def get_classes(profile_id: str = "default"):
    """Backward compatibility"""
    profile = profile_manager.get_profile(profile_id)
    if profile and "data" in profile:
        return sorted(profile["data"].get("classes", {}).keys())
    return []

def get_students(sinf: str, profile_id: str = "default"):
    """Backward compatibility"""
    profile = profile_manager.get_profile(profile_id)
    if profile and "data" in profile:
        return profile["data"].get("classes", {}).get(sinf, [])
    return []