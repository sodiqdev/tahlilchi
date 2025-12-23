# app/controller.py - TO'G'RILANGAN
import json
import os
from typing import Optional
from core import create_assessment_template
from app.profile_manager import ProfileManager

class AppController:
    def __init__(self):
        self.profile_manager = ProfileManager()
        
    def get_classes(self, profile_id: str = "default"):
        """Get classes from profile"""
        try:
            profile = self.profile_manager.get_profile(profile_id)
            if profile and "data" in profile:
                classes = profile["data"].get("classes", {})
                return sorted(classes.keys())
        except Exception as e:
            print(f"❌ Error getting classes: {e}")
        return []
    
    def get_students(self, sinf: str, profile_id: str = "default"):
        """Get students from profile"""
        try:
            profile = self.profile_manager.get_profile(profile_id)
            if profile and "data" in profile:
                return profile["data"].get("classes", {}).get(sinf, [])
        except Exception as e:
            print(f"❌ Error getting students: {e}")
        return []
    
    def get_subjects(self, profile_id: str = "default"):
        """Get subjects from profile"""
        try:
            profile = self.profile_manager.get_profile(profile_id)
            if profile and "data" in profile:
                return profile["data"].get("subjects", [])
        except Exception as e:
            print(f"❌ Error getting subjects: {e}")
        return []
    
    def get_settings(self, profile_id: str = "default"):
        """Get settings from profile"""
        try:
            profile = self.profile_manager.get_profile(profile_id)
            if profile and "settings" in profile:
                return profile["settings"]
        except Exception as e:
            print(f"❌ Error getting settings: {e}")
        return {}
    
    def generate_excel(
        self,
        sinf: str,
        fan: str,
        chorak: str,
        imtihon_nomi: str,
        num_tasks: int,
        max_scores: list,
        output_dir: str,
        profile_id: str = "default",
        tuman: str = None,
        maktab: str = None,
        oibdo: str = None,
        metod_rahbari: str = None,
        fan_oqituvchisi: str = None,
    ):
        """Generate Excel with profile support"""
        students = self.get_students(sinf, profile_id)
        if not students:
            raise ValueError(f"Tanlangan sinfda o'quvchilar yo'q: {sinf}")
        
        # Get settings from profile or use provided values
        profile_settings = self.get_settings(profile_id)
        
        config = {
            "tuman": tuman or profile_settings.get("tuman", ""),
            "maktab": maktab or profile_settings.get("maktab", ""),
            "oibdo": oibdo or profile_settings.get("oibdo", ""),
            "metod_rahbari": metod_rahbari or profile_settings.get("metod_rahbari", ""),
            "fan_oqituvchisi": fan_oqituvchisi or profile_settings.get("fan_oqituvchisi", ""),
            "sinf": sinf,
            "fan": fan,
            "chorak": chorak,
            "imtihon_nomi": imtihon_nomi
        }
        
        return create_assessment_template(
            students_list=students,
            num_tasks=num_tasks,
            max_scores=max_scores,
            config=config,
            output_dir=output_dir
        )