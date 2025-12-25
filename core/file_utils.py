# file_utils.py yaxshilangan versiya
import os
import re
from datetime import datetime

def get_safe_filename(filename: str) -> str:
    """Fayl nomini xavfsiz qilish
    
    Args:
        filename: Original fayl nomi
        
    Returns:
        Xavfsiz fayl nomi
    """
    # Lotin bo'lmagan harflarni almashtirish
    replacements = {
        'ʻ': "'", 'ʼ': "'", '‘': "'", '’': "'",
        'ʻ': "'", '`': "'", '“': '"', '”': '"',
        '«': '"', '»': '"', '—': '-', '–': '-'
    }
    
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    
    # Faqat lotin harflari, raqamlar va allowed belgilar
    filename = re.sub(r'[^a-zA-Z0-9._\-() ]', '', filename)
    
    # Bo'shliqlarni pastgi chiziq bilan almashtirish
    filename = filename.replace(' ', '_')
    
    # Uzunlikni cheklash
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename

def ensure_output_dir(path: str) -> str:
    """Chiqish papkasini yaratish va toza nom qaytarish"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    
    # Papka bo'sh emasligini tekshirish
    if os.listdir(path):
        # Yangi kichik papka yaratish
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_path = os.path.join(path, timestamp)
        os.makedirs(new_path, exist_ok=True)
        return new_path
    
    return path