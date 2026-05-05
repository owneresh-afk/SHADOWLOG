import json
import os
import time
import random
import string

DB_FILE = os.path.join(os.path.dirname(__file__), "db.json")

def _load():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "licenses": {}, "stats": {"total_generated": 0, "total_users": 0}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def _save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(user_id: int):
    db = _load()
    return db["users"].get(str(user_id))

def save_user(user_id: int, data: dict):
    db = _load()
    db["users"][str(user_id)] = data
    _save(db)

def is_user_authorized(user_id: int) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    if not user.get("license_key"):
        return False
    expires_at = user.get("expires_at")
    if expires_at and time.time() > expires_at:
        db = _load()
        db["users"][str(user_id)]["authorized"] = False
        _save(db)
        return False
    return user.get("authorized", False)

def get_license(key: str):
    db = _load()
    return db["licenses"].get(key)

def create_license(key: str, duration_seconds: int, created_by: int):
    db = _load()
    db["licenses"][key] = {
        "key": key,
        "duration_seconds": duration_seconds,
        "created_at": time.time(),
        "created_by": created_by,
        "redeemed_by": None,
        "redeemed_at": None,
        "used": False
    }
    _save(db)

def redeem_license(user_id: int, key: str, username: str = None, first_name: str = None) -> dict:
    db = _load()
    license_data = db["licenses"].get(key)
    
    if not license_data:
        return {"success": False, "reason": "invalid"}
    
    if license_data["used"]:
        if license_data["redeemed_by"] == user_id:
            return {"success": False, "reason": "already_yours"}
        return {"success": False, "reason": "used"}
    
    expires_at = time.time() + license_data["duration_seconds"]
    
    db["licenses"][key]["used"] = True
    db["licenses"][key]["redeemed_by"] = user_id
    db["licenses"][key]["redeemed_at"] = time.time()
    
    existing = db["users"].get(str(user_id), {})
    db["users"][str(user_id)] = {
        **existing,
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "authorized": True,
        "license_key": key,
        "expires_at": expires_at,
        "joined_at": existing.get("joined_at", time.time()),
        "total_generated": existing.get("total_generated", 0)
    }
    
    if str(user_id) not in db["users"] or not existing:
        db["stats"]["total_users"] = db["stats"].get("total_users", 0) + 1
    
    _save(db)
    return {"success": True, "expires_at": expires_at, "duration_seconds": license_data["duration_seconds"]}

def increment_generated(user_id: int, count: int):
    db = _load()
    uid = str(user_id)
    if uid in db["users"]:
        db["users"][uid]["total_generated"] = db["users"][uid].get("total_generated", 0) + count
    db["stats"]["total_generated"] = db["stats"].get("total_generated", 0) + count
    _save(db)

def get_stats():
    db = _load()
    total_users = len(db["users"])
    authorized_users = sum(1 for u in db["users"].values() if u.get("authorized") and (not u.get("expires_at") or time.time() < u.get("expires_at", 0)))
    total_licenses = len(db["licenses"])
    used_licenses = sum(1 for l in db["licenses"].values() if l.get("used"))
    total_generated = db["stats"].get("total_generated", 0)
    return {
        "total_users": total_users,
        "authorized_users": authorized_users,
        "total_licenses": total_licenses,
        "used_licenses": used_licenses,
        "total_generated": total_generated
    }

def get_all_users():
    db = _load()
    return db["users"]

def get_all_licenses():
    db = _load()
    return db["licenses"]

def generate_license_key() -> str:
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4)]
    return '-'.join(parts)

def parse_duration(duration_str: str) -> int:
    """Parse duration like 1D, 2H, 30M into seconds"""
    duration_str = duration_str.strip().upper()
    unit = duration_str[-1]
    try:
        value = int(duration_str[:-1])
    except ValueError:
        return None
    
    if unit == 'D':
        return value * 86400
    elif unit == 'H':
        return value * 3600
    elif unit == 'M':
        return value * 60
    return None

def format_duration(seconds: int) -> str:
    if seconds >= 86400:
        days = seconds // 86400
        return f"{days} day{'s' if days > 1 else ''}"
    elif seconds >= 3600:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        mins = seconds // 60
        return f"{mins} minute{'s' if mins > 1 else ''}"

def format_time_left(expires_at: float) -> str:
    remaining = expires_at - time.time()
    if remaining <= 0:
        return "Expired"
    if remaining >= 86400:
        days = int(remaining // 86400)
        hours = int((remaining % 86400) // 3600)
        return f"{days}d {hours}h"
    elif remaining >= 3600:
        hours = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        return f"{hours}h {mins}m"
    else:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        return f"{mins}m {secs}s"
