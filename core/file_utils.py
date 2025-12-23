import os

def get_safe_filename(filename: str) -> str:
    """Fayl nomini xavfsiz qilish"""
    filename = filename.replace(' ', '_')
    for char in '\\/*?:"<>|':
        filename = filename.replace(char, '')
    return filename


def ensure_output_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)
