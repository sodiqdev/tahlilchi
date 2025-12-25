# app/profile_manager.py - TO'LIQ YANGILANGAN
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Set

class ProfileManager:
    def __init__(self, profiles_dir: str = "data/profiles"):
        self.profiles_dir = profiles_dir
        os.makedirs(profiles_dir, exist_ok=True)
        self._ensure_default_profile()
        self._ensure_master_data()
    
    def _ensure_master_data(self):
        """Create master data files if not exists"""
        # Master subjects (all available subjects)
        master_subjects_path = os.path.join(self.profiles_dir, "_master_subjects.json")
        if not os.path.exists(master_subjects_path):
            # Load from existing subjects.json
            if os.path.exists("subjects.json"):
                with open("subjects.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    master_subjects = data.get("subjects", [])
            else:
                master_subjects = []
            
            with open(master_subjects_path, 'w', encoding='utf-8') as f:
                json.dump({"subjects": master_subjects}, f, ensure_ascii=False, indent=2)
        
        # Master classes (all available classes)
        master_classes_path = os.path.join(self.profiles_dir, "_master_classes.json")
        if not os.path.exists(master_classes_path):
            # Load from existing students_data.json
            if os.path.exists("students_data.json"):
                with open("students_data.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    master_classes = data.get("classes", {})
            else:
                master_classes = {}
            
            with open(master_classes_path, 'w', encoding='utf-8') as f:
                json.dump({"classes": master_classes}, f, ensure_ascii=False, indent=2)
    
    def _ensure_default_profile(self):
        """Create default profile if not exists"""
        default_path = os.path.join(self.profiles_dir, "default.json")
        if os.path.exists(default_path):
            return
        
        print("🔄 Default profile yaratilmoqda...")
        
        # Load master data
        master_subjects = self.get_master_subjects()
        master_classes = self.get_master_classes()
        
        # Load settings
        settings = {}
        if os.path.exists("settings.json"):
            with open("settings.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        default_profile = {
            "profile_id": "default",
            "profile_name": "Tahlilchi",
            "owner": "system",
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "is_active": True,
            "settings": {
                "tuman": settings.get("tuman", ""),
                "maktab": settings.get("maktab", ""),
                "oibdo": settings.get("oibdo", ""),
                "metod_rahbari": settings.get("metod_rahbari", ""),
                "fan_oqituvchisi": settings.get("fan_oqituvchisi", ""),
                "output_dir": settings.get("output_dir", "outputs")
            },
            "data": {
                "classes": master_classes.copy(),  
                "subjects": master_subjects.copy()
            },
            "meta": {
                "is_master": True,
                "can_edit": True,
                "can_delete": False
            }
        }
        
        self.save_profile("default", default_profile)
        print(f"✅ Default profile yaratildi")
    
    def get_master_subjects(self) -> List[str]:
        """Get all subjects from master data"""
        master_path = os.path.join(self.profiles_dir, "_master_subjects.json")
        print(f"📂 Loading master subjects from: {master_path}")
        
        if os.path.exists(master_path):
            try:
                with open(master_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    subjects = data.get("subjects", [])
                    print(f"✅ Loaded {len(subjects)} subjects from master file")
                    return subjects
            except Exception as e:
                print(f"❌ Error loading master subjects: {e}")
                return []
        else:
            print(f"❌ Master subjects file not found: {master_path}")
            return []

    def get_master_classes(self) -> Dict:
        """Get all classes from master data"""
        master_path = os.path.join(self.profiles_dir, "_master_classes.json")
        print(f"📂 Loading master classes from: {master_path}")
        
        if os.path.exists(master_path):
            try:
                with open(master_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    classes = data.get("classes", {})
                    print(f"✅ Loaded {len(classes)} classes from master file")
                    return classes
            except Exception as e:
                print(f"❌ Error loading master classes: {e}")
                return {}
        else:
            print(f"❌ Master classes file not found: {master_path}")
            return {}
    
    def add_to_master_subjects(self, subjects: List[str]):
        """Add subjects to master list"""
        master_path = os.path.join(self.profiles_dir, "_master_subjects.json")
        current = self.get_master_subjects()
        
        new_subjects = []
        for subject in subjects:
            if subject and subject not in current:
                new_subjects.append(subject)
        
        if new_subjects:
            current.extend(new_subjects)
            with open(master_path, 'w', encoding='utf-8') as f:
                json.dump({"subjects": current}, f, ensure_ascii=False, indent=2)
        
        return new_subjects
    
    def add_to_master_classes(self, class_name: str, students: List[str]):
        """Add class to master data"""
        master_path = os.path.join(self.profiles_dir, "_master_classes.json")
        current = self.get_master_classes()
        
        if class_name not in current:
            current[class_name] = students
            with open(master_path, 'w', encoding='utf-8') as f:
                json.dump({"classes": current}, f, ensure_ascii=False, indent=2)
            return True
        return False
    
    def get_profile(self, profile_id: str = "default") -> Optional[Dict]:
        """Get profile by ID"""
        if not profile_id or profile_id == "undefined":
            profile_id = "default"
        
        path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fallback to default
        if profile_id != "default":
            return self.get_profile("default")
        return None
    
    def save_profile(self, profile_id: str, data: Dict):
        """Save profile to file"""
        data["last_modified"] = datetime.now().isoformat()
        path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def update_profile_settings(self, profile_id: str, settings: Dict):
        """Update only settings of a profile"""
        profile = self.get_profile(profile_id)
        if not profile:
            return False
        
        profile["settings"] = settings
        self.save_profile(profile_id, profile)
        return True
    
    def create_profile_with_selection(self, name: str, owner: str = "user",
                                    selected_subjects: List[str] = None,
                                    selected_classes: List[str] = None,
                                    copy_settings_from: str = "default") -> Dict:
        """Create profile with selected subjects and classes"""
        import hashlib
        import time
        
        # Generate unique ID
        unique_id = hashlib.md5(f"{name}_{owner}_{time.time()}".encode()).hexdigest()[:8]
        profile_id = f"{owner}_{unique_id}"
        
        # Get base profile for settings
        base_profile = self.get_profile(copy_settings_from) or self.get_profile("default")
        
        # Get master data
        master_subjects = self.get_master_subjects()
        master_classes = self.get_master_classes()
        
        # Filter subjects
        if selected_subjects:
            # Only include subjects that exist in master
            subjects = [s for s in selected_subjects if s in master_subjects]
            if not subjects:  # If none selected, use all
                subjects = master_subjects.copy()
        else:
            subjects = master_subjects.copy()
        
        # Filter classes
        if selected_classes:
            classes = {k: v for k, v in master_classes.items() if k in selected_classes}
        else:
            classes = master_classes.copy()
        
        # Create profile
        profile = {
            "profile_id": profile_id,
            "profile_name": name,
            "owner": owner,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "is_active": True,
            "settings": base_profile.get("settings", {}).copy(),
            "data": {
                "classes": classes,
                "subjects": subjects
            },
            "meta": {
                "is_master": False,
                "can_edit": True,
                "can_delete": True,
                "subjects_selected": selected_subjects is not None,
                "classes_selected": selected_classes is not None
            }
        }
        
        self.save_profile(profile_id, profile)
        return profile
    
    def add_subject_to_profile(self, profile_id: str, subject: str):
        """Add subject to specific profile"""
        profile = self.get_profile(profile_id)
        if not profile:
            return False
        
        # Add to profile
        if subject not in profile["data"]["subjects"]:
            profile["data"]["subjects"].append(subject)
            profile["data"]["subjects"].sort()
            self.save_profile(profile_id, profile)
        
        # Also add to master if not exists
        master_subjects = self.get_master_subjects()
        if subject not in master_subjects:
            self.add_to_master_subjects([subject])
        
        return True
    
    def remove_subject_from_profile(self, profile_id: str, subject: str):
        """Remove subject from profile (but keep in master)"""
        profile = self.get_profile(profile_id)
        if not profile:
            return False
        
        if subject in profile["data"]["subjects"]:
            profile["data"]["subjects"].remove(subject)
            self.save_profile(profile_id, profile)
        
        return True
    
    def add_class_to_profile(self, profile_id: str, class_name: str, students: List[str]):
        """Add class to profile"""
        profile = self.get_profile(profile_id)
        if not profile:
            return False
        
        # Add to profile
        profile["data"]["classes"][class_name] = students
        self.save_profile(profile_id, profile)
        
        # Also add to master
        self.add_to_master_classes(class_name, students)
        
        return True
    
    def list_profiles(self) -> List[Dict]:
        """List all available profiles (excluding master data files)"""
        profiles = []
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith('.json') and not filename.startswith('_'):
                profile_id = filename[:-5]
                profile = self.get_profile(profile_id)
                if profile:
                    # Add statistics
                    profile_stats = {
                        **profile,
                        "stats": {
                            "classes": len(profile.get("data", {}).get("classes", {})),
                            "students": sum(len(c) for c in profile.get("data", {}).get("classes", {}).values()),
                            "subjects": len(profile.get("data", {}).get("subjects", []))
                        }
                    }
                    profiles.append(profile_stats)
        return profiles