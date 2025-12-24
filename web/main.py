# web/main.py
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
import json

from app.profile_manager import ProfileManager
from core.generator import create_assessment_template
from app.controller import AppController
from app.settings_manager import SettingsManager

import pandas as pd
from openpyxl import load_workbook
from io import BytesIO
from utils.data_manager import load_students_data, save_students_data, get_classes, get_students

app = FastAPI(title="Baholash Tahlili Generator")

# Yangi: templates direktoriyasini o'zgartirish
templates = Jinja2Templates(directory="web/templates")

controller = AppController()
settings_mgr = SettingsManager()
profile_manager = ProfileManager()

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Yangi: dark mode uchun helper funksiya
def get_dark_mode(request: Request):
    dark_mode = request.cookies.get("dark_mode", "false")
    return dark_mode == "true"

async def get_base_context(request: Request):
    """Get base context for all templates"""
    try:
        # Get active profile ID
        active_profile_id = request.cookies.get("active_profile", "default")
        print(f"🔍 Active profile ID: {active_profile_id}")
        
        # Get active profile
        profile = profile_manager.get_profile(active_profile_id)
        if not profile:
            print(f"⚠️ Profile {active_profile_id} topilmadi, default ga o'tildi")
            active_profile_id = "default"
            profile = profile_manager.get_profile("default")
        
        # Get data from profile
        settings = profile.get("settings", {}) if profile else {}
        classes = controller.get_classes(active_profile_id)
        subjects = controller.get_subjects(active_profile_id)
        
        print(f"📊 Profile data: {len(classes)} classes, {len(subjects)} subjects")
        
        # Dark mode
        dark_mode = get_dark_mode(request)
        
        # Get all profiles for selector
        all_profiles = profile_manager.list_profiles()
        print(f"📋 Total profiles: {len(all_profiles)}")
        
        return {
            "request": request,
            "classes": classes,
            "subjects": subjects,
            "settings": settings,
            "dark_mode": dark_mode,
            "profiles": all_profiles,
            "active_profile_id": active_profile_id,
            "active_profile_name": profile.get("profile_name", "Default") if profile else "Default",
            "is_admin": True
        }
        
    except Exception as e:
        print(f"❌ Error in get_base_context: {e}")
        # Return minimal context on error
        return {
            "request": request,
            "classes": [],
            "subjects": [],
            "settings": {},
            "dark_mode": False,
            "profiles": [],
            "active_profile_id": "default",
            "active_profile_name": "Default",
            "is_admin": True
        }

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("web/static/favicon.ico")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    context = await get_base_context(request)
    return templates.TemplateResponse("index.html", context)

@app.post("/generate")
async def generate(
    request: Request,
    sinf: str = Form(...),
    fan: str = Form(...),
    chorak: str = Form(...),
    imtihon_nomi: str = Form(...),
    num_tasks: int = Form(...),
    max_scores_str: str = Form(""),
    tuman: str = Form(None),
    maktab: str = Form(None),
    oibdo: str = Form(None),
    metod_rahbari: str = Form(None),
    fan_oqituvchisi: str = Form(None),
):
    active_profile_id = request.cookies.get("active_profile", "default")
    settings = settings_mgr.load()
    
    config = {
        "tuman": tuman or settings["tuman"],
        "maktab": maktab or settings["maktab"],
        "oibdo": oibdo or settings["oibdo"],
        "metod_rahbari": metod_rahbari or settings["metod_rahbari"],
        "fan_oqituvchisi": fan_oqituvchisi or settings["fan_oqituvchisi"],
        "sinf": sinf,
        "fan": fan,
        "chorak": chorak,
        "imtihon_nomi": imtihon_nomi,
    }
    
    # max_scores ni parse qilish
    if max_scores_str.strip():
        try:
            max_scores = [float(x) for x in max_scores_str.split(",") if x.strip()]
            if len(max_scores) != num_tasks:
                raise ValueError(f"{num_tasks} ta topshiriq uchun {num_tasks} ta ball kiriting")
        except:
            context = await get_base_context(request)
            context["error"] = "Maksimal ballar noto'g'ri formatda (masalan: 10,15,20,5)"
            return templates.TemplateResponse("index.html", context)
    else:
        max_scores = [10] * num_tasks

    try:
        result = controller.generate_excel(
        sinf=sinf,
        fan=fan,
        chorak=chorak,
        imtihon_nomi=imtihon_nomi,
        num_tasks=num_tasks,
        max_scores=max_scores,
        output_dir=OUTPUT_DIR,
        profile_id=active_profile_id,  # ADD THIS
        tuman=tuman,
        maktab=maktab,
        oibdo=oibdo,
        metod_rahbari=metod_rahbari,
        fan_oqituvchisi=fan_oqituvchisi
    )

        file_path = result['file_path']
        filename = os.path.basename(file_path)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        context = await get_base_context(request)
        context["error"] = str(e)
        return templates.TemplateResponse("index.html", context)

@app.post("/save-settings")
async def save_settings(
    request: Request,
    tuman: str = Form(...),
    maktab: str = Form(...),
    oibdo: str = Form(None),
    metod_rahbari: str = Form(None),
    fan_oqituvchisi: str = Form(None),
):
    """Save settings to ACTIVE PROFILE"""
    active_profile_id = request.cookies.get("active_profile", "default")
    
    # Validation
    if not tuman or not maktab:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Tuman va Maktab maydonlari to'ldirilishi shart"}
        )
    
    try:
        profile = profile_manager.get_profile(active_profile_id)
        if not profile:
            return JSONResponse(
                {"success": False, "message": "Profil topilmadi"}
            )
        
        # Update profile settings
        new_settings = {
            "tuman": tuman.strip(),
            "maktab": maktab.strip(),
            "oibdo": oibdo.strip() if oibdo else "",
            "metod_rahbari": metod_rahbari.strip() if metod_rahbari else "",
            "fan_oqituvchisi": fan_oqituvchisi.strip() if fan_oqituvchisi else "",
            "output_dir": profile["settings"].get("output_dir", "outputs")
        }
        
        profile_manager.update_profile_settings(active_profile_id, new_settings)
        
        # Also update global settings.json for backward compatibility
        settings_mgr.save(new_settings)
        
        return JSONResponse(
            content={"success": True, "message": "Sozlamalar profilga saqlandi!"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Sozlamalarni saqlashda xato: {str(e)}"}
        )
    
@app.post("/profile/create-with-selection")
async def create_profile_with_selection(request: Request):
    """Create profile with selected subjects and classes"""
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        owner = data.get("owner", "user").strip()
        selected_subjects = data.get("subjects", [])
        selected_classes = data.get("classes", [])
        
        if not name:
            return JSONResponse({"success": False, "message": "Profil nomi kerak"})
        
        if not selected_subjects:
            return JSONResponse({"success": False, "message": "Kamida 1 ta fan tanlashingiz kerak"})
        
        profile = profile_manager.create_profile_with_selection(
            name=name,
            owner=owner,
            selected_subjects=selected_subjects,
            selected_classes=selected_classes
        )
        
        return JSONResponse({
            "success": True,
            "message": "Profil yaratildi",
            "profile": profile
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})


@app.post("/profile/save-settings")
async def save_profile_settings(
    request: Request,
    tuman: str = Form(None),
    maktab: str = Form(None),
    oibdo: str = Form(None),
    metod_rahbari: str = Form(None),
    fan_oqituvchisi: str = Form(None),
    output_dir: str = Form(None)
):
    """Save settings for active profile"""
    try:
        active_profile_id = request.cookies.get("active_profile", "default")
        profile = profile_manager.get_profile(active_profile_id)
        
        if not profile:
            return JSONResponse({"success": False, "message": "Profil topilmadi"})
        
        # Yangilash
        profile["settings"] = {
            "tuman": tuman or profile["settings"].get("tuman", ""),
            "maktab": maktab or profile["settings"].get("maktab", ""),
            "oibdo": oibdo or profile["settings"].get("oibdo", ""),
            "metod_rahbari": metod_rahbari or profile["settings"].get("metod_rahbari", ""),
            "fan_oqituvchisi": fan_oqituvchisi or profile["settings"].get("fan_oqituvchisi", ""),
            "output_dir": output_dir or profile["settings"].get("output_dir", "outputs")
        }
        
        profile_manager.save_profile(active_profile_id, profile)
        return JSONResponse({"success": True, "message": "Sozlamalar saqlandi"})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Xatolik: {str(e)}"})
    
@app.post("/profile/switch")
async def switch_profile(request: Request):
    data = await request.json()
    profile_id = data.get("profile_id", "default")
    
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        return JSONResponse({"success": False, "message": "Profil topilmadi"})
    
    response = JSONResponse({"success": True, "message": "Profil o'zgartirildi"})
    response.set_cookie(key="active_profile", value=profile_id, max_age=30*24*60*60)
    return response

# @app.post("/profile/create")
# async def create_profile(request: Request):
#     data = await request.json()
#     name = data.get("name", "").strip()
#     owner = data.get("owner", "user").strip()
#     base_profile = data.get("base_profile", "default")
    
#     if not name:
#         return JSONResponse({"success": False, "message": "Profil nomi kerak"})
    
#     try:
#         profile_id = profile_manager.create_profile_(name, owner, base_profile)
#         return JSONResponse({
#             "success": True,
#             "message": "Profil yaratildi",
#             "profile_id": profile_id,
#             "profile_name": name
#         })
#     except Exception as e:
#         return JSONResponse({"success": False, "message": str(e)})


@app.get("/profile/master-data")
async def get_master_data():
    """Get all available subjects and classes for selection"""
    subjects = profile_manager.get_master_subjects()
    classes = list(profile_manager.get_master_classes().keys())
    
    return JSONResponse({
        "success": True,
        "subjects": subjects,
        "classes": classes
    })

# 4. Add subject to profile
@app.post("/profile/add-subject")
async def add_subject(request: Request):
    """Add subject to active profile"""
    try:
        data = await request.json()
        subject = data.get("subject", "").strip()
        active_profile_id = request.cookies.get("active_profile", "default")
        
        if not subject:
            return JSONResponse({"success": False, "message": "Fan nomi kerak"})
        
        # Add to profile
        success = profile_manager.add_subject_to_profile(active_profile_id, subject)
        
        if success:
            return JSONResponse({
                "success": True, 
                "message": f"'{subject}' fani profilga qo'shildi",
                "subject": subject
            })
        else:
            return JSONResponse({"success": False, "message": "Profil topilmadi"})
            
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})

# 5. Remove subject from profile
@app.post("/profile/remove-subject")
async def remove_subject(request: Request):
    """Remove subject from active profile"""
    try:
        data = await request.json()
        subject = data.get("subject", "").strip()
        active_profile_id = request.cookies.get("active_profile", "default")
        
        if not subject:
            return JSONResponse({"success": False, "message": "Fan nomi kerak"})
        
        success = profile_manager.remove_subject_from_profile(active_profile_id, subject)
        
        if success:
            return JSONResponse({
                "success": True, 
                "message": f"'{subject}' fani profildan olib tashlandi"
            })
        else:
            return JSONResponse({"success": False, "message": "Profil topilmadi"})
            
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})

# 6. Add new subject to master
@app.post("/profile/create-subject")
async def create_subject(request: Request):
    """Create new subject in master and add to active profile"""
    try:
        data = await request.json()
        subject = data.get("subject", "").strip()
        active_profile_id = request.cookies.get("active_profile", "default")
        
        if not subject:
            return JSONResponse({"success": False, "message": "Fan nomi kerak"})
        
        # Add to master
        profile_manager.add_to_master_subjects([subject])
        
        # Add to active profile
        profile_manager.add_subject_to_profile(active_profile_id, subject)
        
        return JSONResponse({
            "success": True, 
            "message": f"'{subject}' fani yaratildi va profilga qo'shildi",
            "subject": subject
        })
            
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})

@app.get("/profile/{profile_id}")
async def get_profile_details(profile_id: str):
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        return JSONResponse({"success": False, "message": "Profil topilmadi"})
    
    return JSONResponse({
        "success": True,
        "profile": {
            "id": profile["profile_id"],
            "name": profile["profile_name"],
            "owner": profile["owner"],
            "created_at": profile["created_at"],
            "statistics": {
                "classes": len(profile["data"]["classes"]),
                "students": sum(len(s) for s in profile["data"]["classes"].values()),
                "subjects": len(profile["data"]["subjects"])
            }
        }
    })

@app.get("/profile/{profile_id}/data")
async def get_profile_data(profile_id: str):
    """Get profile data (subjects and classes)"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        return JSONResponse({"success": False, "message": "Profil topilmadi"})
    
    return JSONResponse({
        "success": True,
        "data": profile.get("data", {}),
        "settings": profile.get("settings", {})
    })

@app.get("/profile/{profile_id}/classes")
async def get_profile_classes(profile_id: str):
    """Get classes from specific profile"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        return JSONResponse({"success": False, "message": "Profil topilmadi"})
    
    return JSONResponse({
        "success": True,
        "classes": profile.get("data", {}).get("classes", {})
    })

@app.post("/profile/{profile_id}/delete-class")
async def delete_class_from_profile(profile_id: str, class_name: str = Form(...)):
    """Delete class from profile"""
    try:
        profile = profile_manager.get_profile(profile_id)
        if not profile:
            return JSONResponse({"success": False, "message": "Profil topilmadi"})
        
        if class_name in profile["data"]["classes"]:
            del profile["data"]["classes"][class_name]
            profile_manager.save_profile(profile_id, profile)
            
            return JSONResponse({
                "success": True,
                "message": f"'{class_name}' sinfi profildan o'chirildi"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": f"'{class_name}' sinfi topilmadi"
            })
            
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})
    
# web/main.py ga yangi endpoint:
@app.post("/extract-class-name")
async def extract_class_name(file: UploadFile = File(...)):
    """Extract class name from journal file"""
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), header=None)
        
        # Extract class name from A2 cell
        sinf_cell = df.iloc[1, 0] if df.shape[0] > 1 else None
        sinf_name = "Noma'lum"
        
        if sinf_cell and isinstance(sinf_cell, str):
            if "Sinf:" in sinf_cell:
                sinf_name = sinf_cell.split("Sinf:")[1].split("2025")[0].strip()
            elif any(keyword in sinf_cell for keyword in ["sinf", "SINF", "class", "CLASS"]):
                sinf_name = sinf_cell
        
        return JSONResponse({
            "success": True,
            "class_name": sinf_name,
            "file_name": file.filename
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})

@app.get("/admin-upload", response_class=HTMLResponse)
async def admin_upload_page(request: Request):
    context = await get_base_context(request)
    return templates.TemplateResponse("admin_upload.html", context)

@app.get("/journal-upload", response_class=HTMLResponse)
async def journal_upload_page(request: Request):
    context = await get_base_context(request)
    return templates.TemplateResponse("journal_upload.html", context)

# web/main.py - admin_upload endpoint ni yangilang:
@app.post("/admin-upload")
async def admin_upload(request: Request, file: UploadFile = File(...)):
    context = await get_base_context(request)
    active_profile_id = request.cookies.get("active_profile", "default")
    
    filename = file.filename.lower() if file.filename else ""
    allowed_extensions = ('.xls', '.xlsx', '.html', '.htm')
    
    if not filename.endswith(allowed_extensions):
        context["error"] = "Faqat .xls, .xlsx, .html yoki .htm fayl yuklang!"
        return templates.TemplateResponse("admin_upload.html", context)

    contents = await file.read()

    try:
        if b'<html' in contents.lower()[:100] or filename.endswith(('.html', '.htm')):
            df_list = pd.read_html(BytesIO(contents), flavor='lxml', encoding='utf-8')
        else:
            engine = 'openpyxl' if filename.endswith('.xlsx') else 'xlrd'
            df_list = pd.read_excel(BytesIO(contents), header=None, engine=engine)

        if not df_list:
            context["error"] = "Jadval topilmadi!"
            return templates.TemplateResponse("admin_upload.html", context)

        df = df_list[0]
        df_data = df.iloc[2:].copy()
        df_data.reset_index(drop=True, inplace=True)

        if df_data.shape[1] < 6:
            context["error"] = "Jadvalda yetarli ustun yo'q (kamida 6 ta bo'lishi kerak)"
            return templates.TemplateResponse("admin_upload.html", context)

        names_series = df_data.iloc[:, 1].dropna()
        classes_series = df_data.iloc[:, 5].dropna()

        min_len = min(len(names_series), len(classes_series))
        names = names_series.iloc[:min_len].astype(str).str.strip().tolist()
        classes = classes_series.iloc[:min_len].astype(str).str.strip().tolist()

        new_classes = {}
        total_students = 0
        
        for name, sinf in zip(names, classes):
            if name.lower() == "nan" or sinf.lower() == "nan":
                continue
            name = name.strip()
            sinf = sinf.strip()
            if name and sinf:
                if sinf not in new_classes:
                    new_classes[sinf] = []
                if name not in new_classes[sinf]:
                    new_classes[sinf].append(name)
                    total_students += 1

        # ACTIVE PROFILE GA SAQLASH
        profile = profile_manager.get_profile(active_profile_id)
        if not profile:
            context["error"] = "Profil topilmadi!"
            return templates.TemplateResponse("admin_upload.html", context)
        
        profile["data"]["classes"] = new_classes
        profile_manager.save_profile(active_profile_id, profile)

        context["success"] = f"{len(new_classes)} ta sinf va {total_students} ta o'quvchi profilga yuklandi!"
        return templates.TemplateResponse("admin_upload.html", context)

    except Exception as e:
        context["error"] = f"Fayl o'qishda xato: {str(e)}"
        return templates.TemplateResponse("admin_upload.html", context)
    
@app.post("/journal-upload")
async def journal_upload(
    request: Request,
    file: UploadFile = File(...),
    fan: str = Form(...),
    chorak: str = Form(...),
    imtihon_nomi: str = Form(...),
    num_tasks: int = Form(...),
    max_scores_str: str = Form(""),
    tuman: str = Form(None),
    maktab: str = Form(None),
    oibdo: str = Form(None),
    metod_rahbari: str = Form(None),
    fan_oqituvchisi: str = Form(None),
):
    context = await get_base_context(request)
    active_profile_id = request.cookies.get("active_profile", "default")
    
    if not file.filename.lower().endswith(('.xls', '.xlsx')):
        context["error"] = "Faqat .xls yoki .xlsx fayl!"
        return templates.TemplateResponse("journal_upload.html", context)

    contents = await file.read()

    try:
        df = pd.read_excel(BytesIO(contents), header=None)
    except Exception as e:
        context["error"] = f"Fayl o'qilmadi: {str(e)}"
        return templates.TemplateResponse("journal_upload.html", context)

    # Sinf nomi A2 dan
    sinf_cell = df.iloc[1, 0] if df.shape[0] > 1 else None
    sinf_name = "Unknown"
    if sinf_cell and isinstance(sinf_cell, str) and "Sinf:" in sinf_cell:
        sinf_name = sinf_cell.split("Sinf:")[1].split("2025")[0].strip()

    # O'quvchilar B11 dan
    students = df.iloc[10:, 1].dropna().astype(str).str.strip().tolist()
    students = [s for s in students if s and s.lower() != "nan"]

    if not students:
        context["error"] = "O'quvchilar topilmadi (B11 dan pastga tekshiring)"
        return templates.TemplateResponse("journal_upload.html", context)

    # Bazaga saqlash - ACTIVE PROFILE GA
    profile = profile_manager.get_profile(active_profile_id)
    if not profile:
        context["error"] = "Profil topilmadi!"
        return templates.TemplateResponse("journal_upload.html", context)
    
    # Yangi sinfni profile ga qo'shish
    profile["data"]["classes"][sinf_name] = students
    profile_manager.save_profile(active_profile_id, profile)

    # max_scores parse
    if max_scores_str.strip():
        try:
            max_scores = [float(x) for x in max_scores_str.split(",") if x.strip()]
            if len(max_scores) != num_tasks:
                context["error"] = f"{num_tasks} ta topshiriq uchun {num_tasks} ta ball kiriting"
                return templates.TemplateResponse("journal_upload.html", context)
        except:
            context["error"] = "Maksimal ballar noto'g'ri formatda"
            return templates.TemplateResponse("journal_upload.html", context)
    else:
        max_scores = [10] * num_tasks

    settings = profile["settings"]

    # Excel yaratish
    try:
        result = controller.generate_excel(
            sinf=sinf_name,
            fan=fan,
            chorak=chorak,
            imtihon_nomi=imtihon_nomi,
            num_tasks=num_tasks,
            max_scores=max_scores,
            output_dir=OUTPUT_DIR,
            profile_id=active_profile_id,  # <- ADD THIS
            tuman=tuman,
            maktab=maktab,
            oibdo=oibdo,
            metod_rahbari=metod_rahbari,
            fan_oqituvchisi=fan_oqituvchisi
        )
        
        file_path = result['file_path']
        filename = os.path.basename(file_path)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        context["error"] = f"Excel yaratishda xato: {str(e)}"
        return templates.TemplateResponse("journal_upload.html", context)
    
@app.get("/admin")
async def admin_panel(request: Request):
    context = await get_base_context(request)
    active_profile_id = request.cookies.get("active_profile", "default")
    
    profile = profile_manager.get_profile(active_profile_id)
    classes = profile["data"]["classes"] if profile else {}
    
    context.update({
        "page_title": f"Admin Panel - {profile['profile_name'] if profile else 'Default'}",
        "classes": classes,
        "subjects": controller.get_subjects(active_profile_id)
    })
    return templates.TemplateResponse("admin_panel.html", context)

@app.post("/admin/delete-class")
async def delete_class(request: Request, sinf_nomi: str = Form(...)):
    try:
        active_profile_id = request.cookies.get("active_profile", "default")
        profile = profile_manager.get_profile(active_profile_id)
        
        if not profile:
            return JSONResponse({"success": False, "message": "Profil topilmadi"})
        
        if sinf_nomi in profile["data"]["classes"]:
            # Remove class from profile
            del profile["data"]["classes"][sinf_nomi]
            profile_manager.save_profile(active_profile_id, profile)
            
            return JSONResponse({
                "success": True,
                "message": f"'{sinf_nomi}' sinfi profilidan o'chirildi!"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": f"'{sinf_nomi}' sinfi topilmadi!"
            })
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Xatolik: {str(e)}"})

@app.post("/admin/delete-subject")
async def delete_subject(request: Request, fan_nomi: str = Form(...)):
    """Fanni o'chirish"""
    try:
        # Fanlar ro'yxatini o'qish (settings.json dan yoki boshqa fayldan)
        # Bu sizning fanlarni qayerda saqlaganingizga bog'liq
        
        # Misol uchun: subjects.json faylidan o'qish
        import json
        subjects_file = "data/subjects.json"
        
        if os.path.exists(subjects_file):
            with open(subjects_file, 'r', encoding='utf-8') as f:
                subjects = json.load(f)
        else:
            subjects = []
        
        if fan_nomi in subjects:
            subjects.remove(fan_nomi)
            with open(subjects_file, 'w', encoding='utf-8') as f:
                json.dump(subjects, f, ensure_ascii=False, indent=2)
            
            return JSONResponse({
                "success": True,
                "message": f"'{fan_nomi}' fani muvaffaqiyatli o'chirildi!"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": f"'{fan_nomi}' fani topilmadi!"
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Xatolik: {str(e)}"
    

    })


# Yangi: Dark mode sozlamasini saqlash uchun endpoint
@app.post("/toggle-dark-mode")
async def toggle_dark_mode(request: Request):
    dark_mode = request.cookies.get("dark_mode", "false")
    new_mode = "false" if dark_mode == "true" else "true"
    
    response = JSONResponse({"success": True, "dark_mode": new_mode == "true"})
    response.set_cookie(key="dark_mode", value=new_mode, max_age=30*24*60*60)  # 30 kun
    return response

# Yangi: Sinf va fanlar ro'yxatini JSON formatida olish (AJAX uchun)
@app.get("/api/classes")
async def get_classes_api():
    classes = controller.get_classes()
    return JSONResponse({"classes": classes})

@app.get("/api/subjects")
async def get_subjects_api():
    subjects = controller.get_subjects()
    return JSONResponse({"subjects": subjects})

@app.get("/api/settings")
async def get_settings_api():
    settings = settings_mgr.load()
    return JSONResponse(settings)

static_dir = "web/static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    # Papka yo'q bo'lsa, yaratish yoki e'tiborsiz qoldirish
    try:
        os.makedirs(static_dir, exist_ok=True)
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        print(f"✅ Created {static_dir} directory")
    except:
        print(f"⚠️ Could not create {static_dir}, static files disabled")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)