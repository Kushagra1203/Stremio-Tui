# core/utils.py
from datetime import datetime

def format_size(size_bytes):
    if not size_bytes: return ""
    try:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f}{unit}"
            size /= 1024
    except:
        return ""
    return ""

def format_date(date_str):
    if not date_str: return "N/A"
    try:
        if 'T' in str(date_str):
            date_str = str(date_str).split('T')[0]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except:
        return date_str

def fmt_runtime(val):
    if not val or val == "N/A": return "N/A"
    try:
        # If it's just a number (minutes)
        if isinstance(val, (int, float)) or (isinstance(val, str) and val.isdigit()):
            mins = int(val)
            if mins > 60: return f"{mins // 60}h {mins % 60}m"
            return f"{mins}m"
    except: pass
    return str(val)

def fmt_rating(val):
    if val is None or val == "": return "N/A"
    try:
        f_val = float(val)
        if f_val == 0: return "N/A"
        return f"⭐ {f_val:.1f}"
    except:
        return "N/A"
