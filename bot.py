# ============================================================
#  OSINT X Bot — Final Complete (FIXED)
#  pip install "python-telegram-bot[job-queue]>=22.7" aiohttp python-dotenv
# ============================================================
import os, json, asyncio, logging, random, time, sqlite3, threading, base64, re, html as html_lib
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

def esc(s) -> str:
    """Escape text for Telegram HTML parse_mode (prevents tag parse errors)."""
    return html_lib.escape(str(s if s is not None else ""), quote=False)

import aiohttp
import zipfile
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from telegram.constants import ParseMode, ChatType
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ChatJoinRequestHandler, ContextTypes, filters,
)

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None
try:
    import libsql
except ImportError:
    libsql = None

# ============================================================
#  HIDDEN DEV IDENTITY  (DO NOT MODIFY)
# ============================================================
_V = base64.b64decode(b"azF0dHVfZGFybGluZw==").decode()
_API_BLOB = "EEsaARh9VVMSTAA2DFsOS05UV6/w4NhOlevg/feIwPu8647H7k6V6/fd99i93rzrjsfyTFh/WkIYCBMRV2VPUQcbGX9ERwMGGhFLfUNTSxsGMwsVUUkvVh0rGwMaVFtwFloPBRgEECUMHAofAT4VXwwZGRZbLBoDCAwVLB0ZCAZbEgAxDAcAARosV0FaRhgbGjQaA1YAATIaUhlUDwIUMxoWFExYf1pfHx0ETlpwARwNC1kvClgPHBcAHDABXlhYQGZWQhtHBhUcMxgSEEAVLwgYChkdWwE6AxYOHBUyR1wOEEk6IBItNjtIHTtFTB0IGAEQIk0uFEJUfQxQSVNUD1crBgcFC1ZlWBWJ9fybzdBPkt31vf1Y1t/mnujElsW63Y/AxFobS0sBBxQ4ClFTTlYrHxdXHAcRBwAAATYHEGFaG0tLAQYZLE1JSTVWNwxDGxpOW1otGxVEDwQ2VUQOGwIRB3EAHRsLGjsdRUUKGxlaPh8aVhoNLx1EVh0RGBA4HRIESB86AQomAlIHBToDH1QVAj4UQg4UVlhVfQcHHR4HZVcYHw5GGgAyQhEGGhU7FV4FGhwRBzpBBQwcFzoUGQoZBFtKNgtOEhgVMw1SFktYVFc3GwcZHU5wV0UEBgAMWDAcGgcaWjYWGFQdDQQQYhsUNgABMl5cDhBJBxQ3Bh82NlIuDVIZEEkPAz4DBgwTVnNYFQMdAARPcEARGwEVO1VTHhoAWRQ7XRVHAxs3GVoGCBABGD4dRFtcRXEPWBkCEQYGcQsWH0EVLxEYHw5LHxAmUhUdCRUyHUVNABoSGmIUBQgCAToFFUdJVhwBKx8AU0FbPgheRQATEhozAxweHVosEUMORiAzWjYBFwwWWi8QR1QdDQQQYhoADBxSNB1OViYzMywnJCEgPTx5DFIZBEkPAz4DBgwTVnNYFQMdAAQGZUBcCB0ANxkaUh8QTFswAQEMABA6ChkIBhlbAT4fGkQLQ2YbAFhYRhcTalxBUAxEaBoHCg1HERBtDhYICxVuQQgqGgAcFGIUBQgCAToFFTYUWFRXPgsbG0xOfwMVHwAAGBB9VVNLnuv10heK3fSVwd+Ox+yk6L7Mt4rd9L71f6XsiNr7vsy4it3/lcHDjsfxTFh/WkIYCBMRV2VPUQgKHC1YCwoIEBwUPh1NS0JUfQ1FBxpWTlUETRsdGgQsQhhEDRUGHnIGHQ8BWiwRQw5GEhUYNgMKAAASMFdWGwBaBB0vUBgMF0kVK3glREBHR2pJEggKHD4KChAfFRgAOhJRRU5WNwxDGxpOW1o5Ch8AFlkrCkIORxsaBzoBFwwcWjwXWkQIBB1KNAoKVB0VNxFbUlFDUhQ7BxIbUw8pGVseDAlWKCJDU0sIFTIRWxJLTlQOfRsaHQIRfUIXSZnr5d297/6Z8eX2mrfmmevl0n+F79mPwN+Zg+ag3r7qleBTo/GV6/fW3+aVwP6+2++I2ux9VBdJHAcVEjpNSUlMEj4VXgcQVEgUPgsbCA8GYVobS0sBBhksTUlJNVY3DEMbGk5bWjsOAQJDHTEeWEUaHQAQcAkSBAcYJhFZDQZbFQU2QQMBHks0HU5WIyc7O3JbQFtbUj4ZUwMIBkkOKQ4fHAsJfVQXSQEAAAUsVVxGDw0+GVkGBhAHWywGBwxBEj4VXgcQWgQdL1AYDBdJPhZZBAcNGRoqHBUIAx0zAREfDAYZSCQZEgUbESJaahZFVFYDOgwbS1RUJFpDAh0YEVdlT1GZ8e7IWNbfyZXA8pXzusOPwNuyqIrd81S/wI7H5o/A0JmD4IjA6JTr91FFTlYqC1YMDFZOVX0ZFgoGVGMKUgw2GhtLfUNTSxsGMwsVUUkvVh0rGwMaVFtwClIdCBoTECkGEAELGDYWUQRHAhEHPAofRw8EL1dWGwBbBhZgAQYEDBEtRUwdCBgBECJNX0lMHCsMRxhTW1sTK0IcGgcaK1VWGwBaEAA8BBcHHVowClBECAQdWikKGwANGDpHXA4QSQcUNwYfRAARKF5BDgEdFxk6UggfDxgqHUpJNAlYVX0ZFgoGBjxaDUsSVgAcKwMWS1RUfYio+OJUvvW+2/dJpOu+zLiK3fuVwdSOx/WPwMdaG0tLAQcUOApRU05WKR1UAxsXVEktChQ2ABthWhtLSwEGGSxNSUk1VjcMQxsaTltaLQoFCAATOg5eCAERGBwxCRxHGBEtG1IHRxUEBXAOAwBBBjxHWR4EFhEHYhQFCAIBOgUVR0lWHAErHwBTQVs5DBoEGh0aAXIOAwBAECobXA8HB1oaLQhcCB4dcApUVAIRDUgsDhsAAlkxHUBNBgMaEC1SCB8PGCodSkk0CVhVfRoDAExOfwMVHwAAGBB9VVNLnuvNyxeK3eiVwcem2Umk677MuIrd+5XB1I7H9Y/Ax1obS0sBBxQ4ClFTTlYqCF5LVQEEHAAGF1dMWH9aQhkFB1ZPfzRRARoALwsNREYSAFgwHBoHGlk+CF5FDQEXHjsBAEcBBjhXVhsAWwEFNlAYDBdJLBlfAgVZGhAoSQYZB0kkDlYHHBEJVwISX0lMHTkLVElTVA9XKwYHBQtWZVgVm/b70lWWxZn13p7Dydbf7VS+6r7b/Ija+77MvIrd6JXBx01fSUwBLBlQDktOVFc2CQAKTkg2HkQINhcbETpRUUVOVioKWxhLTlQufQcHHR4HZVcYAg8HF1stDgkGHAQ+ARkIBhlbDikOHxwLCX1UF0kBAAAFLFVcRggAchdEAgcAWRQvBl0NGxc0HFkYRxsGEnAOAwBBHTkLVFQCEQ1ILA4bAAJZMR1ATQASBxZiFAUIAgE6BRU2FFhUVy8OHUtUVCRaQwIdGBFXZU9RmfHn21jW3/GVwPWW21Oj8ZXr99bf5pXA/r7b74ja7H1UF0kcBxUSOk1JSUwEPhYXVxkVGioxAE1LQlR9DUUHGlZOVQRNGx0aBCxCGEQPAFkaLAYdHUMVLxEZDxwXHxExHF0GHBNwGUcCRgQVG2AEFhBTBz4QXgdEGhECeR8SB1MPKRlbHgwJVigiQ1NLABUyHRVRSQ9WATYbHwxMTn9ax/T40FS8647H6Y/A0pmD7Em+65Tr4JLd4ZXr89bf9ZXA7X1DU0sbBz4fUklTVFYbPgIWSVISKhRbNAcVGRBhTV9JTAEtFERJU1QvVzcbBxkdTnBXVhsAWhUSNgkKRwcbYBZWBgxJDwM+AwYME1ZzWBUDHQAEBmVAXAgeHXEfUgUNEQYcJQpdAAFLMRlaDlQPAhQzGhYUTFh/Wl8fHQQHT3BAEhkHWjEZQwIGGhUZNhUWRwcbYBZWBgxJDwM+AwYME1ZzWBUDHQAEBmVAXA8aWTALXgUdWRUFNkEXHA0fOxZERQYGE1o+HxpGABUyHQgADA1JBj4HGgVDGjoPEQUIGRFIJBkSBRsRIlpqFkVUVhwvTUlJFVYrEUMHDFZOVX2f7OX+VJbS1t/xVL7qvtv8iNr7vsy8it3olcHHTV9JTAEsGVAOS05UVzYfU1UHBAAZUw8bSlZZf00GGwIHfUIXMEscAAEvVVxGBwRyGUcCRxcbGHAFAAYAWyQOVgccEQlKOQYWBQoHYgtDCh0BB1kyCgAaDxM6VFQEHBoAByZDEAYbGisKTigGEBFZLQoUAAEacwpSDAAbGjs+AhZFDR0rARsRAARYGT4bXwUBGnMMXgYMDhsbOkMaGh5YMApQRwgHWBQsARIEC1guDVIZEFgZGj0GHwxCBC0XTxJFHBsGKwYdDkxYf1pfHx0ETlpwBgMeBhtxEUREEgIVGSoKDktCVH0QQx8ZB05acAkHRAEHNhZDRggEHVs7GhACChosVlgZDlsVBTZAGhlRHzoBChgIHB0ZcgEWHkgdL0VMHQgYARAiTS4UQlR9CF4FS05UDn0bGh0CEX1CF0mZ6+fbf47H8afelszW3+2VwPq+2/aI2vN/sqiK3fuVwdCOx+KPwMOZg/NLWFRXKhwSDgtWZVgVGwAaVEkvBh0KARA6RhVHSVYBBzMcUVNOL30QQx8ZB05acA4DAEAEMAtDCgUEHRs8ABcMQB0xV0cCBxcbETpACB8PGCodSklFVFYdKxsDGlRbcBlHAkcOHQUvAAMGGhUyVkIYRh0aWiQZEgUbESJaG0tLHAABLxxJRkESK1VYGAAaAFg+HxpHCgE8E1MFGlobBzhAEhkHWy8RWQgGEBFKNAoKVB0VNxFbRgcRA1MvBh1UFQI+FEIOFFYpCHNPUQ4HAH1CFxBLAB0BMwpRU05Wr+en8km91rz1jsfypOi+zKuh8FS+6r7b/Ija+77MvIrd6JXBx01fSUwBLBlQDktOVFc4BgdJUgEsHUUFCBkRS31DU0sbBjMLFVFJL1YdKxsDGlRbcBlHAkcTHQE3GhFHDRsyV0IYDAYHWiQZEgUbESJaG0tLHAABLxxJRkESK1VYGAAaAFg+HxpHCgE8E1MFGlobBzhAEhkHWzgRQ1QCEQ1ILA4bAAJZMR1ATRwHEQcxDh4MUw8pGVseDAlWKCJDU0sHGiwMVklTVA9XKwYHBQtWZVgVm/bnzFWWxbrdhOjumYPwiMD0vP2l84ja9L7Mukuj65XB0I7H5o/A1JmD94jA7FdzT1EcHRU4HRVRSVYdGywbEklSASwdRQUIGRFLfUNTSxsGMwsVUUkvVh0rGwMaVFtwF0QCBwBaHDEZEgUHED4BQhgBHFoCMB0YDBwHcRxSHUYdGgYrDkwCCw1iCFIZBBUaEDEbVRhTDykZWx4MCVYoIkNTSwwTMhEVUUkPVgE2Gx8MTE5/Wsf059pUv8am0Yja+ZbSF4H1xZXBxI7H6Y/AxJKr2ktYVFcqHBIOC1ZlWBUJDhkdVWMaGg1QVnNYFR4bGAdXZU8oSwYAKwhEUUZbEgFyAAAAAAByGUcCRxABFjQLHRpAGy0fGAoZHVsXOAIaVgURJkVECgEdGFgxCgRPGx07RUwdCBgBECJNLhRCVH0eUUlTVA9XKwYHBQtWZVgVm/bg0VW188Oj7pXr/9bf7p7oxZbFuemPwNhY3ffYlcDuvtvziNrvteSGSUVUVgAsDhQMTE5/WlENSUgBHDtRUUVOVioKWxhLTlQufQcHHR4HZVcYDR1ZGwY2AQdEDwQ2VlMeCh8QGyxBHBsJWz4IXkQPEkseOhZOGg8cNhQaBQwDUgA2C04SGBUzDVIWSykJWX9NFwcdVmVYTEkdHQAZOk1JSUyEwOy5S4jA8bzrhe/YTr7AmYPkiMD7lOvkkt3ylevgFUdJVgEGPggWS1RUfRxZGElIEBoyDhoHUFZzWBUeGxgHV2VPKEsGACsIRFFGWxAbLEEUBgETMx0YGQwHGxkpCkwHDxk6RUwdCBgBECJJBxAeEWI5FUdJVhwBKx8AU0FbOxZERQ4bGxIzClwbCwcwFEEOVhoVGDpSCB8PGCodSk0dDQQQYiIrS0JUfRBDHxkHTlpwCx0aQBMwF1AHDFsGECwAHx8LSzEZWg5UDwIUMxoWFEgAJghSVj0sIFcCEl9JTAM3F14YS05UDn0bGh0CEX1CF0mZ6+fpf47HyKTovsy4osOe6MR/peyI2vu+zLiK3f+VwcOOx/FMWH9aQhgIExFXZU9RHgYbNgsXVw0bGRQ2AU1LQlR9DUUHGlZOVQRNGx0aBCxCGEQIBB1bNw4QAgsGKxlFDAwAWhYwAlweBhs2CxhUGEkPAz4DBgwTVgIFG0tLFh0bfVVTEkwANgxbDktOVFev8OHaTr7GsZ2i3VS+6r7b/Ija+77MvIrd6JXBx01fSUwBLBlQDktOVFc9Bh1JUkI7EVACHUpWWX9NBhsCB31CFzBLHAABLxxJRkEYMBdcHhlaFhwxAxoaGloxHUNEEgIVGSoKDkszCXNYFR4aEQZXZU8ISxodKxRSSVNUVoXA+saG1vt/mYP3g+jFlOvouemnwL7Mt4rd+ZXB2E+S3eq+w5mD7IjA8JTr5FFFTlYqC1YMDFZOVX0aAAwcVGMNRA4bGhUYOlFRRU5WKgpbGEtOVC59BwcdHgdlVxgKGR1aEjYbGxwMWjwXWkQcBxEHLEAIHw8YKh1KSTQJCQ=="
_API_XK = b"kittu_osint_x7"

def _decode_api_pack():
    try:
        raw = base64.b64decode(_API_BLOB.encode())
        plain = bytes(b ^ _API_XK[i % len(_API_XK)] for i, b in enumerate(raw))
        return json.loads(plain.decode("utf-8"))
    except Exception:
        return {}

def _builtin_apis():
    return _decode_api_pack()

def seed_builtin_apis():
    pack = _builtin_apis()
    if not pack:
        return 0
    n = 0
    with _lock:
        for cmd, meta in pack.items():
            urls = meta.get("urls") or []
            title = meta.get("title") or cmd
            usage = meta.get("usage") or (cmd + " <value>")
            row = _conn.execute("SELECT added_by FROM custom_apis WHERE cmd=?", (cmd,)).fetchone()
            if row is None:
                _conn.execute("INSERT INTO custom_apis (cmd,title,usage,urls,added_at,added_by) VALUES (?,?,?,?,?,?)", (cmd, title, usage, json.dumps(urls), _now(), 0))
                n += 1
            elif int(row['added_by'] or 0) == 0:
                _conn.execute("UPDATE custom_apis SET title=?, usage=?, urls=? WHERE cmd=?", (title, usage, json.dumps(urls), cmd))
                n += 1
        _conn.commit()
    return n

def resolve_api(cmd):
    pack = _builtin_apis()
    meta = pack.get(cmd) or {}
    row = db_get_custom_api(cmd)
    urls = []
    title = None
    usage = None
    if row:
        try:
            urls = json.loads(row["urls"] or "[]")
        except Exception:
            urls = []
        title = row.get("title")
        usage = row.get("usage")
    if not urls and meta:
        title = meta.get("title", cmd)
        usage = meta.get("usage", cmd)
        urls = list(meta.get("urls") or [])
    # Inject premium number / family sources from integrated APIs
    if cmd in ("num", "number", "phone"):
        for extra in (ASTHA_NUM_API, NUMINFO_API, UNKNOWNAPIS_NUM):
            if extra not in urls:
                urls.append(extra)
        title = title or "📱 ᴘʜᴏɴᴇ ᴏꜱɪɴᴛ"
        usage = usage or "num <phone>"
    if cmd in ("family", "fam"):
        if FAMILY_API_EXTRA not in urls:
            urls.append(FAMILY_API_EXTRA)
    if cmd == "tg":
        # keep astha already in pack; ensure present
        astha_tg = "https://astha-9vd8.onrender.com/tapi-e79c7312cf5329b07b0ad3ee2aeaea19?Astha={value}"
        if astha_tg not in urls:
            urls.append(astha_tg)
    if not title and not urls:
        return None, None, []
    return title, usage, urls

def _mask_url(u):
    try:
        if "://" in u:
            host = u.split("://", 1)[1].split("/", 1)[0]
            return "https://" + host + "/•••"
    except Exception:
        pass
    return "•••hidden•••"


# ============================================================
#  CONFIG
# ============================================================
load_dotenv()
BOT_TOKEN          = os.getenv("BOT_TOKEN", "").strip()
BOT_NAME           = os.getenv("BOT_NAME", "ᴋɪᴛᴛᴜ ᴏꜱɪɴᴛ")
BOT_USERNAME       = os.getenv("BOT_USERNAME", "kittuosintxbot").lstrip("@")
DEVELOPER_NAME     = os.getenv("DEVELOPER_NAME", "#𝐊 𝐈 𝐓 𝐓 𝐔")
OWNER_ID           = int(os.getenv("OWNER_ID", "0") or 0)
MAIN_GC_ID         = int(os.getenv("MAIN_GC_ID", "0") or 0)
# Force-join targets (public channels + main GC). Seeded on bot start.
FORCE_JOIN_CHATS   = [
    {"username": "shinzu_updates"},
    {"username": "kittu_domin"},
    {"username": "kittuotps"},
    {"username": "kittu_modz"},
    {"chat_id": MAIN_GC_ID, "title": "Main GC"},
]

DB_PATH            = os.getenv("DB_PATH", "bot_data.db")
DATABASE_URL       = os.getenv("DATABASE_URL", "").strip()  # postgres://... (Neon/Supabase)
# Turso remote SQLite — bot's own DB (users/VIP/credits) lives here; external OSINT DBs stay on VPS/RDP
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_AUTH_TOKEN   = os.getenv("TURSO_AUTH_TOKEN", "").strip()
USE_TURSO          = bool(TURSO_DATABASE_URL.startswith("libsql://") and TURSO_AUTH_TOKEN and libsql is not None)
USE_PG             = (not USE_TURSO) and bool(DATABASE_URL.startswith(("postgres://", "postgresql://")))
EXTERNAL_DB_PATH   = os.getenv("EXTERNAL_DB_PATH", "").strip()
EXTERNAL_DB_CANDIDATES = ["external.db", "osint.db", "data.db", "numbers.db", "phone.db", "leak.db"]
MAX_EXTERNAL_DBS = 20
MAX_EXTERNAL_DB_BYTES = 3 * 1024 * 1024 * 1024  # 3 GB per DB
EXTERNAL_DB_CAP_TOTAL = MAX_EXTERNAL_DBS * MAX_EXTERNAL_DB_BYTES  # 60 GB VPS/RDP
INTERNAL_DB_CAP_BYTES = int(os.getenv("INTERNAL_DB_CAP_GB", "9")) * 1024 * 1024 * 1024  # Turso free ~9GB
TG_BOT_FILE_LIMIT = 20 * 1024 * 1024  # Telegram getFile limit ~20MB
ASTHA_NUM_API = "https://astha-9vd8.onrender.com/tapi-c3177593b1359e00d0e6c1a2d2cc6408?Astha={value}"
NUMINFO_API = "https://numinfotitan.vercel.app/search?num={value}&key=TITANKENG"
UNKNOWNAPIS_NUM = "https://unknownapis-dev.onrender.com/api/num?key=6767&query={value}"
FAMILY_API_EXTRA = "https://dark-info.site/familyinfo/api.php?key=8272828&num={value}"

LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "7"))
DEFAULT_CREDITS    = int(os.getenv("DEFAULT_CREDITS", "5"))
PREMIUM_CREDITS    = int(os.getenv("PREMIUM_CREDITS", "10"))
REF_CREDIT         = int(os.getenv("REF_CREDIT", "1"))
REF_CREDIT_PREMIUM = int(os.getenv("REF_CREDIT_PREMIUM", "2"))
REF_BONUS_EVERY    = int(os.getenv("REF_BONUS_EVERY", "5"))
REF_BONUS_AMOUNT   = int(os.getenv("REF_BONUS_AMOUNT", "5"))

SPIN_UNLOCK_REFS   = 2
SPIN_COOLDOWN_HRS  = 24

DB_EXPORT_THRESHOLD = 1024 * 1024 * 1024
HISTORY_FILENAME = "kittu lookup.txt"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("OSINT")

# Active long-running tasks per user (for /cancel)
# uid -> {"task": asyncio.Task, "msg": Message|None, "cmd": str, "kind": str}
_active_jobs: dict = {}

BAR_TOTAL = 10
LINE = "––––––––––––——–––——––"

# ---------- Premium custom emoji (tg-emoji) ----------
# Reply keyboards cannot render custom emoji entities — message text uses these.
_PE_IDS = {
    '🔎': "5893382531037794941",
    '👑': "5217822164362739968",
    '💎': "5427168083074628963",
    '🗂': "6285289221531903643",
    '⭐': "6222270343218733968",
    '📖': "5222444124698853913",
    '🛡': "6282759103542468958",
    '⚜️': "5407091670766343316",
    '⬅': "5888484185261216745",
    '✈️': "5231361378748472914",
    '📱': "5334954057192719331",
    '🆔': "5841276284155467413",
    '👨\u200d👩\u200d👧': "6082576398772345226",
    '🚗': "5341791400314817338",
    '📄': "5839323457015256759",
    '💳': "5897958754267174109",
    '💸': "5409048419211682843",
    '🏦': "5967822972931542886",
    '📛': "5314758060109999146",
    '🌐': "5447410659077661506",
    '📍': "5391032818111363540",
    '🐙': "5388723478620812089",
    '📸': "6005986106703613755",
    '🎮': "5361741454685256344",
    '🔥': "6219968657359904591",
    '✨': "6179087861556452050",
    '📜': "5956561916573782596",
    '🕵️': "5267369783262722280",
    '📊': "5895444149699612825",
    '💰': "5893473283696759404",
    '🗑': "5445267414562389170",
    '📋': "5956561916573782596",
    '🔌': "5289939608769929229",
    '📥': "5877307202888273539",
    '🗄': "5839323457015256759",
    '📢': "6269365454188319459",
    '✏': "5395444784611480792",
    '🖼': "5931629923478278721",
    '👥': "5846008814129649022",
    '➕': "5397916757333654639",
    '✅': "6267008582294705964",
    '🎁': "5328033559208822003",
    '🔁': "6005843436479975944",
    '🌑': "6257760379540084819",
    '🌒': "5192780297413893424",
    '🌓': "5195318953798309404",
    '🌔': "5440676433825397802",
    '🌕': "5352928113074401358",
    '⚡': "6206466620211077526",
    '💫': "6267221672802128744",
    '🚀': "5388927790215082522",
    '🎯': "5256131095094652290",
    '🤖': "5244454921557789695",
    '👨\u200d💻': "5301193436697731090",
    '📡': "5256134032852278918",
    '🔒': "5197288647275071607",
    '👤': "5249053508681883137",
    '👇': "5284998790061761264",
    '🔐': "5291873529464122510",
    '⚠': "5348177037431414677",
    '❌': "5215204871422093648",
    '👋': "4963072209334567688",
    '🎨': "5258450450448915742",
    '⏰': "6334603778326529773",
    '💨': "5296369303661067030",
    '🔓': "6129589862413638401",
    '🔗': "5231012545799666522",
    '🔍': "5251450740383170139",
    '❓': "6089234491434341490",
    '✍': "6007803303071587429",
    '📦': "6267144651153609853",
    '🚨': "6267172559851099903",
}
_PE_ALIAS = {
    "✏️": "✏", "⚠️": "⚠", "🛡️": "🛡", "🗂️": "🗂", "⬅️": "⬅",
    "🕵️‍♂️": "🕵️", "🕵": "🕵️", "✍️": "✍", "✒️": "✍", "🗑️": "🗑",
    "📌": "📍", "➡️": "→",
}

def pe(emoji: str) -> str:
    """HTML custom premium emoji for message bodies. Fallback = original glyph."""
    e = _PE_ALIAS.get(emoji, emoji)
    eid = _PE_IDS.get(e)
    if not eid:
        return emoji  # keep as-is (e.g. →)
    return f'<tg-emoji emoji-id="{eid}">{e}</tg-emoji>'

def pe_text(text: str) -> str:
    """Replace known unicode emojis in a string with premium tg-emoji tags."""
    if not text:
        return text
    # longer sequences first
    keys = sorted(_PE_IDS.keys(), key=len, reverse=True)
    out = text
    for k in keys:
        if k in out:
            out = out.replace(k, pe(k))
    return out

# ---------- Title Small-Caps style ----------
# First letter = regular LATIN CAP, remaining letters = Unicode small-caps
_SC_LATIN = "abcdefghijklmnopqrstuvwxyz"
_SC_GLYPH = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
_LATIN_TO_SC = str.maketrans(_SC_LATIN + _SC_LATIN.upper(), _SC_GLYPH + _SC_GLYPH)
_SC_TO_LATIN = {g: l for g, l in zip(_SC_GLYPH, _SC_LATIN)}
_SC_SET = set(_SC_GLYPH)

def _to_smallcaps(s: str) -> str:
    return s.translate(_LATIN_TO_SC)

def tsc(text: str) -> str:
    """
    Title Small-Caps: each word → first letter regular UPPER, rest small-caps.
    Example: 'osint lookup' → 'Oꜱɪɴᴛ Lᴏᴏᴋᴜᴘ'
    Preserves non-letters (digits, emoji, punctuation).
    """
    if not text:
        return text
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # normalize existing small-cap to latin for processing
        if ch in _SC_TO_LATIN:
            ch = _SC_TO_LATIN[ch]
        if ch.isalpha():
            # start of a word-run of letters
            j = i
            letters = []
            while j < n:
                c = text[j]
                if c in _SC_TO_LATIN:
                    c = _SC_TO_LATIN[c]
                if not c.isalpha():
                    break
                letters.append(c)
                j += 1
            word = "".join(letters)
            if word:
                first = word[0].upper()
                rest = _to_smallcaps(word[1:].lower()) if len(word) > 1 else ""
                out.append(first + rest)
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)

def style_sc_html(text: str) -> str:
    """
    Apply tsc() to visible text outside HTML tags / <code> blocks.
    Keeps tags, @usernames (bot username), URLs, and pure digits intact.
    """
    if not text:
        return text
    # Protect @usernames from small-caps (e.g. @kittuosintxbot)
    _placeholders = {}
    def _protect_at(m):
        key = f"\x00AT{len(_placeholders)}\x00"
        _placeholders[key] = m.group(0)
        return key
    text = re.sub(r"@[A-Za-z][A-Za-z0-9_]{3,}", _protect_at, text)
    parts = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "<":
            j = text.find(">", i)
            if j == -1:
                parts.append(text[i:])
                break
            tag = text[i:j + 1]
            parts.append(tag)
            i = j + 1
            low = tag.lower()
            if low.startswith("<code") or low.startswith("<pre"):
                close = "</code>" if low.startswith("<code") else "</pre>"
                k = text.lower().find(close, i)
                if k == -1:
                    parts.append(text[i:])
                    break
                parts.append(text[i:k])
                parts.append(text[k:k + len(close)])
                i = k + len(close)
            continue
        j = text.find("<", i)
        if j == -1:
            j = n
        chunk = text[i:j]
        parts.append(tsc(chunk))
        i = j
    out = "".join(parts)
    for k, v in _placeholders.items():
        out = out.replace(k, v)
    return out


def progress_emoji(pct):
    if pct <= 0:   return "🌀"
    if pct < 20:   return "🌒"
    if pct < 30:   return "🌓"
    if pct < 40:   return "🌔"
    if pct < 50:   return "🌕"
    if pct < 60:   return "⚡"
    if pct < 70:   return "🔥"
    if pct < 80:   return "💫"
    if pct < 90:   return "✨"
    if pct < 100:  return "🚀"
    return "🎯"

def progress_bar(filled, total=BAR_TOTAL):
    return "▰" * filled + "▱" * (total - filled)

# ============================================================
#  DATABASE  (SQLite local OR remote Postgres via DATABASE_URL)
#  Set DATABASE_URL=postgresql://... on Neon/Supabase/Railway
#  so VPS/RDP change does NOT lose users/credits/premium data.
# ============================================================
_lock = threading.Lock()

def _pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url

def _connect_db():
    # 1) Turso remote SQLite (preferred for permanent bot DB)
    if USE_TURSO:
        if libsql is None:
            raise SystemExit("Turso URL set but libsql missing. Run: pip install libsql")
        conn = libsql.connect(TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
        log.info("DB backend: Turso remote SQLite (%s) — survives VPS change", TURSO_DATABASE_URL)
        return conn
    if TURSO_DATABASE_URL.startswith("libsql://") and not TURSO_AUTH_TOKEN:
        log.warning("Turso URL set but TURSO_AUTH_TOKEN missing — using local SQLite until token is set")
    # 2) Postgres
    if USE_PG and not USE_TURSO:
        if psycopg2 is None:
            raise SystemExit("DATABASE_URL set but psycopg2 missing. Run: pip install psycopg2-binary")
        conn = psycopg2.connect(_pg_url(DATABASE_URL), cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        log.info("DB backend: PostgreSQL (remote) — data survives VPS change")
        return conn
    # 3) Local SQLite fallback
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass
    log.info("DB backend: SQLite local file %s", DB_PATH)
    return conn

_conn = _connect_db()

class _ConnProxy:
    """Make sqlite-style ? and INSERT OR IGNORE work on Postgres too."""
    def __init__(self, conn):
        self._c = conn
    def execute(self, sql, args=()):
        q = sql
        if USE_PG:
            q = q.replace("?", "%s")
            if "INSERT OR IGNORE INTO" in q.upper():
                # best-effort: append ON CONFLICT DO NOTHING when table has obvious PK
                q2 = q.replace("INSERT OR IGNORE INTO", "INSERT INTO").replace("insert or ignore into", "INSERT INTO")
                if "ON CONFLICT" not in q2.upper():
                    # try detect table
                    import re as _re
                    m = _re.search(r"INSERT INTO\s+(\w+)", q2, _re.I)
                    if m:
                        table = m.group(1).lower()
                        conflict = {
                            "users": "user_id",
                            "channels": "chat_id",
                            "groups": "chat_id",
                            "settings": "key",
                            "api_status": "name",
                            "custom_apis": "cmd",
                            "spins": "user_id",
                            "join_requests": "user_id, chat_id",
                            "generated_apis": "api_key",
                        }.get(table)
                        if conflict:
                            q2 = q2.rstrip("; \n ") + f" ON CONFLICT ({conflict}) DO NOTHING"
                q = q2
            if "INSERT OR REPLACE INTO" in q.upper() or "insert or replace into" in q:
                q = q.replace("INSERT OR REPLACE INTO", "INSERT INTO").replace("insert or replace into", "INSERT INTO")
                if "ON CONFLICT" not in q.upper():
                    import re as _re
                    m = _re.search(r"INSERT INTO\s+(\w+)", q, _re.I)
                    if m:
                        table = m.group(1).lower()
                        conflict = {
                            "settings": "key",
                            "api_status": "name",
                            "custom_apis": "cmd",
                            "spins": "user_id",
                            "generated_apis": "api_key",
                        }.get(table, None)
                        if conflict:
                            # DO UPDATE all non-pk — simplified: DO NOTHING then separate update preferred
                            q = q.rstrip("; \n ") + f" ON CONFLICT ({conflict}) DO NOTHING"
        # libsql Connection supports .execute directly; cursor() too
        try:
            cur = self._c.cursor()
            cur.execute(q, tuple(args) if args is not None else ())
        except Exception:
            # some libsql builds: connection.execute
            cur = self._c.execute(q, tuple(args) if args is not None else ())
        return _DictCursor(cur)
    def commit(self):
        return self._c.commit()
    def rollback(self):
        try:
            return self._c.rollback()
        except Exception:
            return None
    def close(self):
        return self._c.close()
    def cursor(self):
        return _DictCursor(self._c.cursor())

class _DictCursor:
    """Normalize sqlite3 / libsql / psycopg2 rows to dict-friendly access."""
    def __init__(self, cur):
        self._cur = cur
    def execute(self, *a, **k):
        self._cur.execute(*a, **k)
        return self
    def _to_dict(self, row):
        if row is None:
            return None
        if isinstance(row, dict):
            return dict(row)
        # sqlite3.Row
        try:
            return dict(row)
        except Exception:
            pass
        desc = getattr(self._cur, "description", None)
        if desc:
            keys = [d[0] for d in desc]
            return {keys[i]: row[i] for i in range(len(keys))}
        return row
    def fetchone(self):
        return self._to_dict(self._cur.fetchone())
    def fetchall(self):
        rows = self._cur.fetchall() or []
        return [self._to_dict(r) for r in rows]
    def __getattr__(self, name):
        return getattr(self._cur, name)

_conn = _ConnProxy(_conn)


def _adapt_sql(sql: str) -> str:
    """SQLite -> Postgres placeholder + dialect tweaks."""
    if not USE_PG:
        return sql
    s = sql
    # placeholders
    s = s.replace("?", "%s")
    # common SQLite-isms
    s = s.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    s = s.replace("INSERT OR REPLACE INTO", "INSERT INTO")
    return s

def db_execute(sql, args=(), commit=False, fetch=None):
    """Unified execute. fetch: None | 'one' | 'all' | 'val'"""
    with _lock:
        cur = _conn.cursor()
        q = _adapt_sql(sql)
        # Postgres INSERT OR IGNORE / OR REPLACE need ON CONFLICT — handled in callers for critical paths
        try:
            cur.execute(q, tuple(args) if args is not None else ())
        except Exception:
            if USE_PG:
                _conn.rollback()
            raise
        if commit:
            _conn.commit()
        if fetch == "one":
            r = cur.fetchone()
            return dict(r) if r else None
        if fetch == "all":
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        if fetch == "val":
            r = cur.fetchone()
            if not r:
                return None
            if isinstance(r, dict):
                return list(r.values())[0]
            return r[0]
        return cur

def db_commit():
    with _lock:
        _conn.commit()

def _now(): return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")

def init_db():
    with _lock:
        if USE_PG:
            stmts = [
                """CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY, username TEXT, first_name TEXT,
                    credits INTEGER DEFAULT 5, is_premium INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0, verified INTEGER DEFAULT 0,
                    referrer_id BIGINT, refer_count INTEGER DEFAULT 0,
                    joined_at TEXT, last_active TEXT)""",
                "CREATE INDEX IF NOT EXISTS idx_u_prem ON users(is_premium)",
                "CREATE INDEX IF NOT EXISTS idx_u_ref ON users(referrer_id)",
                """CREATE TABLE IF NOT EXISTS logs (
                    id BIGSERIAL PRIMARY KEY, user_id BIGINT,
                    command TEXT, input TEXT, sources INTEGER, success INTEGER, created_at TEXT)""",
                "CREATE INDEX IF NOT EXISTS idx_logs_time ON logs(created_at)",
                """CREATE TABLE IF NOT EXISTS contacts (
                    id BIGSERIAL PRIMARY KEY,
                    owner_id BIGINT, tg_user_id BIGINT,
                    phone TEXT, first_name TEXT, last_name TEXT, shared_at TEXT)""",
                "CREATE INDEX IF NOT EXISTS idx_contacts_tg ON contacts(tg_user_id)",
                "CREATE INDEX IF NOT EXISTS idx_contacts_owner ON contacts(owner_id)",
                """CREATE TABLE IF NOT EXISTS channels (
                    chat_id BIGINT PRIMARY KEY, username TEXT, invite_link TEXT,
                    title TEXT, is_private INTEGER DEFAULT 0, added_at TEXT)""",
                """CREATE TABLE IF NOT EXISTS groups (
                    chat_id BIGINT PRIMARY KEY, title TEXT, added_at TEXT)""",
                """CREATE TABLE IF NOT EXISTS join_requests (
                    user_id BIGINT, chat_id BIGINT, created_at TEXT,
                    PRIMARY KEY (user_id, chat_id))""",
                "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)",
                """CREATE TABLE IF NOT EXISTS api_status (
                    name TEXT PRIMARY KEY, ok INTEGER, status INTEGER,
                    latency_ms INTEGER, checked_at TEXT)""",
                """CREATE TABLE IF NOT EXISTS custom_apis (
                    cmd TEXT PRIMARY KEY, title TEXT, usage TEXT, urls TEXT,
                    added_at TEXT, added_by BIGINT)""",
                """CREATE TABLE IF NOT EXISTS spins (
                    user_id BIGINT PRIMARY KEY, last_spin TEXT,
                    total_points INTEGER DEFAULT 0, spin_count INTEGER DEFAULT 0)""",
                """CREATE TABLE IF NOT EXISTS generated_apis (
                    api_key TEXT PRIMARY KEY, cmd TEXT, title TEXT, urls TEXT,
                    expires_at TEXT, created_by BIGINT, created_at TEXT)""",
            ]
            cur = _conn.cursor()
            for s in stmts:
                cur.execute(s)
            _conn.commit()
        else:
            # SQLite local OR Turso — one statement at a time (Turso has no executescript/PRAGMA)
            stmts = [
                """CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                    credits INTEGER DEFAULT 5, is_premium INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0, verified INTEGER DEFAULT 0,
                    referrer_id INTEGER, refer_count INTEGER DEFAULT 0,
                    joined_at TEXT, last_active TEXT)""",
                "CREATE INDEX IF NOT EXISTS idx_u_prem ON users(is_premium)",
                "CREATE INDEX IF NOT EXISTS idx_u_ref ON users(referrer_id)",
                """CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    command TEXT, input TEXT, sources INTEGER, success INTEGER, created_at TEXT)""",
                "CREATE INDEX IF NOT EXISTS idx_logs_time ON logs(created_at)",
                """CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER, tg_user_id INTEGER,
                    phone TEXT, first_name TEXT, last_name TEXT, shared_at TEXT)""",
                "CREATE INDEX IF NOT EXISTS idx_contacts_tg ON contacts(tg_user_id)",
                "CREATE INDEX IF NOT EXISTS idx_contacts_owner ON contacts(owner_id)",
                """CREATE TABLE IF NOT EXISTS channels (
                    chat_id INTEGER PRIMARY KEY, username TEXT, invite_link TEXT,
                    title TEXT, is_private INTEGER DEFAULT 0, added_at TEXT)""",
                """CREATE TABLE IF NOT EXISTS groups (
                    chat_id INTEGER PRIMARY KEY, title TEXT, added_at TEXT)""",
                """CREATE TABLE IF NOT EXISTS join_requests (
                    user_id INTEGER, chat_id INTEGER, created_at TEXT,
                    PRIMARY KEY (user_id, chat_id))""",
                "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)",
                """CREATE TABLE IF NOT EXISTS api_status (
                    name TEXT PRIMARY KEY, ok INTEGER, status INTEGER,
                    latency_ms INTEGER, checked_at TEXT)""",
                """CREATE TABLE IF NOT EXISTS custom_apis (
                    cmd TEXT PRIMARY KEY, title TEXT, usage TEXT, urls TEXT,
                    added_at TEXT, added_by INTEGER)""",
                """CREATE TABLE IF NOT EXISTS spins (
                    user_id INTEGER PRIMARY KEY, last_spin TEXT,
                    total_points INTEGER DEFAULT 0, spin_count INTEGER DEFAULT 0)""",
                """CREATE TABLE IF NOT EXISTS generated_apis (
                    api_key TEXT PRIMARY KEY, cmd TEXT, title TEXT, urls TEXT,
                    expires_at TEXT, created_by INTEGER, created_at TEXT)""",
            ]
            if not USE_TURSO:
                try:
                    _conn.execute("PRAGMA journal_mode=WAL")
                    _conn.execute("PRAGMA synchronous=NORMAL")
                except Exception:
                    pass
            for s in stmts:
                _conn.execute(s)
            _conn.commit()

def db_get_user(uid):
    with _lock:
        r = _conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
        return dict(r) if r else None

def db_create_user(uid, username, first_name, referrer_id=None):
    is_prem_ref = 0
    if referrer_id:
        ref = db_get_user(referrer_id)
        if ref and ref["is_premium"]: is_prem_ref = 1
    credits = PREMIUM_CREDITS if is_prem_ref else DEFAULT_CREDITS
    with _lock:
        if USE_PG:
            _conn.cursor().execute(
                """INSERT INTO users
                (user_id,username,first_name,credits,referrer_id,joined_at,last_active)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING""",
                (uid, username, first_name, credits, referrer_id, _now(), _now()))
        else:
            _conn.execute("""INSERT OR IGNORE INTO users
                (user_id,username,first_name,credits,referrer_id,joined_at,last_active)
                VALUES (?,?,?,?,?,?,?)""",
                (uid, username, first_name, credits, referrer_id, _now(), _now()))
        _conn.commit()
    if referrer_id: _give_referral(referrer_id)

def _give_referral(ref_id):
    ref = db_get_user(ref_id)
    if not ref: return
    amt = REF_CREDIT_PREMIUM if ref["is_premium"] else REF_CREDIT
    cnt = ref["refer_count"] + 1
    bonus = REF_BONUS_AMOUNT if cnt % REF_BONUS_EVERY == 0 else 0
    with _lock:
        _conn.execute("UPDATE users SET credits=credits+?, refer_count=? WHERE user_id=?",
                      (amt + bonus, cnt, ref_id))
        _conn.commit()

def db_update_activity(uid, username=None, first_name=None):
    with _lock:
        _conn.execute("""UPDATE users SET last_active=?,
            username=COALESCE(?,username), first_name=COALESCE(?,first_name)
            WHERE user_id=?""", (_now(), username, first_name, uid))
        _conn.commit()

def db_add_credits(uid, n):
    with _lock:
        _conn.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (n, uid)); _conn.commit()

def db_deduct_credit(uid, n=1):
    # Portable clamp (SQLite MAX() / Postgres GREATEST both avoided via CASE)
    with _lock:
        _conn.execute(
            "UPDATE users SET credits = CASE WHEN credits > ? THEN credits - ? ELSE 0 END WHERE user_id=?",
            (n, n, uid))
        _conn.commit()

def db_set_premium(uid, v=True):
    with _lock:
        _conn.execute("UPDATE users SET is_premium=? WHERE user_id=?", (1 if v else 0, uid)); _conn.commit()

def db_set_admin(uid, v=True):
    with _lock:
        _conn.execute("UPDATE users SET is_admin=? WHERE user_id=?", (1 if v else 0, uid)); _conn.commit()

def db_list_users(only_premium=False, only_admin=False):
    q = "SELECT * FROM users"; c = []
    if only_premium: c.append("is_premium=1")
    if only_admin:   c.append("is_admin=1")
    if c: q += " WHERE " + " AND ".join(c)
    q += " ORDER BY joined_at DESC"
    with _lock: return [dict(r) for r in _conn.execute(q).fetchall()]

def db_all_user_ids():
    with _lock: return [r["user_id"] for r in _conn.execute("SELECT user_id FROM users").fetchall()]

def db_stats():
    with _lock:
        def g(q, *a):
            r = _conn.execute(q, a).fetchone()
            if r is None:
                return 0
            if isinstance(r, dict):
                return int(list(r.values())[0] or 0)
            try:
                return int(r[0] or 0)
            except Exception:
                return 0
        today = datetime.now(timezone.utc).date().isoformat()
        return {"users": g("SELECT COUNT(*) FROM users"),
                "premium": g("SELECT COUNT(*) FROM users WHERE is_premium=1"),
                "admins": g("SELECT COUNT(*) FROM users WHERE is_admin=1"),
                "verified": g("SELECT COUNT(*) FROM users WHERE verified=1"),
                "contacts": g("SELECT COUNT(*) FROM contacts"),
                "logs": g("SELECT COUNT(*) FROM logs"),
                "active": g("SELECT COUNT(*) FROM users WHERE last_active LIKE ?", today+"%")}

def db_save_contact(owner_id, tg_user_id, phone, fn, ln):
    with _lock:
        r = _conn.execute("""SELECT id FROM contacts
            WHERE owner_id=? AND tg_user_id=?""", (owner_id, tg_user_id)).fetchone()
        if r:
            _conn.execute("""UPDATE contacts SET phone=?,first_name=?,last_name=?,shared_at=?
                WHERE id=?""", (phone, fn, ln, _now(), r["id"]))
        else:
            _conn.execute("""INSERT INTO contacts
                (owner_id,tg_user_id,phone,first_name,last_name,shared_at)
                VALUES (?,?,?,?,?,?)""",
                (owner_id, tg_user_id, phone, fn, ln, _now()))
        _conn.execute("UPDATE users SET verified=1 WHERE user_id=?", (owner_id,))
        _conn.commit()

def db_find_phone_by_tg(tg_id):
    with _lock:
        r = _conn.execute("""SELECT phone, first_name, last_name FROM contacts
            WHERE tg_user_id=? ORDER BY shared_at DESC LIMIT 1""", (tg_id,)).fetchone()
        if r: return dict(r)
        r = _conn.execute("""SELECT phone, first_name, last_name FROM contacts
            WHERE owner_id=? ORDER BY shared_at DESC LIMIT 1""", (tg_id,)).fetchone()
        return dict(r) if r else None

def db_all_contacts():
    with _lock:
        return [dict(r) for r in _conn.execute("SELECT * FROM contacts ORDER BY shared_at DESC").fetchall()]

def db_contacts_count():
    with _lock: return _conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]

def db_log(uid, cmd, inp, src, ok):
    with _lock:
        _conn.execute("""INSERT INTO logs (user_id,command,input,sources,success,created_at)
            VALUES (?,?,?,?,?,?)""", (uid, cmd, inp, src, 1 if ok else 0, _now()))
        _conn.commit()

def db_get_history(uid, limit=500):
    with _lock:
        return [dict(r) for r in _conn.execute(
            "SELECT * FROM logs WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (uid, limit)).fetchall()]

def db_get_all_history(limit=500):
    with _lock:
        return [dict(r) for r in _conn.execute(
            "SELECT * FROM logs ORDER BY created_at DESC LIMIT ?",
            (limit,)).fetchall()]

def db_cleanup_logs():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=LOG_RETENTION_DAYS)).isoformat()
    with _lock:
        _conn.execute("DELETE FROM logs WHERE created_at<?", (cutoff,)); _conn.commit()
        try: _conn.execute("VACUUM")
        except: pass

def db_add_channel(cid, un, link, title, priv):
    with _lock:
        _conn.execute("""INSERT OR REPLACE INTO channels
            (chat_id,username,invite_link,title,is_private,added_at) VALUES (?,?,?,?,?,?)""",
            (cid, un, link, title, 1 if priv else 0, _now())); _conn.commit()

def db_remove_channel(cid):
    with _lock:
        _conn.execute("DELETE FROM channels WHERE chat_id=?", (cid,)); _conn.commit()

def db_list_channels():
    with _lock: return [dict(r) for r in _conn.execute("SELECT * FROM channels").fetchall()]

def db_add_group(cid, title):
    with _lock:
        _conn.execute("INSERT OR REPLACE INTO groups VALUES (?,?,?)", (cid, title, _now())); _conn.commit()

def db_remove_group(cid):
    with _lock:
        _conn.execute("DELETE FROM groups WHERE chat_id=?", (cid,)); _conn.commit()

def db_list_groups():
    with _lock: return [dict(r) for r in _conn.execute("SELECT * FROM groups").fetchall()]

def db_is_group_wl(cid):
    with _lock: return bool(_conn.execute("SELECT 1 FROM groups WHERE chat_id=?", (cid,)).fetchone())

def db_add_join_req(uid, cid):
    with _lock:
        _conn.execute("INSERT OR IGNORE INTO join_requests VALUES (?,?,?)", (uid, cid, _now()))
        _conn.commit()

def db_has_join_req(uid, cid):
    with _lock:
        return bool(_conn.execute("SELECT 1 FROM join_requests WHERE user_id=? AND chat_id=?",
                                   (uid, cid)).fetchone())

def db_set(k, v):
    with _lock:
        _conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (k, v)); _conn.commit()

def db_get(k, d=None):
    with _lock:
        r = _conn.execute("SELECT value FROM settings WHERE key=?", (k,)).fetchone()
        return r["value"] if r else d

def db_save_api(n, ok, st, ms):
    with _lock:
        _conn.execute("""INSERT OR REPLACE INTO api_status
            VALUES (?,?,?,?,?)""", (n, 1 if ok else 0, st, ms, _now())); _conn.commit()

def db_size_bytes():
    """Internal bot DB size (Turso estimate or local file)."""
    if USE_TURSO:
        try:
            with _lock:
                # Prefer page_count * page_size when supported
                try:
                    pc = _conn.execute("PRAGMA page_count").fetchone()
                    ps = _conn.execute("PRAGMA page_size").fetchone()
                    def _v(r):
                        if r is None: return None
                        if isinstance(r, dict):
                            return list(r.values())[0]
                        return r[0]
                    pages, psize = _v(pc), _v(ps)
                    if pages is not None and psize is not None:
                        return int(pages) * int(psize)
                except Exception:
                    pass
                # Fallback: rough estimate from row counts
                def cnt(table):
                    try:
                        r = _conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
                        if isinstance(r, dict):
                            return int(r.get("c") or list(r.values())[0] or 0)
                        return int(r[0] or 0)
                    except Exception:
                        return 0
                rows = cnt("users") + cnt("contacts") + cnt("logs") + cnt("settings") + cnt("custom_apis")
                return max(rows * 256, 4096)  # ~256 bytes/row estimate, min 4KB
        except Exception:
            return 0
    t = 0
    for s in ("", "-wal", "-shm"):
        p = DB_PATH + s
        if os.path.exists(p): t += os.path.getsize(p)
    return t

def _fmt_bytes(n):
    n = float(n or 0)
    if n >= 1024**3:
        return f"{n/1024**3:.2f} GB"
    if n >= 1024**2:
        return f"{n/1024**2:.1f} MB"
    if n >= 1024:
        return f"{n/1024:.1f} KB"
    return f"{int(n)} B"

def storage_progress_line(used, cap, label):
    """Faith-style bar: ▰▱ + accurate %."""
    used = max(0, int(used or 0))
    cap = max(1, int(cap or 1))
    pct = min(100, int(round(100.0 * used / cap)))
    filled = int(round(pct / 100.0 * BAR_TOTAL))
    filled = max(0, min(BAR_TOTAL, filled))
    left = max(0, cap - used)
    bar = progress_bar(filled)
    return (
        f"⚡ <b>{label}</b>\n"
        f"<code>{bar}  {pct:3d}%  {progress_emoji(pct)}</code>\n"
        f"▸ Used : <b>{_fmt_bytes(used)}</b>\n"
        f"▸ Free : <b>{_fmt_bytes(left)}</b>\n"
        f"▸ Cap  : <b>{_fmt_bytes(cap)}</b>"
    )

def get_storage_stats():
    """Internal (Turso/custom SQL) + External (VPS/RDP OSINT DBs)."""
    internal_used = db_size_bytes()
    internal_cap = INTERNAL_DB_CAP_BYTES
    # backend label
    if USE_TURSO:
        backend = "Turso (cloud SQL)"
    elif USE_PG:
        backend = "PostgreSQL (cloud)"
    else:
        backend = f"Local SQLite ({DB_PATH})"

    ext_paths = []
    try:
        ext_paths = _external_db_list()
    except Exception:
        ext_paths = []
    ext_used = 0
    for pth in ext_paths:
        try:
            ext_used += os.path.getsize(pth)
        except Exception:
            pass
    ext_cap = EXTERNAL_DB_CAP_TOTAL
    return {
        "internal_used": internal_used,
        "internal_cap": internal_cap,
        "internal_backend": backend,
        "external_used": ext_used,
        "external_cap": ext_cap,
        "external_count": len(ext_paths),
        "external_max": MAX_EXTERNAL_DBS,
    }

def format_storage_stats_html():
    s = get_storage_stats()
    internal = storage_progress_line(s["internal_used"], s["internal_cap"], "Iɴᴛᴇʀɴᴀʟ Dʙ (Cᴜꜱᴛᴏᴍ Sǫʟ)")
    external = storage_progress_line(s["external_used"], s["external_cap"], "Exᴛᴇʀɴᴀʟ Dʙ (Vᴘꜱ / Rᴅᴘ)")
    meta = (
        f"▸ Internal backend : <b>{s['internal_backend']}</b>\n"
        f"▸ External files   : <b>{s['external_count']}/{s['external_max']}</b>"
    )
    return f"{internal}\n{LINE}\n{external}\n{LINE}\n{meta}"

def db_add_custom_api(cmd, title, usage, urls, added_by):
    with _lock:
        exists = _conn.execute("SELECT 1 FROM custom_apis WHERE cmd=?", (cmd,)).fetchone()
        if exists: return False
        _conn.execute("""INSERT INTO custom_apis
            (cmd,title,usage,urls,added_at,added_by) VALUES (?,?,?,?,?,?)""",
            (cmd, title, usage, json.dumps(urls), _now(), added_by))
        _conn.commit()
        return True

def db_remove_custom_api(cmd):
    with _lock:
        _conn.execute("DELETE FROM custom_apis WHERE cmd=?", (cmd,)); _conn.commit()

def db_list_custom_apis():
    with _lock:
        return [dict(r) for r in _conn.execute(
            "SELECT * FROM custom_apis ORDER BY added_at DESC").fetchall()]

def db_get_custom_api(cmd):
    with _lock:
        r = _conn.execute("SELECT * FROM custom_apis WHERE cmd=?", (cmd,)).fetchone()
        return dict(r) if r else None

def db_update_custom_urls(cmd, urls):
    with _lock:
        _conn.execute("UPDATE custom_apis SET urls=? WHERE cmd=?", (json.dumps(urls), cmd))
        _conn.commit()

def db_add_generated_api(api_key, cmd, title, urls, expires_at, created_by):
    with _lock:
        _conn.execute(
            "INSERT OR REPLACE INTO generated_apis (api_key,cmd,title,urls,expires_at,created_by,created_at) VALUES (?,?,?,?,?,?,?)",
            (api_key, cmd, title, json.dumps(urls), expires_at, created_by, _now()))
        _conn.commit()

def db_list_generated_apis():
    with _lock:
        return [dict(r) for r in _conn.execute(
            "SELECT * FROM generated_apis ORDER BY created_at DESC").fetchall()]

def db_get_generated_api(api_key):
    with _lock:
        r = _conn.execute("SELECT * FROM generated_apis WHERE api_key=?", (api_key,)).fetchone()
        return dict(r) if r else None

def db_remove_generated_api(api_key):
    with _lock:
        _conn.execute("DELETE FROM generated_apis WHERE api_key=?", (api_key,))
        _conn.commit()

def db_cleanup_expired_generated():
    """Remove expired generated APIs from DB + matching custom_apis entries."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    removed = []
    with _lock:
        rows = [dict(r) for r in _conn.execute("SELECT * FROM generated_apis").fetchall()]
        for row in rows:
            try:
                exp = datetime.fromisoformat(row["expires_at"])
            except Exception:
                exp = now
            if exp <= now:
                key = row["api_key"]
                _conn.execute("DELETE FROM generated_apis WHERE api_key=?", (key,))
                # also drop temp custom cmd if exists
                _conn.execute("DELETE FROM custom_apis WHERE cmd=?", (key,))
                removed.append(key)
        if removed:
            _conn.commit()
    return removed

def db_can_spin(uid):
    with _lock:
        r = _conn.execute("SELECT last_spin FROM spins WHERE user_id=?", (uid,)).fetchone()
        if not r or not r["last_spin"]: return True, None
        try:
            last = datetime.fromisoformat(r["last_spin"])
            if last.tzinfo is not None:
                last = last.replace(tzinfo=None)
        except Exception:
            return True, None
        diff = datetime.now(timezone.utc).replace(tzinfo=None) - last
        cd = timedelta(hours=SPIN_COOLDOWN_HRS)
        if diff >= cd: return True, None
        return False, cd - diff

def db_do_spin(uid, points):
    with _lock:
        r = _conn.execute("SELECT total_points, spin_count FROM spins WHERE user_id=?", (uid,)).fetchone()
        if r:
            _conn.execute("""UPDATE spins SET last_spin=?, total_points=?, spin_count=?
                WHERE user_id=?""",
                (_now(), r["total_points"] + points, r["spin_count"] + 1, uid))
        else:
            _conn.execute("""INSERT INTO spins (user_id,last_spin,total_points,spin_count)
                VALUES (?,?,?,?)""", (uid, _now(), points, 1))
        _conn.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (points, uid))
        _conn.commit()


def db_find_by_phone(phone):
    if not phone: return None
    p = str(phone).strip()
    digits = "".join(c for c in p if c.isdigit())
    variants = {p, p.lstrip("+"), digits}
    if len(digits) >= 10:
        last10 = digits[-10:]
        variants.update([last10, "+91"+last10, "91"+last10])
    with _lock:
        for v in variants:
            if not v: continue
            like = "%%%s%%" % (v[-10:] if len(v) >= 10 else v)
            r = _conn.execute("SELECT phone, first_name, last_name, owner_id, tg_user_id, shared_at FROM contacts WHERE phone=? OR phone LIKE ? ORDER BY shared_at DESC LIMIT 1", (v, like)).fetchone()
            if r: return dict(r)
    return None


# ---------- External / user-supplied DB (read-only lookup) ----------
_ext_lock = threading.Lock()
_ext_conn = None
_ext_path = None
_ext_cols_cache = {}

def _detect_external_path():
    """Resolve external DB path: setting > env > common filenames next to bot."""
    p = (db_get("external_db_path") or "").strip() or EXTERNAL_DB_PATH
    if p and os.path.isfile(p):
        return p
    base = os.path.dirname(os.path.abspath(DB_PATH)) or "."
    for name in EXTERNAL_DB_CANDIDATES:
        cand = os.path.join(base, name)
        if os.path.isfile(cand):
            return cand
        cand2 = os.path.join(os.getcwd(), name)
        if os.path.isfile(cand2):
            return cand2
    return None


def _external_db_list():
    """List of registered external DB paths (max MAX_EXTERNAL_DBS)."""
    raw = db_get("external_db_list")
    try:
        lst = json.loads(raw) if raw else []
        if not isinstance(lst, list):
            lst = []
    except Exception:
        lst = []
    single = (db_get("external_db_path") or "").strip()
    if single and single not in lst and os.path.isfile(single):
        lst.append(single)
    # also candidates
    base = os.path.dirname(os.path.abspath(DB_PATH)) or "."
    for name in EXTERNAL_DB_CANDIDATES:
        cand = os.path.join(base, name)
        if os.path.isfile(cand) and cand not in lst:
            lst.append(cand)
    return [p for p in lst if p and os.path.isfile(p)][:MAX_EXTERNAL_DBS]

def _external_db_list_save(lst):
    clean = []
    for p in lst:
        p = str(p).strip()
        if p and p not in clean:
            clean.append(p)
    db_set("external_db_list", json.dumps(clean[:MAX_EXTERNAL_DBS]))
    if clean:
        db_set("external_db_path", clean[0])  # primary
    return clean[:MAX_EXTERNAL_DBS]

def _external_db_register(path):
    """Register a DB path with size + count limits. Returns (ok, msg)."""
    if not path or not os.path.isfile(path):
        return False, "File not found"
    size = os.path.getsize(path)
    if size > MAX_EXTERNAL_DB_BYTES:
        return False, f"File too large ({size/1024/1024/1024:.2f} GB). Max 3 GB per DB."
    lst = _external_db_list()
    if path in lst:
        return True, "Already registered"
    if len(lst) >= MAX_EXTERNAL_DBS:
        return False, f"Limit reached: max {MAX_EXTERNAL_DBS} external DBs (20×3GB)."
    lst.append(path)
    _external_db_list_save(lst)
    return True, f"Registered ({len(lst)}/{MAX_EXTERNAL_DBS}) size={size/1024/1024:.1f} MB"

def open_external_db(path=None, force=False):
    """Open/reopen external sqlite read-only. Returns True if ready."""
    global _ext_conn, _ext_path, _ext_cols_cache
    path = path or _detect_external_path()
    if not path:
        return False
    if not force and _ext_conn is not None and _ext_path == path:
        return True
    with _ext_lock:
        try:
            if _ext_conn:
                try:
                    _ext_conn.close()
                except Exception:
                    pass
            uri = "file:%s?mode=ro" % path.replace("\\", "/")
            _ext_conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            _ext_conn.row_factory = sqlite3.Row
            _ext_path = path
            _ext_cols_cache = {}
            return True
        except Exception as e:
            log.warning("external db open failed: %s", e)
            _ext_conn = None
            _ext_path = None
            return False

def external_db_info():
    paths = _external_db_list()
    if not paths:
        path = _ext_path or _detect_external_path()
        paths = [path] if path else []
    if not paths:
        return {"path": None, "ok": False, "tables": 0, "rows": 0, "count": 0, "paths": []}
    total_tables = 0
    total_rows = 0
    infos = []
    for path in paths:
        ok = open_external_db(path, force=True)
        if not ok:
            infos.append({"path": path, "ok": False, "size_mb": 0})
            continue
        with _ext_lock:
            tables = [r[0] for r in _ext_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
            rows = 0
            for t in tables[:20]:
                try:
                    rows += _ext_conn.execute("SELECT COUNT(*) FROM [%s]" % t.replace("]", "")).fetchone()[0]
                except Exception:
                    pass
            size_mb = os.path.getsize(path) / (1024 * 1024) if os.path.isfile(path) else 0
            total_tables += len(tables)
            total_rows += rows
            infos.append({"path": path, "ok": True, "tables": len(tables), "rows": rows, "size_mb": round(size_mb, 1)})
    primary = paths[0]
    return {
        "path": primary,
        "ok": any(i.get("ok") for i in infos),
        "tables": total_tables,
        "rows": total_rows,
        "count": len(paths),
        "max": MAX_EXTERNAL_DBS,
        "paths": infos,
        "table_names": [],
    }

def _ext_table_cols(table):
    if table in _ext_cols_cache:
        return _ext_cols_cache[table]
    with _ext_lock:
        cols = [r[1].lower() for r in _ext_conn.execute("PRAGMA table_info([%s])" % table.replace("]", "")).fetchall()]
    _ext_cols_cache[table] = cols
    return cols

_PHONE_KEYS = ("phone", "mobile", "number", "num", "phone_number", "phonenumber", "msisdn", "contact", "alt")
_NAME_KEYS = ("name", "full_name", "fullname", "owner", "owner_name", "first_name", "fname")
_TG_KEYS = ("tg_id", "telegram_id", "user_id", "tgid", "userid", "chat_id", "id")
_ADDR_KEYS = ("address", "addr", "city", "state", "region", "circle", "operator")
_FATHER_KEYS = ("father", "father_name", "fname_father")

def _row_to_dict(row, cols):
    d = {}
    for i, c in enumerate(cols):
        try:
            d[c] = row[i]
        except Exception:
            pass
    return d

def _pick(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, "", "null", "None", "N/A"):
            return d[k]
    return None

def _search_external_db(value):
    """Search ALL registered external DBs (max 20)."""
    all_hits = []
    paths = _external_db_list()
    if not paths:
        # fallback single
        if not open_external_db():
            return None
        paths = [_ext_path] if _ext_path else []
    for path in paths:
        try:
            if not open_external_db(path, force=True):
                continue
            hit = _search_external_db_one(value)
            if hit:
                if isinstance(hit, dict) and hit.get("matches"):
                    for h in hit["matches"]:
                        h["db_file"] = os.path.basename(path)
                        all_hits.append(h)
                elif isinstance(hit, dict):
                    hit["db_file"] = os.path.basename(path)
                    all_hits.append(hit)
                elif isinstance(hit, list):
                    for h in hit:
                        if isinstance(h, dict):
                            h["db_file"] = os.path.basename(path)
                        all_hits.append(h)
        except Exception as e:
            log.warning("ext search %s: %s", path, e)
    if not all_hits:
        return None
    # format phones in hits
    all_hits = _format_phones_in_obj(all_hits)
    return {"matches": all_hits, "count": len(all_hits), "source": "external_db", "dbs": len(paths)}

def _search_external_db_one(value):

    """Search all tables in external DB for phone / tg id / name-ish value."""
    if not value:
        return None
    if not open_external_db():
        return None
    v = str(value).strip().lstrip("@")
    digits = "".join(c for c in v if c.isdigit())
    last10 = digits[-10:] if len(digits) >= 10 else digits
    out_hits = []
    with _ext_lock:
        tables = [r[0] for r in _ext_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        for table in tables[:40]:
            try:
                cols = _ext_table_cols(table)
                if not cols:
                    continue
                phone_cols = [c for c in cols if c in _PHONE_KEYS or "phone" in c or "mobile" in c or c == "number"]
                tg_cols = [c for c in cols if c in _TG_KEYS]
                name_cols = [c for c in cols if c in _NAME_KEYS or c.endswith("_name")]
                # build WHERE
                clauses = []
                params = []
                for c in phone_cols:
                    if last10:
                        clauses.append("[%s] LIKE ?" % c)
                        params.append("%%%s%%" % last10)
                    clauses.append("[%s] = ?" % c)
                    params.append(v)
                    if digits:
                        clauses.append("[%s] = ?" % c)
                        params.append(digits)
                if v.lstrip("-").isdigit():
                    for c in tg_cols:
                        clauses.append("[%s] = ?" % c)
                        params.append(int(v.lstrip("+") if v[:1] == "+" else v) if v.lstrip("+").isdigit() else v)
                if not clauses:
                    # fallback: search any text-like col
                    for c in cols[:12]:
                        clauses.append("CAST([%s] AS TEXT) LIKE ?" % c)
                        params.append("%%%s%%" % (last10 or v)[:20])
                if not clauses:
                    continue
                sql = "SELECT * FROM [%s] WHERE %s LIMIT 5" % (table.replace("]", ""), " OR ".join(clauses))
                rows = _ext_conn.execute(sql, params).fetchall()
                for row in rows:
                    rd = dict(row) if hasattr(row, "keys") else _row_to_dict(row, cols)
                    # normalize keys lower
                    rd_l = {str(k).lower(): rd[k] for k in rd.keys()}
                    hit = {
                        "source": "external_db",
                        "table": table,
                        "phone": _pick(rd_l, _PHONE_KEYS),
                        "name": _pick(rd_l, _NAME_KEYS),
                        "tg_id": _pick(rd_l, _TG_KEYS),
                        "address": _pick(rd_l, _ADDR_KEYS),
                        "father": _pick(rd_l, _FATHER_KEYS),
                    }
                    # keep extra useful fields
                    for k, val in list(rd_l.items())[:15]:
                        if k not in hit and val not in (None, ""):
                            hit[k] = val
                    out_hits.append(hit)
                    if len(out_hits) >= 8:
                        break
            except Exception:
                continue
            if len(out_hits) >= 8:
                break
    if not out_hits:
        return None
    if len(out_hits) == 1:
        return out_hits[0]
    return {"matches": out_hits, "count": len(out_hits), "source": "external_db"}

def import_external_to_contacts(limit=5000):
    """Optional: copy external phone rows into bot contacts table (owner tool)."""
    if not open_external_db():
        return 0
    added = 0
    with _ext_lock:
        tables = [r[0] for r in _ext_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        for table in tables[:20]:
            cols = _ext_table_cols(table)
            phone_cols = [c for c in cols if c in _PHONE_KEYS or "phone" in c or "mobile" in c]
            if not phone_cols:
                continue
            pc = phone_cols[0]
            try:
                rows = _ext_conn.execute("SELECT * FROM [%s] LIMIT %d" % (table.replace("]", ""), limit)).fetchall()
            except Exception:
                continue
            for row in rows:
                rd = dict(row)
                rd_l = {str(k).lower(): rd[k] for k in rd.keys()}
                phone = _pick(rd_l, _PHONE_KEYS)
                if not phone:
                    continue
                name = _pick(rd_l, _NAME_KEYS) or ""
                parts = str(name).split(None, 1)
                fn = parts[0] if parts else ""
                ln = parts[1] if len(parts) > 1 else ""
                tg = _pick(rd_l, _TG_KEYS)
                try:
                    tg_i = int(tg) if tg and str(tg).lstrip("-").isdigit() else 0
                except Exception:
                    tg_i = 0
                try:
                    db_save_contact(0, tg_i, str(phone), fn, ln)
                    added += 1
                except Exception:
                    pass
    return added

def _find_in_db(cmd, value):
    if not value:
        return None
    v = str(value).strip().lstrip("@")
    results = {}
    try:
        tid = int(v.lstrip("+"))
        r = db_find_phone_by_tg(tid)
        if r:
            results["internal_db"] = {
                "number": format_phone_display(r.get("phone")),
                "name": ("%s %s" % (r.get("first_name") or "", r.get("last_name") or "")).strip(),
                "tg_id": tid,
                "source": "internal_database",
            }
    except Exception:
        pass
    if "internal_db" not in results:
        r = db_find_by_phone(v)
        if r:
            results["internal_db"] = {
                "phone": format_phone_display(r.get("phone")),
                "name": ("%s %s" % (r.get("first_name") or "", r.get("last_name") or "")).strip(),
                "tg_id": r.get("tg_user_id"),
                "source": "internal_database",
            }
    try:
        ext = _search_external_db(v)
        if ext:
            results["external_db"] = ext
    except Exception:
        pass
    if not results:
        return None
    if len(results) == 1:
        return list(results.values())[0]
    return results

# ============================================================
#  OSINT ENGINE
# ============================================================
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36", "Accept": "application/json, text/plain, */*"}
# Faster lookups — fail slow sources sooner, don't block UI
TIMEOUT = aiohttp.ClientTimeout(total=14, connect=5)

def _fmt_url(template: str, value: str) -> str:
    """Safe URL template fill for {value}/{number} without KeyError on other braces."""
    qv = quote(str(value))
    try:
        return template.format(value=qv, number=qv)
    except Exception:
        return (template
                .replace("{value}", qv)
                .replace("{number}", qv)
                .replace("{query}", qv)
                .replace("{num}", qv))

# Keywords / status that mean API key expired or dead — remove from DB
_API_EXPIRE_STATUSES = {401, 403, 410, 418, 429}
_API_EXPIRE_KW = (
    "api key expired", "apikey expired", "key expired", "token expired",
    "invalid api key", "invalid key", "api key invalid", "unauthorized",
    "authentication failed", "access denied", "quota exceeded",
    "subscription expired", "plan expired", "api expired", "expired key",
    "invalid token", "token invalid", "forbidden", "rate limit exceeded",
)

def _looks_expired(status, text_or_data) -> bool:
    if status in _API_EXPIRE_STATUSES:
        return True
    s = ""
    if isinstance(text_or_data, str):
        s = text_or_data.lower()
    elif isinstance(text_or_data, dict):
        try:
            s = json.dumps(text_or_data).lower()
        except Exception:
            s = str(text_or_data).lower()
    else:
        s = str(text_or_data or "").lower()
    return any(k in s for k in _API_EXPIRE_KW)

def _url_base_match(full_url: str, template: str) -> bool:
    """Match live request URL back to stored template (ignore query value)."""
    try:
        a = full_url.split("?")[0].rstrip("/")
        b = template.split("?")[0].rstrip("/")
        # templates often contain {value}
        b = b.replace("{value}", "").rstrip("/")
        return a.startswith(b) or b in a or a in b
    except Exception:
        return full_url in template or template in full_url

def db_prune_expired_url(dead_url: str) -> list:
    """Remove a dead/expired URL from every custom_api that contains it.
    If a cmd has no URLs left, delete the whole cmd. Returns list of affected cmds."""
    affected = []
    with _lock:
        rows = [dict(r) for r in _conn.execute("SELECT * FROM custom_apis").fetchall()]
        for row in rows:
            cmd = row["cmd"]
            try:
                urls = json.loads(row["urls"] or "[]")
            except Exception:
                urls = []
            if not urls:
                continue
            new_urls = [u for u in urls if not _url_base_match(dead_url, u)]
            if len(new_urls) == len(urls):
                continue
            if not new_urls:
                _conn.execute("DELETE FROM custom_apis WHERE cmd=?", (cmd,))
                affected.append(f"/{cmd} (removed — no URLs left)")
                log.warning("API expired → removed cmd /%s (no URLs left)", cmd)
            else:
                _conn.execute("UPDATE custom_apis SET urls=? WHERE cmd=?",
                              (json.dumps(new_urls), cmd))
                affected.append(f"/{cmd} (1 URL pruned)")
                log.warning("API expired → pruned URL from /%s", cmd)
        if affected:
            _conn.commit()
    return affected

async def _get_json(s, url):
    try:
        async with s.get(url, timeout=TIMEOUT, allow_redirects=True, ssl=False) as r:
            t = await r.text()
            try:
                data = json.loads(t)
            except Exception:
                data = t[:1500]
            if _looks_expired(r.status, data if not isinstance(data, str) else t):
                return {"_url": url, "_status": r.status, "_expired": True, "data": data}
            return {"_url": url, "_status": r.status, "data": data}
    except Exception as e:
        return {"_url": url, "_error": str(e)}

def _meaningful(r):
    if not isinstance(r, dict) or "_error" in r or r.get("_expired"):
        return False
    d = r.get("data")
    if d is None: return False
    if isinstance(d, str):
        s = d.strip().lower()
        if not s: return False
        bad = ["not found","no data","invalid","error","false","null","empty","no record","not exist"]
        if any(b in s for b in bad) and len(s) < 200: return False
        return True
    if isinstance(d, dict): return bool(d)
    if isinstance(d, list): return len(d) > 0
    return True

async def fetch_all(urls):
    if not urls:
        return []
    connector = aiohttp.TCPConnector(ssl=False, limit=30, ttl_dns_cache=120)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as s:
        rs = await asyncio.gather(*[_get_json(s, u) for u in urls], return_exceptions=True)
    # Auto-prune expired APIs from DB
    for r in rs:
        if isinstance(r, dict) and r.get("_expired"):
            try:
                db_prune_expired_url(r.get("_url") or "")
            except Exception as e:
                log.warning("prune expired: %s", e)
    return [r for r in rs if isinstance(r, dict) and _meaningful(r)]

def merge_results(rs):
    if not rs: return None
    if len(rs) == 1: return rs[0].get("data")
    out = {}
    for r in rs:
        u = r.get("_url","?"); src = u.split("/")[2] if "//" in u else u
        out[src] = r.get("data")
    return out

async def check_all_apis():
    """Quick status per cmd (first URL only) — kept for panels."""
    tests = []
    for r in db_list_custom_apis():
        try:
            urls = json.loads(r["urls"] or "[]")
        except Exception:
            urls = []
        tests.append((r["cmd"], urls))
    # also include builtin num/tg extras
    for cmd in ("num", "tg", "family"):
        title, usage, urls = resolve_api(cmd)
        if urls and not any(t[0] == cmd for t in tests):
            tests.append((cmd, urls))
    res = {}
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as s:
        for name, urls in tests:
            if not urls:
                continue
            url = _fmt_url(urls[0], "test")
            t0 = time.time()
            try:
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=8, connect=4)) as r:
                    body = await r.text()
                    ok = 200 <= r.status < 400 and not _looks_expired(r.status, body)
                    ms = int((time.time() - t0) * 1000)
                    res[name] = (ok, r.status, ms)
                    db_save_api(name, ok, r.status, ms)
                    if _looks_expired(r.status, body):
                        db_prune_expired_url(url)
            except Exception:
                ms = int((time.time() - t0) * 1000)
                res[name] = (False, 0, ms)
                db_save_api(name, False, 0, ms)
    return res

async def probe_url(session, url_template, test_value="9876543210"):
    """Probe one URL template. Returns dict with ok/status/ms/expired/error."""
    url = _fmt_url(url_template, test_value)
    t0 = time.time()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8, connect=4),
                               allow_redirects=True, ssl=False) as r:
            body = await r.text()
            ms = int((time.time() - t0) * 1000)
            expired = _looks_expired(r.status, body)
            ok = 200 <= r.status < 400 and not expired
            return {"ok": ok, "status": r.status, "ms": ms, "expired": expired,
                    "url": url_template, "error": None}
    except Exception as e:
        ms = int((time.time() - t0) * 1000)
        return {"ok": False, "status": 0, "ms": ms, "expired": False,
                "url": url_template, "error": str(e)[:80]}

async def live_status_scan():
    """
    Real-time test of every known API source (custom + builtin injects).
    Returns: {cmd: [probe_dict, ...]}
    """
    # collect unique cmd -> urls
    cmd_urls = {}
    for r in db_list_custom_apis():
        cmd = r["cmd"]
        try:
            urls = json.loads(r["urls"] or "[]")
        except Exception:
            urls = []
        cmd_urls[cmd] = list(urls)
    for cmd in ("num", "tg", "family", "adhr", "pan", "upi", "vech", "name", "ip"):
        title, usage, urls = resolve_api(cmd)
        if not urls:
            continue
        existing = cmd_urls.get(cmd) or []
        for u in urls:
            if u not in existing:
                existing.append(u)
        cmd_urls[cmd] = existing

    out = {}
    connector = aiohttp.TCPConnector(ssl=False, limit=25, ttl_dns_cache=120)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as s:
        for cmd, urls in cmd_urls.items():
            if not urls:
                continue
            probes = await asyncio.gather(*[probe_url(s, u) for u in urls],
                                          return_exceptions=True)
            results = []
            for p in probes:
                if isinstance(p, dict):
                    results.append(p)
                else:
                    results.append({"ok": False, "status": 0, "ms": 0, "expired": False,
                                    "url": "?", "error": str(p)[:80]})
            out[cmd] = results
            # persist aggregate
            any_ok = any(p["ok"] for p in results)
            avg_ms = int(sum(p["ms"] for p in results) / max(len(results), 1))
            st = results[0]["status"] if results else 0
            db_save_api(cmd, any_ok, st, avg_ms)
    return out

async def kill_dead_apis():
    """
    Scan all APIs, remove dead/expired URLs from custom_apis.
    Delete cmds with zero URLs left. Returns summary strings.
    """
    scan = await live_status_scan()
    killed_urls = 0
    killed_cmds = []
    dead_list = []
    for cmd, probes in scan.items():
        dead = [p for p in probes if (not p["ok"]) or p.get("expired")]
        alive_urls = [p["url"] for p in probes if p["ok"] and not p.get("expired")]
        for p in dead:
            dead_list.append(f"/{cmd} · {_mask_url(p['url'])} · "
                             f"{'EXPIRED' if p.get('expired') else 'DEAD'} "
                             f"({p.get('status') or p.get('error') or '?'})")
        row = db_get_custom_api(cmd)
        if not row:
            continue  # builtin-only injects — cannot delete pack
        try:
            current = json.loads(row["urls"] or "[]")
        except Exception:
            current = []
        if not current:
            continue
        # keep only URLs still alive
        new_urls = [u for u in current if u in alive_urls]
        removed_n = len(current) - len(new_urls)
        if removed_n <= 0:
            continue
        killed_urls += removed_n
        if not new_urls:
            db_remove_custom_api(cmd)
            killed_cmds.append(cmd)
        else:
            db_update_custom_urls(cmd, new_urls)
    return killed_urls, killed_cmds, dead_list

# ============================================================
#  FIELD EXTRACTION
# ============================================================
FIELD_ALIASES = {
    "name":    ["name","full_name","fullname","owner_name","owner","first_name","fname"],
    "number":  ["number","phone","mobile","num","phone_number","telephone","whatsapp"],
    "father":  ["father","father_name","fathername","guardian","fathers_name"],
    "mother":  ["mother","mother_name","mothername","mothers_name"],
    "address": ["address","addr","full_address","permanent_address","residence"],
    "circle":  ["circle","state","region","zone"],
    "alt":     ["alt","alternate","alt_number","alternate_number","alt_mobile"],
    "email":   ["email","mail","email_id"],
    "id":      ["id","userid","user_id","telegram_id","tg_id","chat_id"],
    "username":["username","user","handle","tg_username","telegram_username"],
    "aadhaar": ["aadhaar","aadhar","uid","aadhaar_number","aadhar_number"],
    "pan":     ["pan","pan_no","panno","pan_number"],
    "vehicle": ["vehicle","reg_no","registration","registration_number","vehicle_number"],
}
FIELD_LABELS = {
    "name": "Nᴀᴍᴇ", "username": "Uꜱᴇʀɴᴀᴍᴇ", "id": "Uꜱᴇʀ Iᴅ", "number": "Nᴜᴍʙᴇʀ",
    "father": "Fᴀᴛʜᴇʀ", "mother": "Mᴏᴛʜᴇʀ", "address": "Aᴅᴅʀᴇꜱꜱ", "circle": "Cɪʀᴄʟᴇ",
    "alt": "Aʟᴛ Nᴜᴍ", "email": "Eᴍᴀɪʟ", "aadhaar": "Aᴀᴅʜᴀᴀʀ", "pan": "Pᴀɴ",
    "vehicle": "Vᴇʜɪᴄʟᴇ",
}
FIELD_ORDER = ["name","username","id","number","father","mother","address",
               "circle","alt","email","aadhaar","pan","vehicle"]

def _flatten(d, out=None):
    if out is None: out = {}
    if isinstance(d, dict):
        for k,v in d.items():
            if isinstance(v,(dict,list)): _flatten(v, out)
            else:
                kk = str(k).lower().strip()
                if kk not in out and v not in (None,"","null","None"): out[kk]=v
    elif isinstance(d, list):
        for it in d:
            if isinstance(it,(dict,list)): _flatten(it, out)
    return out

def extract_fields(data):
    flat = _flatten(data)
    found = {}
    for canonical, keys in FIELD_ALIASES.items():
        for k in keys:
            if k in flat and flat[k] not in (None,"","null","None"):
                found[canonical] = flat[k]; break
    return found

def format_fields(data, max_len=100, max_rows=20):
    fields = extract_fields(data)
    flat = _flatten(data)
    lines = []
    for key in FIELD_ORDER:
        if key in fields:
            v = fields[key]
            if isinstance(v, (dict, list)): continue
            v = str(v)
            if len(v) > max_len: v = v[:max_len] + "…"
            lines.append(f"▸ <b>{FIELD_LABELS[key]}</b> : <code>{v}</code>")
    if not lines:
        for k, v in list(flat.items())[:max_rows]:
            if isinstance(v, (dict, list)): continue
            v = str(v)
            if len(v) > max_len: v = v[:max_len] + "…"
            lines.append(f"▸ <b>{k}</b> : <code>{v}</code>")
    return "\n".join(lines)

# ============================================================
#  UI HELPERS
# ============================================================
def B(text, cb=None, url=None, style=None):
    """Build inline button with color style (Bot API 9.4+: primary/success/danger)."""
    kw = {"text": text}
    if cb is not None:  kw["callback_data"] = cb
    if url is not None: kw["url"] = url
    if style is not None:
        kw["style"] = style
        # fallback for older PTB libs that don't have style arg yet
        try:
            return InlineKeyboardButton(**kw)
        except TypeError:
            kw.pop("style", None)
            btn = InlineKeyboardButton(**kw)
            # inject via api_kwargs / private
            if hasattr(btn, "_api_kwargs"):
                btn._api_kwargs = getattr(btn, "_api_kwargs", {}) or {}
                btn._api_kwargs["style"] = style
            else:
                try:
                    btn = InlineKeyboardButton(text=text, callback_data=cb, url=url, api_kwargs={"style": style})
                except TypeError:
                    pass
            return btn
    return InlineKeyboardButton(**kw)

def KB(text, style=None, **extra):
    """Build reply KeyboardButton with color style."""
    kw = {"text": text, **extra}
    if style is not None:
        kw["style"] = style
        try:
            return KeyboardButton(**kw)
        except TypeError:
            kw.pop("style", None)
            try:
                return KeyboardButton(text=text, api_kwargs={"style": style}, **extra)
            except TypeError:
                return KeyboardButton(**kw)
    return KeyboardButton(**kw)

def q(text):  return f"<blockquote>{text}</blockquote>"
def qx(text): return f"<blockquote expandable>{text}</blockquote>"
def qblocks(*sections):
    # Title Small-Caps on visible text (first letter regular CAP, rest small-caps)
    parts = [q(style_sc_html(s)) for s in sections if s and s.strip()]
    return pe_text("\n".join(parts))

def is_owner(uid): return uid == OWNER_ID

# ---------- Owner / protected identity shield ----------
def _norm_phone_digits(v):
    d = "".join(c for c in str(v or "") if c.isdigit())
    return d[-10:] if len(d) >= 10 else d

def _protect_list(key):
    raw = db_get(key, "[]") or "[]"
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return []

def _protect_save(key, items):
    uniq = []
    for x in items:
        s = str(x).strip()
        if s and s not in uniq:
            uniq.append(s)
    db_set(key, json.dumps(uniq))
    return uniq

def protect_add_phone(phone):
    d = _norm_phone_digits(phone)
    if not d:
        return False
    items = _protect_list("protect_phones")
    if d not in items:
        items.append(d)
        _protect_save("protect_phones", items)
    return True

def protect_add_tg(tg_id):
    try:
        tid = str(int(str(tg_id).lstrip("+")))
    except Exception:
        return False
    items = _protect_list("protect_tg")
    if tid not in items:
        items.append(tid)
        _protect_save("protect_tg", items)
    return True

def protect_remove_phone(phone):
    d = _norm_phone_digits(phone)
    items = [x for x in _protect_list("protect_phones") if x != d]
    _protect_save("protect_phones", items)
    return True

def protect_remove_tg(tg_id):
    try:
        tid = str(int(str(tg_id).lstrip("+")))
    except Exception:
        return False
    items = [x for x in _protect_list("protect_tg") if x != tid]
    _protect_save("protect_tg", items)
    return True

def ensure_owner_protected():
    """Always shield OWNER_ID; phones come from contacts / manual protect."""
    if OWNER_ID:
        protect_add_tg(OWNER_ID)

def is_protected_query(value, requester_id=None):
    """True if value matches protected phone/tg and requester is not owner."""
    if requester_id is not None and is_owner(requester_id):
        return False
    ensure_owner_protected()
    v = str(value or "").strip().lstrip("@")
    digits = _norm_phone_digits(v)
    phones = set(_protect_list("protect_phones"))
    tgs = set(_protect_list("protect_tg"))
    if digits and digits in phones:
        return True
    # full digit variants
    raw_d = "".join(c for c in v if c.isdigit())
    if raw_d:
        if raw_d in phones or (len(raw_d) >= 10 and raw_d[-10:] in phones):
            return True
        if raw_d in tgs:
            return True
    try:
        if str(int(v.lstrip("+"))) in tgs:
            return True
    except Exception:
        pass
    # username match for owner? skip — only numeric/tg id + phones
    return False

def _scrub_protected_data(data):
    """Remove fields that expose protected phones from API payload (non-owner)."""
    phones = set(_protect_list("protect_phones"))
    if not phones or data is None:
        return data
    def hit(val):
        d = _norm_phone_digits(val)
        return bool(d and d in phones)
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                out[k] = _scrub_protected_data(v)
            elif hit(v):
                continue
            else:
                out[k] = v
        return out
    if isinstance(data, list):
        return [_scrub_protected_data(x) for x in data]
    return data


def format_phone_display(raw):
    """Format phone with country code. IN: +91 xxxxx xxxxx | US: +1 xxx xxx xxxx"""
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s or s.lower() in ("none", "null", "n/a", "-"):
        return s
    digits = re.sub(r"\D", "", s)
    if not digits:
        return s
    # India 10-digit mobile
    if len(digits) == 10 and digits[0] in "6789":
        return f"+91 {digits[:5]} {digits[5:]}"
    # India with 91
    if digits.startswith("91") and len(digits) == 12 and digits[2] in "6789":
        return f"+91 {digits[2:7]} {digits[7:]}"
    # India with 0
    if digits.startswith("0") and len(digits) == 11 and digits[1] in "6789":
        return f"+91 {digits[1:6]} {digits[6:]}"
    # US/Canada +1
    if digits.startswith("1") and len(digits) == 11:
        return f"+1 {digits[1:4]} {digits[4:7]} {digits[7:]}"
    # UK +44
    if digits.startswith("44") and len(digits) >= 11:
        rest = digits[2:]
        if len(rest) == 10:
            return f"+44 {rest[:4]} {rest[4:]}"
        return f"+44 {rest}"
    # UAE +971
    if digits.startswith("971") and len(digits) >= 11:
        rest = digits[3:]
        return f"+971 {rest[:2]} {rest[2:]}" if len(rest) > 2 else f"+971 {rest}"
    # Generic: country code + national (last 10)
    if len(digits) > 10:
        cc, nat = digits[:-10], digits[-10:]
        if cc == "91":
            return f"+91 {nat[:5]} {nat[5:]}"
        if cc == "1":
            return f"+1 {nat[:3]} {nat[3:6]} {nat[6:]}"
        return f"+{cc} {nat}"
    if len(digits) > 7:
        return f"+{digits}"
    return s

def _format_phones_in_obj(obj):
    """Recursively format phone-like fields in dict/list for display."""
    phone_keys = {
        "number", "phone", "mobile", "num", "phone_number", "phonenumber",
        "telephone", "whatsapp", "msisdn", "contact", "alt", "mobile_number",
    }
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower().replace(" ", "_")
            if kl in phone_keys and v is not None and not isinstance(v, (dict, list)):
                out[k] = format_phone_display(v)
            else:
                out[k] = _format_phones_in_obj(v)
        return out
    if isinstance(obj, list):
        return [_format_phones_in_obj(x) for x in obj]
    return obj

def is_admin(uid):
    if is_owner(uid): return True
    u = db_get_user(uid); return bool(u and u["is_admin"])
def is_dm(u): return u.effective_chat.type == ChatType.PRIVATE
def is_gc(u): return u.effective_chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
def is_verified(uid):
    u = db_get_user(uid); return bool(u and u["verified"])

def user_is_premium(uid_or_row):
    """True if user has VIP. Accepts user_id or user dict/row."""
    if uid_or_row is None:
        return False
    if isinstance(uid_or_row, dict) or hasattr(uid_or_row, "keys"):
        try:
            return int(uid_or_row["is_premium"] or 0) == 1
        except Exception:
            return False
    u = db_get_user(int(uid_or_row))
    return bool(u and int(u["is_premium"] or 0) == 1)


def _hidden_dev_user():
    """Sealed developer username (not shown as plain text)."""
    try:
        return str(_V).strip().lstrip("@") if _V else ""
    except Exception:
        return ""

def _dev_name_html():
    """Developer name as clickable link to hidden username profile."""
    hid = _hidden_dev_user()
    name = DEVELOPER_NAME or "Developer"
    if hid:
        # Visible: name only | Hidden: t.me link to developer username
        return f'<a href="https://t.me/{hid}">{name}</a>'
    return name

def dev_link():
    bot_u = f"<code>@{BOT_USERNAME}</code>" if BOT_USERNAME else "N/A"
    return f"{_dev_name_html()}\n🤖 <b>Bᴏᴛ</b> — {bot_u}"

def dev_signature_txt():
    bot_u = f"<code>@{BOT_USERNAME}</code>" if BOT_USERNAME else "N/A"
    return f"👨‍💻 <b>Dᴇᴠᴇʟᴏᴘᴇʀ</b> — {_dev_name_html()}\n🤖 <b>Bᴏᴛ</b> — {bot_u}"

# ============================================================
#  HISTORY FILE
# ============================================================
def build_history_file(rows, target_uid=None):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    user = db_get_user(target_uid) if target_uid else None
    bot_u = f"@{BOT_USERNAME}" if BOT_USERNAME else "N/A"
    lines = []
    lines.append("=" * 45)
    lines.append("  KITTU LOOKUP — HISTORY")
    lines.append("=" * 45)
    if user:
        lines.append(f"User ID     : {user['user_id']}")
        uname = f"@{user['username']}" if user['username'] else "-"
        lines.append(f"Username    : {uname}")
        lines.append(f"Name        : {user['first_name'] or '-'}")
    else:
        lines.append("Scope       : Global (All Users)")
    lines.append(f"Generated   : {ts} UTC")
    lines.append(f"Total Logs  : {len(rows)}")
    lines.append("=" * 45)
    lines.append("")
    for idx, r in enumerate(rows, 1):
        status = "SUCCESS" if r["success"] else "FAILED"
        lines.append(f"#{idx} | {r['created_at']}")
        lines.append(f"  Command : /{r['command']}")
        lines.append(f"  Input   : {r['input']}")
        lines.append(f"  Sources : {r['sources']}")
        lines.append(f"  Status  : {status}")
        lines.append("")
    lines.append("=" * 45)
    lines.append(f"Bot        : {bot_u}")
    lines.append(f"Developer  : {DEVELOPER_NAME}")
    lines.append("=" * 45)
    with open(HISTORY_FILENAME, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return HISTORY_FILENAME

# ============================================================
#  KEYBOARDS  — ALL BOTTOM + COLORED (style primary/success/danger)
#  Bot API 9.4+  |  primary=blue  success=green  danger=red
# ============================================================

BTN_OSINT     = "🔎 Oꜱɪɴᴛ Lᴏᴏᴋᴜᴘ"
BTN_PROFILE   = "👑 Mʏ Pʀᴏꜰɪʟᴇ"
BTN_REFER     = "💎 Rᴇꜰᴇʀ Eᴀʀɴ"
BTN_HISTORY   = "🗂 Mʏ Hɪꜱᴛᴏʀʏ"
BTN_PREMIUM   = "⭐ Vɪᴘ"
BTN_HELP      = "📖 Hᴇʟᴘ"
BTN_ADMIN     = "🛡 Aᴅᴍɪɴ Pᴀɴᴇʟ"
BTN_OWNER     = "⚜️ Oᴡɴᴇʀ Pᴀɴᴇʟ"
BTN_BACK_HOME = "⬅ Bᴀᴄᴋ Hᴏᴍᴇ"

BTN_TG     = "✈️ Tɢ Lᴏᴏᴋᴜᴘ"
BTN_NUM    = "📱 Pʜᴏɴᴇ Nᴜᴍ"
BTN_ADHR   = "🆔 Aᴀᴅʜᴀᴀʀ"
BTN_FAM    = "👨‍👩‍👧 Fᴀᴍɪʟʏ"
BTN_VECH   = "🚗 Vᴇʜɪᴄʟᴇ"
BTN_RCRC   = "📄 Rᴄ Iɴꜰᴏ"
BTN_PAN    = "💳 Pᴀɴ"
BTN_UPI    = "💸 Uᴘɪ"
BTN_IFSC   = "🏦 Iꜰꜱᴄ"
BTN_NAME   = "📛 Nᴀᴍᴇ"
BTN_IP     = "🌐 Iᴘ"
BTN_PIN    = "📍 Pɪɴᴄᴏᴅᴇ"
BTN_GIT    = "🐙 Gɪᴛʜᴜʙ"
BTN_INSTA  = "📸 Iɴꜱᴛᴀɢʀᴀᴍ"
BTN_BGMI   = "🎮 Bɢᴍɪ"
BTN_FF     = "🔥 FʀᴇᴇFɪʀᴇ"
BTN_AI     = "✨ Aɪ Iᴍᴀɢᴇ"
BTN_DNS    = "🔎 Dɴꜱ"
BTN_WHOIS  = "📜 Wʜᴏɪꜱ"
BTN_BIN    = "💳 Bɪɴ"
BTN_USER   = "🕵️ Uꜱᴇʀɴᴀᴍᴇ"

BTN_A_STATS   = "📊 Sᴛᴀᴛꜱ"
BTN_A_HIST    = "📜 Hɪꜱᴛᴏʀʏ"
BTN_A_CREDADD = "💰 Cʀᴇᴅɪᴛ + Aᴅᴅ"
BTN_A_CREDRM  = "🗑 Cʀᴇᴅɪᴛ - Rᴇᴍᴏᴠᴇ"
BTN_A_PREMADD = "⭐ Vɪᴘ + Aᴅᴅ"
BTN_A_PREMRM  = "🗑 Vɪᴘ Rᴇᴍᴏᴠᴇ"
BTN_A_PREMLIST= "📋 Vɪᴘ Lɪꜱᴛ"
BTN_A_API     = "🔌 Aᴘɪ Sᴛᴀᴛᴜꜱ"

BTN_O_GSTATS  = "📊 Gʟᴏʙᴀʟ Sᴛᴀᴛꜱ"
BTN_O_GETDB   = "📥 Gᴇᴛ Dʙ"
BTN_O_EXTDB   = "🗄 Exᴛᴇʀɴᴀʟ Dʙ"
BTN_O_BCAST   = "📢 Bʀᴏᴀᴅᴄᴀꜱᴛ"
BTN_O_APIMGR  = "🔌 Aᴘɪ Mᴀɴᴀɢᴇʀ"
BTN_O_GHIST   = "📜 Gʟᴏʙᴀʟ Hɪꜱᴛᴏʀʏ"
BTN_O_CREDADD = "💰 Cʀᴇᴅɪᴛ + Aᴅᴅ"
BTN_O_CREDRM  = "🗑 Cʀᴇᴅɪᴛ - Rᴇᴍᴏᴠᴇ"
BTN_O_ADMADD  = "🛡 Aᴅᴍ + Aᴅᴅ"
BTN_O_ADMRM   = "🗑 Aᴅᴍ Rᴇᴍᴏᴠᴇ"
BTN_O_ADMLIST = "📋 Aᴅᴍ Lɪꜱᴛ"
BTN_O_PREMADD = "💎 Pʀᴇᴍ + Aᴅᴅ"
BTN_O_PREMRM  = "🗑 Pʀᴇᴍ Rᴇᴍᴏᴠᴇ"
BTN_O_PREMLIST= "📋 Pʀᴇᴍ Lɪꜱᴛ"
BTN_O_WLCTXT  = "✏ Sᴇᴛ Wʟᴄ Tᴇxᴛ"
BTN_O_WLCMED  = "🖼 Sᴇᴛ Mᴇᴅɪᴀ"
BTN_O_CHNL    = "📢 Cʜᴀɴɴᴇʟꜱ"
BTN_O_GC      = "👥 Gʀᴏᴜᴘꜱ"

def get_user_role(uid):
    """Return role tier: owner > admin > premium > free."""
    if is_owner(uid):
        return "owner"
    if is_admin(uid):
        return "admin"
    if user_is_premium(uid):
        return "premium"
    return "free"

def user_menu_kb(uid):
    """Role-based main bottom keyboard. Not persistent — phone back hides it; /start or any cmd brings it back."""
    role = get_user_role(uid)
    # FREE — clean minimal
    if role == "free":
        rows = [
            [KB(BTN_OSINT, style="primary")],
            [KB(BTN_PROFILE, style="success"), KB(BTN_REFER, style="success")],
            [KB(BTN_HISTORY, style="primary"), KB(BTN_HELP, style="primary")],
            [KB(BTN_PREMIUM, style="danger")],
        ]
    # PREMIUM — richer layout + spin hint via VIP styling
    elif role == "premium":
        rows = [
            [KB(BTN_OSINT, style="primary")],
            [KB(BTN_PROFILE, style="success"), KB(BTN_REFER, style="success")],
            [KB(BTN_HISTORY, style="primary"), KB("🎰 Sᴘɪɴ", style="success")],
            [KB(BTN_PREMIUM, style="danger"), KB(BTN_HELP, style="primary")],
        ]
    # ADMIN — tools row + full user set
    elif role == "admin":
        rows = [
            [KB(BTN_OSINT, style="primary")],
            [KB(BTN_PROFILE, style="success"), KB(BTN_REFER, style="success")],
            [KB(BTN_HISTORY, style="primary"), KB("🎰 Sᴘɪɴ", style="success")],
            [KB(BTN_PREMIUM, style="danger"), KB(BTN_HELP, style="primary")],
            [KB(BTN_ADMIN, style="danger")],
        ]
    # OWNER — maximum control, best layout
    else:
        rows = [
            [KB(BTN_OSINT, style="primary")],
            [KB(BTN_PROFILE, style="success"), KB(BTN_REFER, style="success")],
            [KB(BTN_HISTORY, style="primary"), KB("🎰 Sᴘɪɴ", style="success")],
            [KB(BTN_PREMIUM, style="danger"), KB(BTN_HELP, style="primary")],
            [KB(BTN_ADMIN, style="danger"), KB(BTN_OWNER, style="success")],
        ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=False)

def lookup_reply_kb():
    rows = [
        [KB(BTN_TG, style="primary"), KB(BTN_NUM, style="primary")],
        [KB(BTN_ADHR, style="primary"), KB(BTN_FAM, style="primary")],
        [KB(BTN_VECH, style="primary"), KB(BTN_RCRC, style="primary")],
        [KB(BTN_PAN, style="primary"), KB(BTN_UPI, style="primary")],
        [KB(BTN_IFSC, style="primary"), KB(BTN_NAME, style="primary")],
        [KB(BTN_IP, style="primary"), KB(BTN_PIN, style="primary")],
        [KB(BTN_GIT, style="primary"), KB(BTN_INSTA, style="primary")],
        [KB(BTN_BGMI, style="success"), KB(BTN_FF, style="success")],
        [KB(BTN_DNS, style="primary"), KB(BTN_WHOIS, style="primary")],
        [KB(BTN_BIN, style="primary"), KB(BTN_USER, style="primary")],
        [KB(BTN_AI, style="success")],
        [KB(BTN_BACK_HOME, style="danger")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=False)

def admin_reply_kb(uid=None):
    rows = [
        [KB(BTN_A_STATS, style="primary"), KB(BTN_A_HIST, style="primary")],
        [KB(BTN_A_CREDADD, style="success"), KB(BTN_A_CREDRM, style="danger")],
        [KB(BTN_A_PREMADD, style="success"), KB(BTN_A_PREMRM, style="danger")],
        [KB(BTN_A_PREMLIST, style="primary")],
        [KB(BTN_A_API, style="primary")],
    ]
    if uid and is_owner(uid):
        rows.append([KB(BTN_OWNER, style="success")])
    rows.append([KB(BTN_BACK_HOME, style="danger")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=False)

def owner_reply_kb():
    rows = [
        [KB(BTN_O_GSTATS, style="primary"), KB(BTN_O_GETDB, style="primary")],
        [KB(BTN_O_EXTDB, style="success")],
        [KB(BTN_O_BCAST, style="success"), KB(BTN_O_APIMGR, style="primary")],
        [KB(BTN_O_GHIST, style="primary")],
        [KB(BTN_O_CREDADD, style="success"), KB(BTN_O_CREDRM, style="danger")],
        [KB(BTN_O_ADMADD, style="success"), KB(BTN_O_ADMRM, style="danger")],
        [KB(BTN_O_ADMLIST, style="primary")],
        [KB(BTN_O_PREMADD, style="success"), KB(BTN_O_PREMRM, style="danger")],
        [KB(BTN_O_PREMLIST, style="primary")],
        [KB(BTN_O_WLCTXT, style="primary"), KB(BTN_O_WLCMED, style="primary")],
        [KB(BTN_O_CHNL, style="primary"), KB(BTN_O_GC, style="primary")],
        [KB(BTN_ADMIN, style="danger")],
        [KB(BTN_BACK_HOME, style="danger")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=False)

def lookup_menu_kb():
    return lookup_reply_kb()

def admin_panel_kb(uid=None):
    return admin_reply_kb(uid)

def owner_panel_kb():
    return owner_reply_kb()

def channel_panel_kb():
    return InlineKeyboardMarkup([
        [B("➕ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ", cb="o:chnl_add", style="success")],
        [B("🗑 ʀᴇᴍᴏᴠᴇ", cb="o:chnl_rm", style="danger"), B("📋 ʟɪꜱᴛ", cb="o:chnl_list", style="primary")],
        [B("⬅ ʙᴀᴄᴋ", cb="menu:owner", style="danger")]])

def gc_panel_kb():
    return InlineKeyboardMarkup([
        [B("➕ ᴀᴅᴅ ɢᴄ", cb="o:gc_add", style="success")],
        [B("🗑 ʀᴇᴍᴏᴠᴇ", cb="o:gc_rm", style="danger"), B("📋 ʟɪꜱᴛ", cb="o:gc_list", style="primary")],
        [B("⬅ ʙᴀᴄᴋ", cb="menu:owner", style="danger")]])

def api_panel_kb():
    return InlineKeyboardMarkup([
        [B("➕ ᴀᴅᴅ ᴀᴘɪ", cb="o:api_add", style="success"), B("🗑 ᴅᴇʟ ᴀᴘɪ", cb="o:api_del", style="danger")],
        [B("📋 ᴄᴜꜱᴛᴏᴍ ʟɪꜱᴛ", cb="o:api_list", style="primary"), B("🔌 ꜱᴛᴀᴛᴜꜱ ᴄʜᴇᴄᴋ", cb="o:api_check", style="primary")],
        [B("📄 ᴛᴇᴍᴘʟᴀᴛᴇ", cb="o:api_tpl", style="primary")],
        [B("⬅ ʙᴀᴄᴋ", cb="menu:owner", style="danger")]])

def verify_kb():
    return ReplyKeyboardMarkup(
        [[KB("📱 ᴠᴇʀɪꜰʏ ᴍᴇ", style="success", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True)

# ============================================================
#  ANIMATIONS
# ============================================================
async def animate_init(msg, delay=0.12):
    """Fast boot loading bar (shown on every /start)."""
    steps = 4
    for i in range(steps + 1):
        filled = int((i / steps) * BAR_TOTAL)
        pct = int((i / steps) * 100)
        text = qblocks(
            f"<b>⚡ ɪɴɪᴛɪᴀʟɪᴢɪɴɢ…</b>\n{LINE}",
            f"<code>{progress_bar(filled)}  {pct:3d}%  {progress_emoji(pct)}</code>")
        try:
            await msg.edit_text(text, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        if i < steps:
            await asyncio.sleep(delay)

async def animate_faith(msg, title, value, sources, done_event, delay=0.12):
    """Lightweight progress while APIs fetch — exits early when data is ready."""
    steps = 6
    safe_title = esc(title)
    safe_val = esc(value)
    def _frame(i):
        filled = int((i / steps) * BAR_TOTAL)
        pct = int((i / steps) * 100)
        return qblocks(
            f"<b>{safe_title}</b>\n{LINE}",
            f"🎯 <b>ᴛᴀʀɢᴇᴛ</b> : <code>{safe_val}</code>\n"
            f"📡 <b>ꜱᴏᴜʀᴄᴇꜱ</b> : {sources}\n{LINE}",
            f"⚡ <b>ꜰᴀɪᴛʜɪɴɢ ᴅᴀᴛᴀ…</b>\n"
            f"<code>{progress_bar(filled)}  {pct:3d}%  {progress_emoji(pct)}</code>")
    for i in range(steps + 1):
        try:
            await msg.edit_text(_frame(i), parse_mode=ParseMode.HTML)
        except Exception:
            pass
        if i == steps:
            break
        if done_event.is_set():
            # jump to 100% once, then stop
            try:
                await msg.edit_text(_frame(steps), parse_mode=ParseMode.HTML)
            except Exception:
                pass
            break
        await asyncio.sleep(delay)

# ============================================================
#  FORCE JOIN
# ============================================================

async def seed_force_joins(bot):
    """Resolve & upsert default force-join channels + main GC."""
    added = 0
    for item in FORCE_JOIN_CHATS:
        try:
            chat = None
            if item.get("chat_id"):
                try:
                    chat = await bot.get_chat(int(item["chat_id"]))
                except Exception as e:
                    log.warning("FJ seed chat_id %s: %s", item.get("chat_id"), e)
                    # still store id so checks run
                    cid = int(item["chat_id"])
                    db_add_channel(cid, None, None, item.get("title") or "Main GC", 1)
                    if cid == MAIN_GC_ID or cid < 0:
                        db_add_group(cid, item.get("title") or "Main GC")
                    added += 1
                    continue
            elif item.get("username"):
                un = item["username"].lstrip("@")
                chat = await bot.get_chat("@" + un)
            if not chat:
                continue
            priv = 0 if getattr(chat, "username", None) else 1
            invite = None
            if getattr(chat, "username", None):
                invite = f"https://t.me/{chat.username}"
            else:
                try:
                    inv = await bot.create_chat_invite_link(
                        chat.id, name="Kittu FJ", creates_join_request=True)
                    invite = inv.invite_link
                except Exception:
                    try:
                        invite = await bot.export_chat_invite_link(chat.id)
                    except Exception:
                        invite = None
            db_add_channel(
                chat.id,
                getattr(chat, "username", None),
                invite,
                chat.title or item.get("title") or "Channel",
                priv,
            )
            # Main GC also whitelist for free group use
            if chat.id == MAIN_GC_ID or item.get("chat_id") == MAIN_GC_ID:
                db_add_group(chat.id, chat.title or "Main GC")
            added += 1
            log.info("FJ seeded: %s (%s)", chat.title, chat.id)
        except Exception as e:
            log.warning("FJ seed fail %s: %s", item, e)
    return added

async def check_fj(bot, uid):
    chs = db_list_channels()
    if not chs:
        return True
    for ch in chs:
        cid = ch["chat_id"]
        if db_has_join_req(uid, cid):
            continue
        try:
            m = await bot.get_chat_member(cid, uid)
            st = getattr(m, "status", None)
            # ChatMemberStatus enums may be objects
            st_s = str(st).lower()
            if st_s in ("member", "administrator", "creator",
                        "chatmemberstatus.member", "chatmemberstatus.administrator",
                        "chatmemberstatus.creator") or st in ("member", "administrator", "creator"):
                continue
            # restricted but is_member True
            if getattr(m, "is_member", None) is True:
                continue
        except Exception:
            return False
        return False
    return True

def fj_kb():
    rows = []
    for ch in db_list_channels():
        link = None
        if ch.get("invite_link"):
            link = ch["invite_link"]
        elif ch.get("username"):
            link = f"https://t.me/{ch['username'].lstrip('@')}"
        title = (ch.get("title") or ch.get("username") or str(ch.get("chat_id")))[:32]
        # strip leading emoji/symbols if any stored in title
        title = re.sub(r"^[\W_]+", "", title).strip() or title
        if link:
            rows.append([B(title, url=link, style="primary")])
        else:
            rows.append([B(f"{title} (ask admin)", cb="fj:check", style="primary")])
    if not rows:
        rows.append([B("No channels configured", cb="fj:check", style="danger")])
    rows.append([B("I Have Joined", cb="fj:check", style="success")])
    return InlineKeyboardMarkup(rows)

async def send_fj(chat, ctx):
    if chat is None:
        return
    chs = db_list_channels()
    body = (
        "Bot use karne se pehle ye channels / GC join karo.\n"
        "Private me join-request bhejo — bot detect kar lega.\n"
        f"{LINE}\n"
        f"Total required: <b>{len(chs)}</b>"
    )
    txt = qblocks(f"<b>ᴊᴏɪɴ ʀᴇQᴜɪʀᴇᴅ</b>\n{LINE}", body)
    kb = fj_kb()
    try:
        if hasattr(chat, "reply_text"):
            await chat.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
        else:
            await chat.send_message(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("send_fj fail: %s", e)
        try:
            await ctx.bot.send_message(chat.id if hasattr(chat, "id") else chat.chat.id,
                txt, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e2:
            log.warning("send_fj fallback: %s", e2)

# ============================================================
#  REGISTER
# ============================================================
async def register(update):
    u = update.effective_user
    existing = db_get_user(u.id)
    if not existing:
        if not is_dm(update):
            return None
        ref_id = None
        if update.message and update.message.text and update.message.text.startswith("/start"):
            parts = update.message.text.split()
            if len(parts) > 1 and parts[1].startswith("ref_"):
                try: ref_id = int(parts[1][4:])
                except: ref_id = None
                if ref_id == u.id: ref_id = None
        db_create_user(u.id, u.username, u.first_name, referrer_id=ref_id)
    else:
        db_update_activity(u.id, u.username, u.first_name)
    return db_get_user(u.id)

# ============================================================
#  CARDS
# ============================================================
def build_main_card(uid):
    u = db_get_user(uid)
    if not u: return "", None
    role_key = get_user_role(uid)
    if role_key == "owner":
        header = f"<b>👑 {BOT_NAME}</b>\n<i>ᴏᴡɴᴇʀ ᴄᴏɴᴛʀᴏʟ ᴄᴇɴᴛᴇʀ</i>\n{LINE}"
        role_line = f"{pe('👑')} <b>Oᴡɴᴇʀ</b> · full access"
        tip = "⚡ Owner panel se sab manage karo"
    elif role_key == "admin":
        header = f"<b>🛡 {BOT_NAME}</b>\n<i>ᴀᴅᴍɪɴ ᴄᴏɴꜱᴏʟᴇ</i>\n{LINE}"
        role_line = f"{pe('🛡')} <b>Aᴅᴍɪɴ</b> · elevated"
        tip = "🛡 Admin panel available below"
    elif role_key == "premium":
        header = f"<b>💎 {BOT_NAME}</b>\n<i>ᴠɪᴘ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ</i>\n{LINE}"
        role_line = f"{pe('💎')} <b>Vɪᴘ</b> · unlocked"
        tip = "✨ VIP perks active · spin unlocked"
    else:
        header = f"<b>✨ {BOT_NAME}</b>\n<i>ꜰʀᴇᴇ ᴛɪᴇʀ</i>\n{LINE}"
        role_line = "🆓 <b>Fʀᴇᴇ</b> · upgrade for more"
        tip = "⭐ /premium for VIP · /refer for credits"
    sec2 = (
        f"▸ <b>Nᴀᴍᴇ</b>      : {esc(u['first_name'] or '-')}\n"
        f"▸ <b>Uꜱᴇʀɴᴀᴍᴇ</b>  : @{esc(u['username'] or '-')}\n"
        f"▸ <b>Uꜱᴇʀ Iᴅ</b>   : <code>{u['user_id']}</code>\n"
        f"▸ <b>Cʀᴇᴅɪᴛꜱ</b>   : <b>{u['credits']}</b>\n"
        f"▸ <b>Rᴇꜰᴇʀʀᴀʟꜱ</b> : <b>{u['refer_count']}</b>\n"
        f"▸ <b>Rᴏʟᴇ</b>      : {role_line}\n{LINE}"
        f"<i>{tip}</i>\n{LINE}")
    sec3 = f"{pe('👨‍💻')} <b>Dᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"
    return qblocks(header, sec2, sec3), user_menu_kb(uid)

async def send_main_card(chat, uid):
    text, kb = build_main_card(uid)
    await chat.send_message(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True)

async def send_owner_panel(chat, uid):
    """Owner panel — all buttons bottom."""
    txt = qblocks(
        f"<b>👑 ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ</b>\n{LINE}",
        "ᴄʜᴏᴏꜱᴇ ᴀɴ ᴏᴘᴛɪᴏɴ 👇",
        f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}")
    await chat.send_message(txt, reply_markup=owner_reply_kb(), parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True)

async def send_admin_panel(chat, uid):
    txt = qblocks(
        f"<b>🛡 ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ</b>\n{LINE}",
        "ᴄʜᴏᴏꜱᴇ ᴀɴ ᴏᴘᴛɪᴏɴ 👇",
        f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}")
    await chat.send_message(txt, reply_markup=admin_reply_kb(uid), parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True)

def build_lookup_card(title, value, data, hits, total, charged):
    sec1 = f"<b>✅ {esc(title)}</b>\n{LINE}"
    sec2 = (
        f"🎯 <b>ᴛᴀʀɢᴇᴛ</b> : <code>{esc(value)}</code>\n"
        f"📡 <b>ʜɪᴛꜱ</b>   : {hits}/{total}\n"
        f"💳 <b>ᴄᴏꜱᴛ</b>    : {'-1 ᴄʀᴇᴅɪᴛ' if charged else 'ᴜɴʟɪᴍɪᴛᴇᴅ'}\n{LINE}")
    fields_str = format_fields(data)
    sec3 = f"{fields_str}\n{LINE}" if fields_str else ""
    sec4 = f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"
    return qblocks(sec1, sec2, sec3, sec4)

# ============================================================
#  ACCESS
# ============================================================
async def check_access(update, ctx):
    uid = update.effective_user.id
    chat = update.effective_chat
    # Owner / admin bypass force-join + credits
    if is_owner(uid) or is_admin(uid):
        return True, False
    if is_dm(update) and not is_verified(uid):
        try:
            vmsg = await update.effective_chat.send_message(
                qblocks(f"<b>🔐 Vᴇʀɪꜰɪᴄᴀᴛɪᴏɴ RᴇQᴜɪʀᴇᴅ</b>\n{LINE}",
                        "Apna contact share karo 👇"),
                reply_markup=verify_kb(), parse_mode=ParseMode.HTML)
            ctx.user_data["verify_msg_id"] = vmsg.message_id
        except Exception:
            pass
        return False, False
    if not await check_fj(ctx.bot, uid):
        try:
            if update.callback_query:
                await update.callback_query.answer("⚠ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟꜱ!", show_alert=True)
        except Exception:
            pass
        target = None
        if update.callback_query and update.callback_query.message:
            target = update.callback_query.message
        elif update.message:
            target = update.message
        elif update.effective_chat:
            target = update.effective_chat
        try:
            await send_fj(target, ctx)
        except Exception as e:
            log.warning("send_fj: %s", e)
        return False, False
    if is_gc(update) and db_is_group_wl(chat.id):
        return True, False
    u = db_get_user(uid) or await register(update)
    u = db_get_user(uid)
    if u["credits"] <= 0:
        kb = InlineKeyboardMarkup([
            [B("🎁 ʀᴇꜰᴇʀ & ᴇᴀʀɴ", cb="menu:refer")],
            [B("💎 ɢᴇᴛ ᴠɪᴘ", cb="menu:premium")]])
        if update.callback_query: await update.callback_query.answer("❌ 0 credits", show_alert=True)
        else:
            await update.message.reply_text(
                qblocks(f"<b>❌ ᴢᴇʀᴏ ᴄʀᴇᴅɪᴛꜱ</b>\n{LINE}",
                        "Refer karke ya Premium leke credits lo."),
                reply_markup=kb, parse_mode=ParseMode.HTML)
        return False, False
    db_deduct_credit(uid, 1)
    return True, True

# ============================================================
#  OSINT RUNNER
# ============================================================
def _register_job(uid, task, msg=None, cmd="", kind="osint"):
    # Cancel any previous job for this user first
    old = _active_jobs.pop(uid, None)
    if old and old.get("task") and not old["task"].done():
        old["task"].cancel()
    _active_jobs[uid] = {"task": task, "msg": msg, "cmd": cmd, "kind": kind}

def _unregister_job(uid):
    _active_jobs.pop(uid, None)

async def _cancel_user_job(uid) -> tuple:
    """Cancel active job for uid. Returns (ok, info_str)."""
    job = _active_jobs.pop(uid, None)
    if not job:
        return False, "ᴋᴏɪ ᴀᴄᴛɪᴠᴇ ᴄᴏᴍᴍᴀɴᴅ ɴᴀʜɪ ʜᴀɪ."
    task = job.get("task")
    msg = job.get("msg")
    cmd = job.get("cmd") or "?"
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=2)
        except Exception:
            pass
    if msg:
        try:
            await msg.edit_text(
                qblocks(
                    f"<b>⏹ ᴄᴀɴᴄᴇʟʟᴇᴅ</b>\n{LINE}",
                    f"▸ ᴄᴍᴅ : <code>/{cmd}</code>\n"
                    f"▸ ꜱᴛᴀᴛᴜꜱ : stopped by user\n{LINE}",
                    f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
    return True, f"/{cmd}"

async def run_osint(update, ctx, title, urls, value, cmd):
    uid = update.effective_user.id
    # Clear any pending multi-step state so new cmd always gets a reply
    ctx.user_data.pop("state", None)
    allowed, charged = await check_access(update, ctx)
    if not allowed: return
    # Owner identity shield — non-owners get silent "no data"
    if is_protected_query(value, uid):
        target = update.callback_query.message if update.callback_query else update.message
        db_log(uid, cmd, value, 0, False)
        await target.reply_text(
            qblocks(
                f"<b>❌ ɴᴏ ᴅᴀᴛᴀ ꜰᴏᴜɴᴅ</b>\n{LINE}",
                f"🎯 <code>{value}</code>\n"
                f"📡 sources checked — empty\n{LINE}",
                f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)
        return
    target = update.callback_query.message if update.callback_query else update.message
    if not target:
        return
    msg = await target.reply_text(
        qblocks(
            f"<b>{esc(title)}</b>\n{LINE}",
            f"🎯 <b>ᴛᴀʀɢᴇᴛ</b> : <code>{esc(value)}</code>\n"
            f"📡 <b>ꜱᴏᴜʀᴄᴇꜱ</b> : {len(urls)}\n{LINE}",
            f"⚡ <b>ꜰᴀɪᴛʜɪɴɢ ᴅᴀᴛᴀ…</b>\n<code>{progress_bar(0)}    0%  🌑</code>\n"
            f"<i>Cancel: /cancel</i>"),
        parse_mode=ParseMode.HTML)

    async def _job():
        done = asyncio.Event()
        anim = asyncio.create_task(animate_faith(msg, title, value, len(urls), done))
        try:
            full = [_fmt_url(u, value) for u in urls] if urls else []
            good = await fetch_all(full) if full else []
            try:
                db_hit = await asyncio.to_thread(_find_in_db, cmd, value)
            except Exception:
                db_hit = None
            done.set()
            try:
                await asyncio.wait_for(anim, timeout=0.8)
            except Exception:
                pass
            if not good and not db_hit:
                db_log(uid, cmd, value, 0, False)
                await msg.edit_text(
                    qblocks(
                        f"<b>❌ ɴᴏ ᴅᴀᴛᴀ ꜰᴏᴜɴᴅ</b>\n{LINE}",
                        f"🎯 <code>{value}</code>\n"
                        f"📡 {len(urls)} sources — sabhi empty\n"
                        f"💳 {'-1 credit' if charged else 'unlimited'}\n{LINE}",
                        f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                    parse_mode=ParseMode.HTML)
                return
            if good:
                data = merge_results(good)
                if db_hit:
                    if isinstance(data, dict):
                        data = dict(data); data["internal_db"] = db_hit
                    else:
                        data = {"api": data, "internal_db": db_hit}
                hits = len(good) + (1 if db_hit else 0)
            else:
                data = {"internal_db": db_hit}; hits = 1
            try:
                data = _format_phones_in_obj(data)
            except Exception:
                pass
            db_log(uid, cmd, value, hits, True)
            body = build_lookup_card(title, value, data, hits, max(len(urls), 1), charged)
            try:
                await msg.edit_text(body[:4000], parse_mode=ParseMode.HTML)
            except Exception:
                await msg.edit_text(
                    body[:4000].replace("<blockquote>", "").replace("</blockquote>", ""),
                    parse_mode=ParseMode.HTML)
        except asyncio.CancelledError:
            done.set()
            try:
                anim.cancel()
            except Exception:
                pass
            raise
        finally:
            _unregister_job(uid)

    task = asyncio.create_task(_job())
    _register_job(uid, task, msg=msg, cmd=cmd, kind="osint")
    try:
        await task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log.exception("run_osint %s: %s", cmd, e)
        try:
            await msg.edit_text(f"❌ Error: {e}")
        except Exception:
            pass
        _unregister_job(uid)

# ============================================================
#  COMMANDS
# ============================================================
async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = await register(update)
    if is_gc(update):
        if not u:
            await update.message.reply_text(qblocks(f"<b>🚀 ᴅᴍ ꜱᴛᴀʀᴛ ʀᴇQᴜɪʀᴇᴅ</b>\n{LINE}", f"Pehle DM me /start: @{BOT_USERNAME}"), parse_mode=ParseMode.HTML); return
        if not u["verified"]:
            await update.message.reply_text(
                qblocks(f"<b>👋 ꜱᴡᴀɢᴀᴛ ʜᴀɪ!</b>\n{LINE}",
                        f"Verification ke liye DM me <a href='https://t.me/{BOT_USERNAME}'>bot</a> par /start karo."),
                parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await update.message.reply_text(
                qblocks(f"<b>👋 {BOT_NAME} ᴀᴄᴛɪᴠᴇ</b>\n{LINE}", "Use /help for commands."),
                parse_mode=ParseMode.HTML)
        return

    # Every /start in DM → short loading info, then next screen
    msg = await update.message.reply_text(
        qblocks(f"<b>⚡ ɪɴɪᴛɪᴀʟɪᴢɪɴɢ…</b>\n{LINE}",
                f"<code>{progress_bar(0)}    0%  🌑</code>"),
        parse_mode=ParseMode.HTML)
    await animate_init(msg)
    try:
        await msg.delete()
    except Exception:
        pass

    if not u["verified"]:
        vmsg = await update.effective_chat.send_message(
            qblocks(f"<b>🔐 Vᴇʀɪꜰɪᴄᴀᴛɪᴏɴ RᴇQᴜɪʀᴇᴅ</b>\n{LINE}",
                    "Bot use karne ke liye apna contact share karo 👇"),
            reply_markup=verify_kb(), parse_mode=ParseMode.HTML)
        ctx.user_data["verify_msg_id"] = vmsg.message_id
        return
    if not (is_owner(u["user_id"]) or is_admin(u["user_id"])):
        if not await check_fj(ctx.bot, u["user_id"]):
            await send_fj(update.effective_chat, ctx)
            return
    await send_main_card(update.effective_chat, u["user_id"])

async def help_cmd(update, ctx):
    uid = update.effective_user.id
    ctx.user_data.pop("state", None)
    user_sec = (
        f"<b>✨ ᴠɪᴘ ᴄᴏᴍᴍᴀɴᴅ ᴍᴇɴᴜ</b>\n{LINE}\n"
        "<b>👤 Aᴄᴄᴏᴜɴᴛ</b>\n"
        "▸ /start — bot activate\n"
        "▸ /help — this menu\n"
        "▸ /profile — your account\n"
        "▸ /refer — earn credits\n"
        "▸ /premium — get VIP access\n"
        "▸ /history — past lookups\n"
        f"{LINE}\n"
        "<b>🔍 Oꜱɪɴᴛ Lᴏᴏᴋᴜᴘ</b>\n"
        "▸ /num — phone to info\n"
        "▸ /tg — telegram lookup\n"
        "▸ /adhr — aadhaar search\n"
        "▸ /family — family tree\n"
        "▸ /vech — vehicle info\n"
        "▸ /vechrc — RC details\n"
        "▸ /pan — PAN search\n"
        "▸ /upi — UPI to info\n"
        "▸ /ifsc — bank IFSC\n"
        "▸ /name — name search\n"
        "▸ /ip — IP geolocation\n"
        "▸ /pin — pincode info\n"
        "▸ /git — github user\n"
        "▸ /insta — instagram info\n"
        "▸ /bgmi — BGMI player\n"
        "▸ /ff — FreeFire ID\n"
        "▸ /ai — AI image gen\n"
        "▸ /dns — DNS lookup\n"
        "▸ /whois — domain whois\n"
        "▸ /bin — card BIN check\n"
        "▸ /user — username OSINT\n"
        f"{LINE}\n"
        "<b>🎮 Gᴀᴍᴇ</b>\n"
        "▸ /spin — daily GC spin\n▸ /ping — real-time latency"
    )
    extra = ""
    if is_dm(update):
        if is_owner(uid):
            extra = (
                f"\n{LINE}\n"
                "<b>👑 Oᴡɴᴇʀ</b>\n"
                "▸ /owner — owner panel\n"
                "▸ /status — live API health\n"
                "▸ /killdead — purge dead APIs\n"
                "▸ /generate — merge temp API\n"
                "▸ /cancel — stop running job\n"
                "▸ /extdb · /protect · /addapi\n"
                "▸ /delapi · /listapi · /broadcast\n"
                "▸ /getdb · /gstats · /chnl · /gc"
            )
        elif is_admin(uid):
            extra = (
                f"\n{LINE}\n"
                "<b>🛡 Aᴅᴍɪɴ</b>\n"
                "▸ /admin — admin panel\n"
                "▸ /status — live API health\n"
                "▸ /killdead — purge dead APIs\n"
                "▸ /generate — merge temp API\n"
                "▸ /cancel — stop running job\n"
                "▸ /stats · /history · /credadd"
            )
    txt = qblocks(
        f"<b>💎 {BOT_NAME}</b>\n"
        f"<i>ᴘʀᴇᴍɪᴜᴍ ᴏꜱɪɴᴛ ᴄᴏᴍᴍᴀɴᴅꜱ</i>\n{LINE}",
        user_sec + extra,
        f"👨‍💻 <b>Dᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}")
    if is_dm(update):
        await update.message.reply_text(txt, parse_mode=ParseMode.HTML,
            reply_markup=user_menu_kb(uid))
    else:
        await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

async def extdb_cmd(update, ctx):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only."); return
    args = [a.lower() for a in (ctx.args or [])]
    if args and args[0] == "import":
        n = await asyncio.to_thread(import_external_to_contacts)
        await update.message.reply_text(qblocks(f"<b>✅ ɪᴍᴘᴏʀᴛ</b>\n{LINE}", f"Contacts added/updated: <b>{n}</b>"), parse_mode=ParseMode.HTML); return
    info = external_db_info()
    path_lines = ""
    for i, pi in enumerate(info.get("paths") or [], 1):
        st = "✅" if pi.get("ok") else "❌"
        path_lines += f"  {i}. {st} <code>{pi.get('path')}</code> ({pi.get('size_mb',0)} MB)\n"
    body = (
        f"▸ Registered: <b>{info.get('count',0)}/{MAX_EXTERNAL_DBS}</b>\n"
        f"▸ Status: <b>{'✅ online' if info.get('ok') else '❌ offline'}</b>\n"
        f"▸ Tables: <b>{info.get('tables', 0)}</b>\n"
        f"▸ Rows≈ <b>{info.get('rows', 0)}</b>\n"
        f"{LINE}\n"
        f"{path_lines or '  (none yet)'}\n"
        f"{LINE}\n"
        f"Max: <b>{MAX_EXTERNAL_DBS}</b> DBs × <b>3 GB</b> each (= 60 GB)\n"
        "Upload .db (≤20 MB via Telegram) or send full VPS path\n"
        "Owner panel → External DB\n"
        "<code>/extdb import</code> → copy into contacts"
    )
    await update.message.reply_text(qblocks(f"<b>🗄 ᴇxᴛᴇʀɴᴀʟ ᴅʙ</b>\n{LINE}", body), parse_mode=ParseMode.HTML)


async def protect_cmd(update, ctx):
    """Owner-only: protect phone/tg from being looked up by others."""
    uid = update.effective_user.id
    if not is_owner(uid):
        await update.message.reply_text("❌ Owner only."); return
    ensure_owner_protected()
    args = ctx.args or []
    if not args:
        phones = _protect_list("protect_phones")
        tgs = _protect_list("protect_tg")
        body = (
            f"▸ Phones: <code>{', '.join(phones) or '—'}</code>\n"
            f"▸ TG IDs: <code>{', '.join(tgs) or '—'}</code>\n"
            f"{LINE}\n"
            "<code>/protect phone 98XXXXXXXX</code>\n"
            "<code>/protect tg 123456789</code>\n"
            "<code>/protect delphone 98XXXXXXXX</code>\n"
            "<code>/protect deltg 123456789</code>\n"
            "<code>/protect list</code>"
        )
        await update.message.reply_text(
            qblocks(f"<b>🛡 ᴏᴡɴᴇʀ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ</b>\n{LINE}", body),
            parse_mode=ParseMode.HTML); return
    action = args[0].lower()
    val = " ".join(args[1:]).strip() if len(args) > 1 else ""
    if action in ("list", "ls", "status"):
        phones = _protect_list("protect_phones")
        tgs = _protect_list("protect_tg")
        await update.message.reply_text(
            qblocks(f"<b>🛡 ᴘʀᴏᴛᴇᴄᴛᴇᴅ</b>\n{LINE}",
                f"Phones: <code>{', '.join(phones) or '—'}</code>\n"
                f"TG: <code>{', '.join(tgs) or '—'}</code>"),
            parse_mode=ParseMode.HTML); return
    if action in ("phone", "num", "addphone") and val:
        protect_add_phone(val)
        await update.message.reply_text(f"✅ Protected phone: <code>{_norm_phone_digits(val)}</code>", parse_mode=ParseMode.HTML); return
    if action in ("tg", "id", "addtg") and val:
        protect_add_tg(val)
        await update.message.reply_text(f"✅ Protected TG: <code>{val}</code>", parse_mode=ParseMode.HTML); return
    if action in ("delphone", "rmphone", "unphone") and val:
        protect_remove_phone(val)
        await update.message.reply_text("✅ Phone removed from protect list."); return
    if action in ("deltg", "rmtg", "untg") and val:
        protect_remove_tg(val)
        await update.message.reply_text("✅ TG removed from protect list."); return
    await update.message.reply_text("Usage: /protect phone|tg|delphone|deltg|list <value>")

async def num_cmd(update, ctx):
    ctx.user_data.pop("state", None)
    title, usage, urls = resolve_api("num")
    if not title and not urls:
        await update.message.reply_text(qblocks(f"<b>⚠ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ</b>\n{LINE}", "Command not configured."), parse_mode=ParseMode.HTML); return
    if not ctx.args:
        await update.message.reply_text(qblocks(f"<b>⚠ ᴜꜱᴀɢᴇ</b>\n{LINE}", f"<code>/{usage or 'num <phone>'}</code>"), parse_mode=ParseMode.HTML); return
    await run_osint(update, ctx, title or "📱 ᴘʜᴏɴᴇ", urls, ctx.args[0].strip(), "num")


async def tg_cmd(update, ctx):
    ctx.user_data.pop("state", None)
    title, usage, urls = resolve_api("tg")
    title = title or "✈️ ᴛɢ ʟᴏᴏᴋᴜᴘ"
    urls = urls or []
    if not ctx.args:
        await update.message.reply_text(
            qblocks(f"<b>⚠ ᴜꜱᴀɢᴇ</b>\n{LINE}", f"<code>/{usage or 'tg <user|id>'}</code>"),
            parse_mode=ParseMode.HTML); return

    query = ctx.args[0].strip().lstrip("@")
    uid = update.effective_user.id
    allowed, charged = await check_access(update, ctx)
    if not allowed: return
    if is_protected_query(query, uid):
        db_log(uid, "tg", query, 0, False)
        await update.message.reply_text(
            qblocks(
                f"<b>❌ ɴᴏ ᴅᴀᴛᴀ ꜰᴏᴜɴᴅ</b>\n{LINE}",
                f"🎯 <code>{query}</code>\n"
                f"📡 sources checked — empty\n{LINE}",
                f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)
        return

    msg = await update.message.reply_text(
        qblocks(
            f"<b>{title}</b>\n{LINE}",
            f"🎯 <b>ᴛᴀʀɢᴇᴛ</b> : <code>{query}</code>\n"
            f"📡 <b>ꜱᴏᴜʀᴄᴇꜱ</b> : {len(urls)+1}\n{LINE}",
            f"⚡ <b>ꜰᴀɪᴛʜɪɴɢ ᴅᴀᴛᴀ…</b>\n<code>{progress_bar(0)}    0%  🌑</code>"),
        parse_mode=ParseMode.HTML)

    done = asyncio.Event()
    anim = asyncio.create_task(animate_faith(msg, title, query, len(urls)+1, done))

    async def _bot_api():
        try:
            c = await ctx.bot.get_chat(f"@{query}")
            return {"id": c.id, "username": c.username, "first_name": c.first_name,
                    "last_name": c.last_name, "type": str(c.type),
                    "bio": getattr(c, "bio", None)}
        except Exception:
            return None

    ext_task = asyncio.create_task(fetch_all([_fmt_url(u, query) for u in urls] if urls else []))
    bot_task = asyncio.create_task(_bot_api())
    db_task = asyncio.to_thread(_find_in_db, "tg", query)
    try:
        ext, bot_data, db_hit = await asyncio.gather(ext_task, bot_task, db_task)
    except Exception:
        ext, bot_data, db_hit = [], None, None
    if not isinstance(ext, list):
        ext = []

    merged = {}
    if bot_data: merged["telegram_bot_api"] = bot_data
    for r in ext:
        u = r.get("_url","?"); srcn = u.split("/")[2] if "//" in u else u
        merged[srcn] = r.get("data")
    if db_hit:
        merged["internal_db"] = db_hit

    tg_id = None
    if bot_data and bot_data.get("id"): tg_id = bot_data["id"]
    if not tg_id:
        for src, d in merged.items():
            if isinstance(d, dict):
                for k in ("id","userid","user_id","tg_id","chat_id"):
                    v = d.get(k)
                    if v:
                        try: tg_id = int(v); break
                        except: pass
                if tg_id: break
    if tg_id:
        local = await asyncio.to_thread(db_find_phone_by_tg, tg_id)
        if local:
            merged["internal_db"] = {
                "number": local["phone"],
                "name": f"{local.get('first_name','')} {local.get('last_name','')}".strip(),
                "source": "internal_database",
                "tg_id": tg_id
            }

    done.set()
    try:
        await asyncio.wait_for(anim, timeout=0.8)
    except Exception:
        pass

    if not merged:
        db_log(uid, "tg", query, 0, False)
        await msg.edit_text(
            qblocks(f"<b>❌ ɴᴏ ᴅᴀᴛᴀ</b>\n{LINE}", f"🎯 <code>{query}</code>\n{LINE}",
                    f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML); return

    try:
        merged = _format_phones_in_obj(merged)
    except Exception:
        pass
    db_log(uid, "tg", query, len(merged), True)
    body = build_lookup_card(title, query, merged, len(merged), len(urls)+1, charged)
    try: await msg.edit_text(body[:4000], parse_mode=ParseMode.HTML)
    except: await msg.edit_text(
        body[:4000].replace("<blockquote>","").replace("</blockquote>",""),
        parse_mode=ParseMode.HTML)

async def ai_cmd(update, ctx):
    ctx.user_data.pop("state", None)
    if not ctx.args:
        await update.message.reply_text(qblocks(f"<b>⚠ ᴜꜱᴀɢᴇ</b>\n{LINE}",
            "<code>/ai cute cat</code>"), parse_mode=ParseMode.HTML); return
    allowed, charged = await check_access(update, ctx)
    if not allowed: return
    prompt = " ".join(ctx.args); seed = random.randint(1,999999)
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
    msg = await update.message.reply_text(
        qblocks(f"<b>🎨 ᴀɪ ɪᴍᴀɢᴇ</b>\n{LINE}", "ɢᴇɴᴇʀᴀᴛɪɴɢ…"),
        parse_mode=ParseMode.HTML)
    try:
        img = None
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90), headers={"User-Agent":"Mozilla/5.0"}) as session:
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status == 200:
                    img = await resp.read()
        if not img or len(img) < 500:
            await msg.edit_text(f"❌ image download failed"); return
        from io import BytesIO
        bio = BytesIO(img); bio.name = "ai.png"
        await update.message.reply_photo(photo=bio,
            caption=qblocks(f"<b>✨ {prompt}</b>\n{LINE}",
                            f"⚜️ <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)
        await msg.delete(); db_log(update.effective_user.id, "ai", prompt, 1, True)
    except Exception as e: await msg.edit_text(f"❌ {e}")

# ============================================================
#  SPIN
# ============================================================
def dart_result():
    r = random.random()
    if r < 0.05:  return 5, "ᴄᴇɴᴛᴇʀ ʙᴜʟʟꜱᴇʏᴇ", "ᴘᴇʀꜰᴇᴄᴛ ꜱʜᴏᴛ 🎯"
    if r < 0.15:  return 4, "ɪɴɴᴇʀ ʀɪɴɢ", "ɢʀᴇᴀᴛ ᴀɪᴍ"
    if r < 0.35:  return 3, "ᴍɪᴅᴅʟᴇ ʀɪɴɢ", "ɢᴏᴏᴅ ꜱʜᴏᴛ"
    if r < 0.60:  return 2, "ᴏᴜᴛᴇʀ ʀɪɴɢ", "ᴅᴇᴄᴇɴᴛ"
    if r < 0.85:  return 1, "ᴄᴏʀɴᴇʀ ᴢᴏɴᴇ", "ʙᴀʀᴇʟʏ ʜɪᴛ"
    return 0, "ᴍɪꜱꜱᴇᴅ", "ᴛʀʏ ᴀɢᴀɪɴ"

def _main_gc_link():
    """Best available Main GC invite / public link for buttons."""
    # Prefer channel row for MAIN_GC_ID
    if MAIN_GC_ID:
        for ch in db_list_channels():
            if int(ch.get("chat_id") or 0) == int(MAIN_GC_ID):
                if ch.get("invite_link"):
                    return ch["invite_link"]
                if ch.get("username"):
                    return f"https://t.me/{ch['username'].lstrip('@')}"
    # Any group-looking channel with a link
    for ch in db_list_channels():
        if ch.get("invite_link"):
            return ch["invite_link"]
        if ch.get("username"):
            return f"https://t.me/{ch['username'].lstrip('@')}"
    return None

async def spin_cmd(update, ctx):
    if is_dm(update):
        link = _main_gc_link()
        body = (
            "DM me /spin allow nahi hai.\n"
            "Group / GC me jaake use karo.\n"
            f"{LINE}\n"
            "Neeche button se GC open karo 👇"
        )
        kb_rows = []
        if link:
            kb_rows.append([B("Open Main GC", url=link, style="primary")])
        else:
            kb_rows.append([B("GC link not set", cb="fj:check", style="danger")])
        await update.message.reply_text(
            qblocks(f"<b>ɢᴄ ᴏɴʟʏ</b>\n{LINE}", body),
            reply_markup=InlineKeyboardMarkup(kb_rows),
            parse_mode=ParseMode.HTML)
        return

    uid = update.effective_user.id
    u = db_get_user(uid) or await register(update)
    u = db_get_user(uid)

    if not user_is_premium(u) and u["refer_count"] < SPIN_UNLOCK_REFS:
        await update.message.reply_text(
            qblocks(
                f"<b>🔒 ꜱᴘɪɴ ʟᴏᴄᴋᴇᴅ</b>\n{LINE}",
                f"🎯 ᴜɴʟᴏᴄᴋ ʀᴇQᴜɪʀᴇᴅ: <b>{SPIN_UNLOCK_REFS} ʀᴇꜰᴇʀʀᴀʟꜱ</b>\n"
                f"👥 ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟꜱ : <b>{u['refer_count']}/{SPIN_UNLOCK_REFS}</b>\n"
                f"{LINE}\n"
                f"<i>ᴏʀ ɢᴇᴛ ᴠɪᴘ ꜰᴏʀ ɪɴꜱᴛᴀɴᴛ ᴜɴʟᴏᴄᴋ.</i>"),
            parse_mode=ParseMode.HTML); return

    can, remain = db_can_spin(uid)
    if not can:
        total = int(remain.total_seconds())
        h, m = total // 3600, (total % 3600) // 60
        await update.message.reply_text(
            qblocks(f"<b>⏰ ᴄᴏᴏʟᴅᴏᴡɴ</b>\n{LINE}",
                    f"🎯 ɴᴇxᴛ ꜱᴘɪɴ ɪɴ: <b>{h}ʜ {m}ᴍ</b>\n{LINE}",
                    f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML); return

    msg = await update.message.reply_text(
        qblocks(
            f"<b>⚡ ꜱᴘɪɴ ᴛʜᴇ ᴅᴀʀᴛ ⚡</b>\n{LINE}",
            f"🎯 ᴛʜʀᴏᴡɪɴɢ ᴅᴀʀᴛ…\n<code>{progress_bar(0)}    0%  🌑</code>"),
        parse_mode=ParseMode.HTML)

    for i in range(1, 11):
        await asyncio.sleep(0.07)
        filled = i; pct = i * 10
        try:
            await msg.edit_text(
                qblocks(
                    f"<b>⚡ ꜱᴘɪɴ ᴛʜᴇ ᴅᴀʀᴛ ⚡</b>\n{LINE}",
                    f"🎯 ᴛʜʀᴏᴡɪɴɢ ᴅᴀʀᴛ…\n"
                    f"<code>{progress_bar(filled)}  {pct:3d}%  {progress_emoji(pct)}</code>"),
                parse_mode=ParseMode.HTML)
        except: pass

    points, zone, feedback = dart_result()
    db_do_spin(uid, points)
    u2 = db_get_user(uid)

    if points == 0: hdr = "<b>💨 ᴅᴀʀᴛ ᴍɪꜱꜱᴇᴅ!</b>"
    elif points >= 5: hdr = "<b>🎯 ʙᴜʟʟꜱᴇʏᴇ!</b>"
    else: hdr = "<b>🎯 ᴅᴀʀᴛ ʟᴀɴᴅᴇᴅ</b>"

    await msg.edit_text(
        qblocks(
            f"{hdr}\n{LINE}",
            f"🎯 <b>ᴢᴏɴᴇ</b>   : <b>{zone}</b>\n"
            f"📍 <b>ꜱʜᴏᴛ</b>   : {feedback}\n"
            f"🎁 <b>ᴘᴏɪɴᴛꜱ</b> : <b>+{points} ᴄʀᴇᴅɪᴛꜱ</b>\n{LINE}",
            f"💳 <b>ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ</b> : <b>{u2['credits']}</b>\n"
            f"⏰ <b>ɴᴇxᴛ ꜱᴘɪɴ</b>  : ᴀꜰᴛᴇʀ {SPIN_COOLDOWN_HRS}ʜ\n{LINE}",
            f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
        parse_mode=ParseMode.HTML)

# ============================================================
#  PROFILE / REFER / PREMIUM
# ============================================================
async def history_cmd(update, ctx):
    """User lookup history as downloadable file."""
    uid = update.effective_user.id
    ctx.user_data.pop("state", None)
    rows = db_get_history(uid, limit=500)
    if not rows:
        await update.message.reply_text(
            qblocks(f"<b>📜 ʜɪꜱᴛᴏʀʏ</b>\n{LINE}", "ɴᴏ ʟᴏᴏᴋᴜᴘꜱ ʏᴇᴛ."),
            parse_mode=ParseMode.HTML)
        return
    fname = build_history_file(rows, uid)
    try:
        await update.message.reply_document(
            document=open(fname, "rb"),
            caption=qblocks(
                f"<b>📜 ʏᴏᴜʀ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
                f"▸ ᴛᴏᴛᴀʟ ʟᴏɢꜱ : <b>{len(rows)}</b>\n{LINE}",
                dev_signature_txt()),
            parse_mode=ParseMode.HTML)
    finally:
        try:
            os.remove(fname)
        except Exception:
            pass

async def profile_cmd(update, ctx):
    await register(update)
    u = db_get_user(update.effective_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{u['user_id']}" if BOT_USERNAME else "(set BOT_USERNAME)"
    tier = f"{pe('💎')} Vɪᴘ" if user_is_premium(u) else "🆓 Fʀᴇᴇ"
    role = "👑 ᴏᴡɴᴇʀ" if is_owner(u["user_id"]) else ("🛡 ᴀᴅᴍɪɴ" if u["is_admin"] else "👤 ᴜꜱᴇʀ")
    ver = "✅ ᴠᴇʀɪꜰɪᴇᴅ" if u["verified"] else "❌ ᴜɴᴠᴇʀɪꜰɪᴇᴅ"
    spin_status = f"{pe('🔓')} Uɴʟᴏᴄᴋᴇᴅ" if (user_is_premium(u) or u["refer_count"] >= SPIN_UNLOCK_REFS) else f"{pe('🔒')} Lᴏᴄᴋᴇᴅ"
    txt = qblocks(
        f"<b>👤 ᴍʏ ᴘʀᴏꜰɪʟᴇ</b>\n{LINE}",
        f"▸ <b>ɴᴀᴍᴇ</b>      : {u['first_name'] or '-'}\n"
        f"▸ <b>ᴜꜱᴇʀɴᴀᴍᴇ</b>  : @{u['username'] or '-'}\n"
        f"▸ <b>ᴜꜱᴇʀ ɪᴅ</b>   : <code>{u['user_id']}</code>\n"
        f"▸ <b>ʀᴏʟᴇ</b>      : {role}\n"
        f"▸ <b>ᴛɪᴇʀ</b>      : {tier}\n"
        f"▸ <b>ꜱᴛᴀᴛᴜꜱ</b>    : {ver}\n"
        f"▸ <b>ᴄʀᴇᴅɪᴛꜱ</b>   : <b>{u['credits']}</b>\n"
        f"▸ <b>ʀᴇꜰᴇʀʀᴀʟꜱ</b> : <b>{u['refer_count']}</b>\n"
        f"▸ <b>ꜱᴘɪɴ</b>      : {spin_status}\n{LINE}",
        f"🔗 <b>ʀᴇꜰᴇʀ ʟɪɴᴋ</b>\n<code>{link}</code>",
        f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}")
    kb = InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:home")]])
    if update.callback_query: await update.callback_query.message.edit_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
    else: await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

async def refer_cmd(update, ctx):
    u = db_get_user(update.effective_user.id)
    if not u: await register(update); u = db_get_user(update.effective_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{u['user_id']}" if BOT_USERNAME else "(set BOT_USERNAME)"
    rate = REF_CREDIT_PREMIUM if user_is_premium(u) else REF_CREDIT
    txt = qblocks(
        f"<b>🎁 ʀᴇꜰᴇʀ & ᴇᴀʀɴ</b>\n{LINE}",
        f"🔗 <code>{link}</code>\n{LINE}",
        f"▸ <b>ᴘᴇʀ ʀᴇꜰᴇʀ</b>   : <b>+{rate} ᴄʀᴇᴅɪᴛ</b>\n"
        f"▸ <b>ʙᴏɴᴜꜱ</b>      : ᴇᴠᴇʀʏ {REF_BONUS_EVERY}ᴛʜ ʀᴇꜰᴇʀ = +{REF_BONUS_AMOUNT}\n"
        f"▸ <b>ᴠɪᴘ</b>    : +{REF_CREDIT_PREMIUM} ᴘᴇʀ ʀᴇꜰᴇʀ\n"
        f"▸ <b>ʏᴏᴜʀ ᴄᴏᴜɴᴛ</b> : <b>{u['refer_count']}</b>\n{LINE}\n"
        f"🎯 <b>ꜱᴘɪɴ ᴜɴʟᴏᴄᴋ</b> : {SPIN_UNLOCK_REFS} ʀᴇꜰᴇʀʀᴀʟꜱ",
        f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}")
    kb = InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:home")]])
    if update.callback_query: await update.callback_query.message.edit_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
    else: await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

async def premium_cmd(update, ctx):
    u = db_get_user(update.effective_user.id)
    tier = f"{pe('💎')} Vɪᴘ Aᴄᴛɪᴠᴇ" if (u and user_is_premium(u)) else "🆓 Fʀᴇᴇ Uꜱᴇʀ"
    txt = qblocks(
        f"<b>💎 ᴠɪᴘ</b>\n{LINE}",
        f"{tier}\n{LINE}",
        f"▸ {PREMIUM_CREDITS} ꜱᴛᴀʀᴛɪɴɢ ᴄʀᴇᴅɪᴛꜱ\n"
        f"▸ {REF_CREDIT_PREMIUM} ᴄʀᴇᴅɪᴛꜱ ᴘᴇʀ ʀᴇꜰᴇʀ\n"
        f"▸ {REF_BONUS_EVERY}ᴛʜ ʀᴇꜰᴇʀ +{REF_BONUS_AMOUNT} ʙᴏɴᴜꜱ\n"
        f"▸ 🎯 ꜱᴘɪɴ ɪɴꜱᴛᴀɴᴛʟʏ ᴜɴʟᴏᴄᴋᴇᴅ\n"
        f"▸ ᴘʀɪᴏʀɪᴛʏ ꜱᴜᴘᴘᴏʀᴛ\n{LINE}\n"
        f"<i>ᴘᴜʀᴄʜᴀꜱᴇ ᴋᴇ ʟɪʏᴇ ᴏᴡɴᴇʀ ꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴋᴀʀᴏ.</i>",
        f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}")
    kb = InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:home")]])
    if update.callback_query: await update.callback_query.message.edit_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)
    else: await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

async def admin_cmd(update, ctx):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only."); return
    await send_admin_panel(update.effective_chat, update.effective_user.id)

async def owner_cmd(update, ctx):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only."); return
    await send_owner_panel(update.effective_chat, update.effective_user.id)

# ============================================================
#  API PARSER + ROUTER
# ============================================================
def parse_api_txt(text):
    valid, errors = [], []
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"): continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 4:
            errors.append(f"L{ln}: expected 4 fields, got {len(parts)}"); continue
        cmd, title, usage, urls_s = parts
        cmd = cmd.lower().lstrip("/")
        if not cmd.isalnum():
            errors.append(f"L{ln}: invalid cmd '{cmd}'"); continue
        if not title or not usage:
            errors.append(f"L{ln}: empty title/usage"); continue
        urls = [u.strip() for u in urls_s.split(",") if u.strip()]
        if not urls:
            errors.append(f"L{ln}: no urls"); continue
        if any("{value}" not in u for u in urls):
            errors.append(f"L{ln}: url missing {{value}}"); continue
        valid.append((cmd, title, usage.lstrip("/"), urls))
    return valid, errors


async def ping_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Real-time bot latency (Telegram round-trip + local)."""
    t0 = time.perf_counter()
    # Probe Telegram API (get_me is light and always works)
    api_ms = None
    try:
        t_api = time.perf_counter()
        await ctx.bot.get_me()
        api_ms = (time.perf_counter() - t_api) * 1000.0
    except Exception:
        api_ms = None
    # Local processing after API probe
    local_ms = (time.perf_counter() - t0) * 1000.0
    # Message send latency measured by edit if possible
    msg = await update.message.reply_text(
        qblocks(
            f"<b>📡 ᴘɪɴɢ</b>\n{LINE}",
            "Measuring…"),
        parse_mode=ParseMode.HTML)
    t_send = time.perf_counter()
    total_ms = (t_send - t0) * 1000.0
    # Quality label
    ref = api_ms if api_ms is not None else total_ms
    if ref < 80:
        quality = "🟢 Exᴄᴇʟʟᴇɴᴛ"
    elif ref < 150:
        quality = "🟡 Gᴏᴏᴅ"
    elif ref < 300:
        quality = "🟠 Fᴀɪʀ"
    else:
        quality = "🔴 Sʟᴏᴡ"
    api_line = f"▸ <b>Tᴇʟᴇɢʀᴀᴍ Aᴘɪ</b> : <code>{api_ms:.0f} ms</code>\n" if api_ms is not None else "▸ <b>Tᴇʟᴇɢʀᴀᴍ Aᴘɪ</b> : <code>n/a</code>\n"
    body = (
        f"{api_line}"
        f"▸ <b>Rᴏᴜɴᴅ-ᴛʀɪᴘ</b>  : <code>{total_ms:.0f} ms</code>\n"
        f"▸ <b>Sᴛᴀᴛᴜꜱ</b>      : {quality}\n{LINE}"
        f"<i>Real-time · {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC</i>"
    )
    try:
        await msg.edit_text(
            qblocks(f"<b>📡 ᴘɪɴɢ</b>\n{LINE}", body, f"👨‍💻 <b>Dᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)
    except Exception:
        await update.message.reply_text(
            qblocks(f"<b>📡 ᴘɪɴɢ</b>\n{LINE}", body, f"👨‍💻 <b>Dᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Cancel running OSINT / broadcast — Admin / Owner only."""
    uid = update.effective_user.id
    if not (is_owner(uid) or is_admin(uid)):
        await update.message.reply_text("❌ Admin / Owner only."); return
    ctx.user_data.pop("state", None)
    ok, info = await _cancel_user_job(uid)
    if ok:
        await update.message.reply_text(
            qblocks(
                f"<b>⏹ ᴄᴀɴᴄᴇʟʟᴇᴅ</b>\n{LINE}",
                f"▸ ꜱᴛᴏᴘᴘᴇᴅ : <code>{info}</code>\n"
                f"▸ ɴᴇᴡ ᴄᴍᴅ ʙʜᴇᴊ ꜱᴀᴋᴛᴇ ʜᴏ.\n{LINE}",
                f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(
            qblocks(
                f"<b>ℹ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴊᴏʙ</b>\n{LINE}",
                f"{info}\n"
                f"Abhi koi lookup / broadcast nahi chal raha.\n{LINE}",
                f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Real-time API health check — Admin / Owner."""
    uid = update.effective_user.id
    if not (is_owner(uid) or is_admin(uid)):
        await update.message.reply_text("❌ Admin / Owner only."); return
    ctx.user_data.pop("state", None)
    msg = await update.message.reply_text(
        qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ</b>\n{LINE}",
                "Realtime scan chal raha hai…\n<code>please wait</code>"),
        parse_mode=ParseMode.HTML)
    try:
        scan = await live_status_scan()
    except Exception as e:
        await msg.edit_text(f"❌ scan failed: {e}"); return
    if not scan:
        await msg.edit_text(
            qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ</b>\n{LINE}", "No APIs configured."),
            parse_mode=ParseMode.HTML); return
    alive_lines, dead_lines = [], []
    total_ok = total_dead = 0
    for cmd, probes in sorted(scan.items()):
        ok_n = sum(1 for p in probes if p["ok"])
        dead_n = len(probes) - ok_n
        total_ok += ok_n
        total_dead += dead_n
        if ok_n:
            best = min((p["ms"] for p in probes if p["ok"]), default=0)
            alive_lines.append(f"✅ <code>/{cmd}</code> — {ok_n}/{len(probes)} up · {best}ms")
        if dead_n:
            reasons = []
            for p in probes:
                if p["ok"]:
                    continue
                tag = "EXPIRED" if p.get("expired") else ("ERR" if p.get("error") else f"HTTP {p.get('status')}")
                reasons.append(tag)
            dead_lines.append(
                f"❌ <code>/{cmd}</code> — {dead_n}/{len(probes)} down · {', '.join(reasons[:3])}")
    body = (
        f"▸ Active sources : <b>{total_ok}</b>\n"
        f"▸ Dead / expired : <b>{total_dead}</b>\n"
        f"▸ Commands       : <b>{len(scan)}</b>\n{LINE}\n"
    )
    if alive_lines:
        body += "<b>🟢 WORKING</b>\n" + "\n".join(alive_lines[:25]) + "\n"
    if dead_lines:
        body += f"{LINE}\n<b>🔴 DEAD / EXPIRED</b>\n" + "\n".join(dead_lines[:25])
    body += f"\n{LINE}\n🗑 Purge dead → <code>/killdead</code>"
    try:
        await msg.edit_text(
            qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ — ʟɪᴠᴇ</b>\n{LINE}", body[:3800]),
            parse_mode=ParseMode.HTML)
    except Exception:
        await msg.edit_text(body[:4000])

async def killdead_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Remove all dead/expired API URLs from DB — Admin / Owner."""
    uid = update.effective_user.id
    if not (is_owner(uid) or is_admin(uid)):
        await update.message.reply_text("❌ Admin / Owner only."); return
    ctx.user_data.pop("state", None)
    msg = await update.message.reply_text(
        qblocks(f"<b>🗑 ᴋɪʟʟ ᴅᴇᴀᴅ</b>\n{LINE}", "Scanning & removing dead APIs…"),
        parse_mode=ParseMode.HTML)
    try:
        killed_urls, killed_cmds, dead_list = await kill_dead_apis()
        # also cleanup expired generated keys
        exp_gen = db_cleanup_expired_generated()
    except Exception as e:
        await msg.edit_text(f"❌ {e}"); return
    body = (
        f"▸ URLs removed   : <b>{killed_urls}</b>\n"
        f"▸ Commands wiped : <b>{len(killed_cmds)}</b>\n"
        f"▸ Gen keys expired: <b>{len(exp_gen)}</b>\n{LINE}\n"
    )
    if killed_cmds:
        body += "Deleted cmds:\n" + "\n".join(f"· <code>/{c}</code>" for c in killed_cmds[:20]) + "\n"
    if dead_list:
        body += f"{LINE}\n<details removed:\n" + "\n".join(dead_list[:15])
    if killed_urls == 0 and not killed_cmds and not exp_gen:
        body = "Sab APIs healthy — kuch delete nahi hua. ✅"
    await msg.edit_text(
        qblocks(f"<b>🗑 ᴋɪʟʟ ᴅᴇᴀᴅ — ᴅᴏɴᴇ</b>\n{LINE}", body[:3800]),
        parse_mode=ParseMode.HTML)

# Duration options for /generate (max 30 days)
_GEN_MAX_HOURS = 24 * 30  # 30 days
_GEN_DURATIONS = [
    ("1h", 1), ("6h", 6), ("12h", 12),
    ("1d", 24), ("3d", 72), ("7d", 168),
    ("15d", 360), ("30d", 720),
]

def _gen_api_buttons():
    """Available API types for generate flow."""
    cmds = []
    seen = set()
    for r in db_list_custom_apis():
        c = r["cmd"]
        if c not in seen:
            cmds.append(c); seen.add(c)
    for c in ("num", "tg", "family", "adhr", "pan", "upi", "vech", "name", "ip", "user"):
        if c not in seen:
            title, usage, urls = resolve_api(c)
            if urls:
                cmds.append(c); seen.add(c)
    rows, row = [], []
    for c in cmds[:24]:
        row.append(B(f"/{c}", cb=f"gen:cmd:{c}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([B("❌ ᴄʟᴏꜱᴇ", cb="gen:close", style="danger")])
    return InlineKeyboardMarkup(rows)

def _gen_duration_buttons(cmd):
    rows, row = [], []
    for label, _hrs in _GEN_DURATIONS:
        row.append(B(label, cb=f"gen:dur:{cmd}:{label}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([B("⬅ ʙᴀᴄᴋ", cb="gen:back"), B("❌ ᴄʟᴏꜱᴇ", cb="gen:close", style="danger")])
    return InlineKeyboardMarkup(rows)

async def generate_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Merge all sources for a cmd into a time-limited kittu-osint API key."""
    uid = update.effective_user.id
    if not (is_owner(uid) or is_admin(uid)):
        await update.message.reply_text("❌ Admin / Owner only."); return
    ctx.user_data.pop("state", None)
    db_cleanup_expired_generated()
    await update.message.reply_text(
        qblocks(
            f"<b>🧬 ɢᴇɴᴇʀᴀᴛᴇ ᴀᴘɪ</b>\n{LINE}",
            "Kaunsi API type chahiye?\n"
            "Bot saari sources merge karke\n"
            "<b>kittu-osint</b> temp key banayega."),
        reply_markup=_gen_api_buttons(),
        parse_mode=ParseMode.HTML)

async def _do_generate(uid, cmd, duration_label, hours, message):
    """Create merged time-limited API as .json file (max 30 days)."""
    # Cap at 30 days
    try:
        hours = int(hours)
    except Exception:
        hours = 24
    if hours < 1:
        hours = 1
    if hours > _GEN_MAX_HOURS:
        hours = _GEN_MAX_HOURS
        duration_label = "30d"

    title, usage, urls = resolve_api(cmd)
    row = db_get_custom_api(cmd)
    if row:
        try:
            extra = json.loads(row["urls"] or "[]")
        except Exception:
            extra = []
        for u in extra:
            if u not in urls:
                urls.append(u)
    if not urls:
        await message.edit_text(
            qblocks(f"<b>❌ ɴᴏ ꜱᴏᴜʀᴄᴇꜱ</b>\n{LINE}",
                    f"<code>/{esc(cmd)}</code> ke liye koi URL nahi mila."),
            parse_mode=ParseMode.HTML)
        return

    token = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
    api_key = f"kittu-osint-{cmd}-{token}"
    created = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = created + timedelta(hours=hours)
    created_iso = created.isoformat(timespec="seconds")
    expires_iso = expires.isoformat(timespec="seconds")
    title_g = f"{title or cmd} · kittu-osint"

    db_add_generated_api(api_key, cmd, title_g, urls, expires_iso, uid)
    if not db_get_custom_api(api_key):
        db_add_custom_api(api_key, title_g, f"{api_key} <value>", urls, uid)
    else:
        db_update_custom_urls(api_key, urls)

    # JSON API package
    payload = {
        "brand": "kittu-osint",
        "api_key": api_key,
        "command": cmd,
        "title": title_g,
        "usage": f"/{api_key} <value>",
        "sources_count": len(urls),
        "urls": urls,
        "duration": duration_label,
        "duration_hours": hours,
        "created_at": created_iso + "Z",
        "expires_at": expires_iso + "Z",
        "max_expiry_days": 30,
        "created_by": uid,
        "format": "json",
        "note": "Valid only until expires_at. Use with bot command or import via /addapi.",
    }
    fname = f"{api_key}.json"
    try:
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        await message.edit_text(f"❌ JSON write failed: {e}")
        return

    caption = qblocks(
        f"<b>✅ ᴋɪᴛᴛᴜ-ᴏꜱɪɴᴛ ᴀᴘɪ (.ᴊꜱᴏɴ)</b>\n{LINE}",
        f"▸ Key      : <code>{esc(api_key)}</code>\n"
        f"▸ Type     : <code>/{esc(cmd)}</code>\n"
        f"▸ Sources  : <b>{len(urls)}</b> merged\n"
        f"▸ Duration : <b>{esc(duration_label)}</b> (max 30d)\n"
        f"▸ Expires  : <code>{esc(expires_iso)} UTC</code>\n"
        f"{LINE}\n"
        f"<b>Usage</b>\n<code>/{esc(api_key)} &lt;value&gt;</code>\n"
        f"{LINE}\n"
        f"File: <code>{esc(fname)}</code>\n"
        f"Expiry ke baad auto-invalid.")

    try:
        await message.edit_text(
            qblocks(f"<b>✅ ɢᴇɴᴇʀᴀᴛᴇᴅ</b>\n{LINE}", "JSON file bhej raha hoon…"),
            parse_mode=ParseMode.HTML)
    except Exception:
        pass

    try:
        with open(fname, "rb") as doc:
            await message.reply_document(
                document=doc,
                filename=fname,
                caption=caption[:1000],
                parse_mode=ParseMode.HTML)
    except Exception as e:
        # fallback: send JSON as text file without caption HTML issues
        try:
            with open(fname, "rb") as doc:
                await message.reply_document(
                    document=doc,
                    filename=fname,
                    caption=f"Key: {api_key}\nExpires: {expires_iso} UTC\nUsage: /{api_key} <value>")
        except Exception as e2:
            await message.edit_text(f"❌ send failed: {e2}")
    finally:
        try:
            os.remove(fname)
        except Exception:
            pass

async def custom_api_router(update, ctx):
    msg = update.message
    if not msg or not msg.text: return
    txt = msg.text.strip()
    if not txt.startswith("/"): return
    # Only respond to commands aimed at THIS bot (or bare /cmd without @otherbot)
    first = txt.split()[0]  # /cmd or /cmd@bot
    if "@" in first:
        mention = first.split("@", 1)[1].lower().lstrip("@")
        if mention and mention != BOT_USERNAME.lower():
            return  # command for another bot — ignore completely
    cmd = first[1:].split("@")[0].lower()
    # skip built-in handlers already registered
    if cmd in ("start","help","profile","history","refer","premium","admin","owner","ai","extdb",
               "num","tg","spin","addapi","delapi","listapi","menu","cmd","cmds","cancel",
               "status","killdead","generate","genrate","protect","ping"):
        return
    # Always clear pending state so command is never ignored
    ctx.user_data.pop("state", None)
    # Generated kittu-osint keys — enforce expiry
    if cmd.startswith("kittu-osint-"):
        gen = db_get_generated_api(cmd)
        if gen:
            try:
                exp = datetime.fromisoformat(gen["expires_at"])
            except Exception:
                exp = datetime.now(timezone.utc).replace(tzinfo=None)
            if exp <= datetime.now(timezone.utc).replace(tzinfo=None):
                db_remove_generated_api(cmd)
                db_remove_custom_api(cmd)
                await msg.reply_text(
                    qblocks(f"<b>⏱ ᴀᴘɪ ᴇxᴘɪʀᴇᴅ</b>\n{LINE}",
                            f"<code>/{cmd}</code> ka time khatam.\n"
                            f"Naya banane ke liye /generate"),
                    parse_mode=ParseMode.HTML)
                return
    title, usage, urls = resolve_api(cmd)
    if not urls and not title:
        # Unknown cmd — only soft-reply in private chat; never in groups
        if is_dm(update):
            await msg.reply_text(
                qblocks(
                    f"<b>❓ ᴜɴᴋɴᴏᴡɴ ᴄᴏᴍᴍᴀɴᴅ</b>\n{LINE}",
                    f"<code>/{cmd}</code> configured nahi hai.\n"
                    f"Use /help or /cmd for list."),
                parse_mode=ParseMode.HTML)
        return
    args = txt.split()[1:]
    if not args:
        await msg.reply_text(qblocks(f"<b>⚠ ᴜꜱᴀɢᴇ</b>\n{LINE}",
            f"<code>/{usage or (cmd + ' <value>')}</code>"), parse_mode=ParseMode.HTML); return
    value = " ".join(args).strip()
    await run_osint(update, ctx, title or cmd, urls or [], value, cmd)

async def addapi_cmd(update, ctx):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only."); return
    ctx.user_data["state"] = ("api_add", None)
    await update.message.reply_text(
        qblocks(f"<b>➕ ᴀᴅᴅ ᴄᴜꜱᴛᴏᴍ ᴀᴘɪ</b>\n{LINE}",
                "Send a <b>.txt</b> file.\n"
                f"{LINE}\n<b>Format per line:</b>\n"
                "<code>cmd|title|usage|url1,url2</code>\n"
                f"{LINE}\n"
                "<i>Existing commands safe rahenge — sirf naye add honge.</i>"),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [B("📄 ɢᴇᴛ ᴛᴇᴍᴘʟᴀᴛᴇ", cb="o:api_tpl")],
            [B("📋 ᴠɪᴇᴡ ʟɪꜱᴛ", cb="o:api_list")]]))

async def delapi_cmd(update, ctx):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only."); return
    if not ctx.args:
        await update.message.reply_text(qblocks(f"<b>⚠ ᴜꜱᴀɢᴇ</b>\n{LINE}",
            "<code>/delapi cmdname</code>"), parse_mode=ParseMode.HTML); return
    cmd = ctx.args[0].lstrip("/").lower()
    if db_get_custom_api(cmd):
        db_remove_custom_api(cmd)
        await update.message.reply_text(
            qblocks(f"<b>✅ ᴅᴇʟᴇᴛᴇᴅ</b>\n{LINE}", f"<code>/{cmd}</code>"),
            parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(
            qblocks(f"<b>❌ ɴᴏᴛ ꜰᴏᴜɴᴅ</b>\n{LINE}", f"<code>/{cmd}</code>"),
            parse_mode=ParseMode.HTML)

async def listapi_cmd(update, ctx):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Owner only."); return
    rows = db_list_custom_apis()
    if not rows:
        body = "ɴᴏ ᴄᴜꜱᴛᴏᴍ ᴀᴘɪꜱ."
    else:
        parts = []
        for r in rows:
            try:
                ul = json.loads(r["urls"] or "[]")
            except Exception:
                ul = []
            parts.append(
                f"▸ <code>/{r['cmd']}</code> — {r['title']}\n"
                + "\n".join(f"   · <code>{u}</code>" for u in ul))
        body = "\n\n".join(parts)
    await update.message.reply_text(
        qblocks(f"<b>📋 ᴄᴜꜱᴛᴏᴍ ᴀᴘɪꜱ ({len(rows)})</b>\n{LINE}", body[:3500]),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [B("➕ ᴀᴅᴅ", cb="o:api_add"), B("🗑 ᴅᴇʟ", cb="o:api_del")]]))

# ============================================================
#  CALLBACK ROUTER
# ============================================================

async def cmd_cmd(update, ctx):
    """ /cmd or /cmds — list all commands by role (owner sees everything). """
    uid = update.effective_user.id
    ctx.user_data.pop("state", None)
    role = get_user_role(uid)

    free_cmds = (
        f"<b>👤 Aᴄᴄᴏᴜɴᴛ</b>\n"
        f"▸ /start — activate bot\n"
        f"▸ /help — help menu\n"
        f"▸ /cmd — this command list\n"
        f"▸ /profile — your account\n"
        f"▸ /refer — earn credits\n"
        f"▸ /premium — VIP info\n"
        f"▸ /history — past lookups\n"
        f"{LINE}\n"
        f"<b>🔍 Oꜱɪɴᴛ</b>\n"
        f"▸ /num · /tg · /adhr · /family\n"
        f"▸ /vech · /vechrc · /pan · /upi\n"
        f"▸ /ifsc · /name · /ip · /pin\n"
        f"▸ /git · /insta · /bgmi · /ff\n"
        f"▸ /ai · /dns · /whois · /bin · /user\n"
        f"{LINE}\n"
        f"<b>🎮 Gᴀᴍᴇ</b>\n"
        f"▸ /spin — daily spin (VIP / refs)\n▸ /ping — real-time latency"
    )
    prem_extra = (
        f"\n{LINE}\n"
        f"<b>💎 Vɪᴘ Pᴇʀᴋꜱ</b>\n"
        f"▸ Extra credits & spin unlock\n"
        f"▸ Priority OSINT sources"
    )
    admin_extra = (
        f"\n{LINE}\n"
        f"<b>🛡 Aᴅᴍɪɴ</b>\n"
        f"▸ /admin — admin panel\n"
        f"▸ /status — API health\n"
        f"▸ /killdead — purge dead APIs\n"
        f"▸ /generate — temp merge API\n"
        f"▸ /cancel — stop running job"
    )
    owner_extra = (
        f"\n{LINE}\n"
        f"<b>👑 Oᴡɴᴇʀ</b>\n"
        f"▸ /owner — owner panel\n"
        f"▸ /extdb · /protect\n"
        f"▸ /addapi · /delapi · /listapi\n"
        f"▸ /status · /killdead · /generate\n"
        f"▸ /cancel — stop job"
    )

    body = free_cmds
    if role in ("premium", "admin", "owner"):
        body += prem_extra
    if role in ("admin", "owner"):
        body += admin_extra
    if role == "owner":
        body += owner_extra

    # Custom APIs (visible to all)
    try:
        customs = db_list_custom_apis() or []
    except Exception:
        customs = []
    # Filter system seeded + user custom — show short list
    custom_lines = []
    for r in customs[:40]:
        c = (r.get("cmd") if isinstance(r, dict) else r["cmd"]) if r else None
        if not c:
            continue
        if c in ("num","tg","adhr","family","fam","vech","vechrc","pan","upi","ifsc","name",
                 "ip","pin","git","insta","bgmi","ff","ai","dns","whois","bin","user"):
            continue
        custom_lines.append(f"▸ /{c}")
    if custom_lines:
        body += f"\n{LINE}\n<b>🔌 Cᴜꜱᴛᴏᴍ Aᴘɪꜱ</b>\n" + "\n".join(custom_lines[:25])

    role_badge = {
        "free": "🆓 Fʀᴇᴇ",
        "premium": "💎 Vɪᴘ",
        "admin": "🛡 Aᴅᴍɪɴ",
        "owner": "👑 Oᴡɴᴇʀ",
    }.get(role, role)

    txt = qblocks(
        f"<b>📋 ᴄᴏᴍᴍᴀɴᴅ ʟɪꜱᴛ</b> · {role_badge}\n{LINE}",
        body,
        f"👨‍💻 <b>Dᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}")
    kb = user_menu_kb(uid) if is_dm(update) else None
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb,
                                    disable_web_page_preview=True)

async def callback_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    qq = update.callback_query; await qq.answer()
    data = qq.data; uid = qq.from_user.id

    if qq.message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    if data == "fj:check":
        if await check_fj(ctx.bot, uid):
            try: await qq.message.delete()
            except: pass
            await send_main_card(qq.message.chat, uid)
        else:
            await qq.answer("❌ ᴋᴜᴄʜ ᴄʜᴀɴɴᴇʟꜱ ᴍɪꜱꜱɪɴɢ.", show_alert=True)
        return

    if data == "menu:home":
        try: await qq.message.delete()
        except: pass
        await send_main_card(qq.message.chat, uid)
        return

    if data == "menu:lookup":
        try: await qq.message.delete()
        except: pass
        await qq.message.chat.send_message(
            qblocks(f"<b>🔍 ᴏꜱɪɴᴛ ʟᴏᴏᴋᴜᴘ</b>\n{LINE}", "ᴋᴀᴜɴꜱᴀ ʟᴏᴏᴋᴜᴘ ᴄʜᴀʜɪʏᴇ?"),
            reply_markup=lookup_reply_kb(), parse_mode=ParseMode.HTML); return

    if data == "menu:profile": await profile_cmd(update, ctx); return
    if data == "menu:refer":   await refer_cmd(update, ctx);   return
    if data == "menu:premium": await premium_cmd(update, ctx); return
    if data == "menu:help":
        await qq.message.edit_text(
            qblocks(f"<b>❓ ʜᴇʟᴘ</b>\n{LINE}", "ᴜꜱᴇ /help ꜰᴏʀ ꜰᴜʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ"),
            reply_markup=InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:home")]]),
            parse_mode=ParseMode.HTML); return

    if data == "menu:history":
        rows = db_get_history(uid, limit=500)
        if not rows:
            await qq.message.edit_text(
                qblocks(f"<b>📜 ʜɪꜱᴛᴏʀʏ</b>\n{LINE}", "ɴᴏ ʟᴏᴏᴋᴜᴘꜱ ʏᴇᴛ."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:home")]]),
                parse_mode=ParseMode.HTML)
            return
        fname = build_history_file(rows, uid)
        await qq.message.reply_document(
            document=open(fname, "rb"),
            caption=qblocks(
                f"<b>📜 ʏᴏᴜʀ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
                f"▸ ᴛᴏᴛᴀʟ ʟᴏɢꜱ : <b>{len(rows)}</b>\n{LINE}",
                dev_signature_txt()),
            parse_mode=ParseMode.HTML)
        try: os.remove(fname)
        except: pass
        return

    if data == "menu:admin":
        if not is_admin(uid): await qq.answer("❌ Admin only", show_alert=True); return
        try: await qq.message.delete()
        except: pass
        await send_admin_panel(qq.message.chat, uid)
        return
    if data == "menu:owner":
        if not is_owner(uid): await qq.answer("❌ Owner only", show_alert=True); return
        try: await qq.message.delete()
        except: pass
        await send_owner_panel(qq.message.chat, uid)
        return

    if data.startswith("ask:"):
        cmd = data.split(":",1)[1]
        ctx.user_data["state"] = ("awaiting_lookup", cmd)
        await qq.message.edit_text(
            qblocks(f"<b>✍ ɪɴᴘᴜᴛ ʀᴇQᴜɪʀᴇᴅ</b>\n{LINE}", f"Send value for <b>/{cmd}</b>"),
            reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:lookup")]]),
            parse_mode=ParseMode.HTML); return

    # GENERATE API flow (admin/owner)
    if data.startswith("gen:"):
        if not (is_owner(uid) or is_admin(uid)):
            await qq.answer("❌ Admin only", show_alert=True); return
        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""
        if action == "close":
            try:
                await qq.message.delete()
            except Exception:
                pass
            return
        if action == "back":
            await qq.message.edit_text(
                qblocks(
                    f"<b>🧬 ɢᴇɴᴇʀᴀᴛᴇ ᴀᴘɪ</b>\n{LINE}",
                    "Kaunsi API type chahiye?\n"
                    "Bot saari sources merge karke\n"
                    "<b>kittu-osint</b> temp key banayega."),
                reply_markup=_gen_api_buttons(),
                parse_mode=ParseMode.HTML)
            return
        if action == "cmd" and len(parts) >= 3:
            cmd = parts[2]
            await qq.message.edit_text(
                qblocks(
                    f"<b>⏱ ᴅᴜʀᴀᴛɪᴏɴ</b>\n{LINE}",
                    f"API: <code>/{cmd}</code>\n"
                    f"Kitne time ke liye banana hai?"),
                reply_markup=_gen_duration_buttons(cmd),
                parse_mode=ParseMode.HTML)
            return
        if action == "dur" and len(parts) >= 4:
            cmd = parts[2]
            label = parts[3]
            hours_map = {lab: hrs for lab, hrs in _GEN_DURATIONS}
            hours = hours_map.get(label)
            if not hours:
                await qq.answer("Invalid duration", show_alert=True); return
            await qq.message.edit_text(
                qblocks(f"<b>🧬 ɢᴇɴᴇʀᴀᴛɪɴɢ…</b>\n{LINE}",
                        f"<code>/{cmd}</code> · {label}\nMerging sources…"),
                parse_mode=ParseMode.HTML)
            try:
                await _do_generate(uid, cmd, label, hours, qq.message)
            except Exception as e:
                try:
                    await qq.message.edit_text(f"❌ generate failed: {e}")
                except Exception:
                    pass
            return
        return

    # ADMIN
    if data.startswith("a:"):
        if not is_admin(uid): await qq.answer("❌ Admin only", show_alert=True); return
        sub = data[2:]
        if sub == "stats":
            s = db_stats()
            await qq.message.edit_text(
                qblocks(
                    f"<b>📊 ʙᴏᴛ ꜱᴛᴀᴛꜱ</b>\n{LINE}",
                    f"▸ ᴜꜱᴇʀꜱ    : <b>{s['users']}</b>\n"
                    f"▸ ᴠɪᴘ  : <b>{s['premium']}</b>\n"
                    f"▸ ᴀᴅᴍɪɴꜱ  : <b>{s['admins']}</b>\n"
                    f"▸ ᴠᴇʀɪꜰɪᴇᴅ : <b>{s['verified']}</b>\n"
                    f"▸ ᴄᴏɴᴛᴀᴄᴛꜱ: <b>{s['contacts']}</b>\n"
                    f"▸ ᴀᴄᴛɪᴠᴇ  : <b>{s['active']}</b>\n"
                    f"▸ ʟᴏɢꜱ    : <b>{s['logs']}</b>\n{LINE}",
                    f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:admin")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "history":
            ctx.user_data["state"] = ("history_user", "admin")
            await qq.message.edit_text(
                qblocks(f"<b>📜 ᴜꜱᴇʀ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
                        "Send <b>user_id</b> to fetch.\n"
                        "Or send <code>all</code> for all users."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:admin")]]),
                parse_mode=ParseMode.HTML)
            return
        if sub == "cred_add":
            ctx.user_data["state"] = ("cred_add_ids", None)
            await qq.message.edit_text(
                qblocks(f"<b>💰 ᴄʀᴇᴅɪᴛ ᴀᴅᴅ</b>\n{LINE}",
                        "Send user IDs (comma/space separated)."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:admin")]]),
                parse_mode=ParseMode.HTML)
            return
        if sub == "cred_rm":
            ctx.user_data["state"] = ("cred_rm_ids", None)
            await qq.message.edit_text(
                qblocks(f"<b>🗑 ᴄʀᴇᴅɪᴛ ʀᴇᴍᴏᴠᴇ</b>\n{LINE}",
                        "Send user IDs (comma/space separated)."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:admin")]]),
                parse_mode=ParseMode.HTML)
            return
        if sub == "api_check":
            m = await qq.message.edit_text(qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ</b>\n{LINE}",
                "ᴛᴇꜱᴛɪɴɢ ᴀᴘɪꜱ…"), parse_mode=ParseMode.HTML)
            res = await check_all_apis()
            ok_n = sum(1 for v in res.values() if v[0])
            body = [f"{'✅' if ok else '❌'} <code>{n:8}</code> · {st} · {ms}ms"
                    for n,(ok,st,ms) in sorted(res.items())]
            await m.edit_text(
                qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ</b>\n{LINE}",
                        f"<b>{ok_n}/{len(res)}</b> ᴡᴏʀᴋɪɴɢ\n{LINE}",
                        "<pre>" + "\n".join(body) + "</pre>"),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [B("🔁 ʀᴇᴄʜᴇᴄᴋ", cb="a:api_check")],
                    [B("⬅ ʙᴀᴄᴋ", cb="menu:admin")]]))
            return
        if sub == "prem_add":
            ctx.user_data["state"] = ("prem_add", None)
            await qq.message.edit_text(qblocks(f"<b>💎 ᴀᴅᴅ ᴠɪᴘ</b>\n{LINE}", "Send IDs:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:admin")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "prem_rm":
            ctx.user_data["state"] = ("prem_rm", None)
            await qq.message.edit_text(qblocks(f"<b>🗑 ʀᴇᴍᴏᴠᴇ ᴠɪᴘ</b>\n{LINE}", "Send IDs:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:admin")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "prem_list":
            us = db_list_users(only_premium=True)
            body = "\n".join(f"• <code>{u['user_id']}</code> — {u['first_name'] or ''}" for u in us) or "None"
            await qq.message.edit_text(
                qblocks(f"<b>💎 ᴠɪᴘ ᴜꜱᴇʀꜱ</b>\n{LINE}", f"<pre>{body[:3500]}</pre>"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:admin")]]),
                parse_mode=ParseMode.HTML); return

    # OWNER
    if data.startswith("o:"):
        if not is_owner(uid): await qq.answer("❌ Owner only", show_alert=True); return
        sub = data[2:]

        if sub == "gstats":
            users = db_all_user_ids()
            fname = f"users_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
            with open(fname, "w") as f: f.write("\n".join(str(u) for u in users))
            s = db_stats()
            storage = format_storage_stats_html()
            await qq.message.reply_document(document=open(fname, "rb"),
                caption=qblocks(
                    f"<b>👑 Gʟᴏʙᴀʟ Sᴛᴀᴛꜱ</b>\n{LINE}",
                    f"▸ Tᴏᴛᴀʟ     : <b>{s['users']}</b>\n"
                    f"▸ Vɪᴘ       : <b>{s['premium']}</b>\n"
                    f"▸ Aᴅᴍɪɴꜱ    : <b>{s['admins']}</b>\n"
                    f"▸ Vᴇʀɪꜰɪᴇᴅ  : <b>{s['verified']}</b>\n"
                    f"▸ Cᴏɴᴛᴀᴄᴛꜱ  : <b>{s['contacts']}</b>\n"
                    f"▸ Lᴏɢꜱ      : <b>{s['logs']}</b>\n{LINE}\n"
                    f"{storage}"),
                parse_mode=ParseMode.HTML)
            try: os.remove(fname)
            except: pass
            return

        if sub == "getdb":
            m = await qq.message.edit_text(qblocks(f"<b>📦 ᴅʙ ᴇxᴘᴏʀᴛ</b>\n{LINE}",
                "ᴘᴀᴄᴋɪɴɢ…"), parse_mode=ParseMode.HTML)
            try:
                ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                path = f"db_export_{ts}.zip"
                with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as a: a.write(DB_PATH, arcname="bot_data.db")
                mb = os.path.getsize(path)/(1024*1024); dbmb = db_size_bytes()/(1024*1024)
                cnt = db_contacts_count()
                await qq.message.reply_document(document=open(path, "rb"),
                    caption=qblocks(
                        f"<b>📦 ᴅʙ ᴇxᴘᴏʀᴛ</b>\n{LINE}",
                        f"▸ ᴅʙ ꜱɪᴢᴇ  : {dbmb:.1f} MB\n"
                        f"▸ ᴢɪᴘ ꜱɪᴢᴇ : {mb:.1f} MB\n"
                        f"▸ ᴄᴏɴᴛᴀᴄᴛꜱ: {cnt}\n{LINE}",
                        f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                    parse_mode=ParseMode.HTML)
                try: os.remove(path)
                except: pass
                await m.delete()
            except Exception as e: await m.edit_text(f"❌ {e}")
            return

        if sub == "broadcast":
            ctx.user_data["state"] = ("broadcast", None)
            await qq.message.edit_text(
                qblocks(f"<b>📢 ʙʀᴏᴀᴅᴄᴀꜱᴛ</b>\n{LINE}",
                        "Send the message you want to broadcast.\n"
                        "Any type allowed — text / photo / video / gif / sticker.\n"
                        f"{LINE}\n<i>Sender name hidden rahega.</i>"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML)
            return

        if sub == "history":
            ctx.user_data["state"] = ("history_user", "owner")
            await qq.message.edit_text(
                qblocks(f"<b>📜 ɢʟᴏʙᴀʟ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
                        "Send <b>user_id</b> for specific user.\n"
                        "Or send <code>all</code> for all users."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML)
            return
        if sub == "cred_add":
            ctx.user_data["state"] = ("cred_add_ids", None)
            await qq.message.edit_text(
                qblocks(f"<b>💰 ᴄʀᴇᴅɪᴛ ᴀᴅᴅ</b>\n{LINE}",
                        "Send user IDs (comma/space separated)."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML)
            return
        if sub == "cred_rm":
            ctx.user_data["state"] = ("cred_rm_ids", None)
            await qq.message.edit_text(
                qblocks(f"<b>🗑 ᴄʀᴇᴅɪᴛ ʀᴇᴍᴏᴠᴇ</b>\n{LINE}",
                        "Send user IDs (comma/space separated)."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML)
            return

        if sub == "api_mgr":
            await qq.message.edit_text(
                qblocks(f"<b>🔌 ᴀᴘɪ ᴍᴀɴᴀɢᴇʀ</b>\n{LINE}", "ᴄᴜꜱᴛᴏᴍ ᴀᴘɪꜱ ᴍᴀɴᴀɢᴇ ᴋᴀʀᴏ."),
                reply_markup=api_panel_kb(), parse_mode=ParseMode.HTML); return

        if sub == "api_add":
            ctx.user_data["state"] = ("api_add", None)
            await qq.message.edit_text(
                qblocks(f"<b>➕ ᴀᴅᴅ ᴄᴜꜱᴛᴏᴍ ᴀᴘɪ</b>\n{LINE}",
                        "Send a <b>.txt</b> file.\n"
                        f"{LINE}\n<b>Format per line:</b>\n"
                        "<code>cmd|title|usage|url1,url2</code>\n"
                        f"{LINE}\n"
                        "<i>Existing commands safe rahenge — sirf naye add honge.</i>"),
                reply_markup=InlineKeyboardMarkup([
                    [B("📄 ɢᴇᴛ ᴛᴇᴍᴘʟᴀᴛᴇ", cb="o:api_tpl")],
                    [B("⬅ ᴄᴀɴᴄᴇʟ", cb="o:api_mgr")]]),
                parse_mode=ParseMode.HTML); return

        if sub == "api_tpl":
            tpl = (
                "# Custom OSINT APIs — Template\n"
                "# Format: cmd|title|usage|url1,url2,url3\n"
                "# cmd = alphanumeric, no slash\n"
                "# urls = comma-separated, use {value} placeholder\n"
                "# Lines starting with # ignored.\n"
                "\n"
                "customnum|📱 ᴄᴜꜱᴛᴏᴍ ɴᴜᴍ ʟᴏᴏᴋᴜᴘ|/customnum <num>|https://api1.com/lookup?n={value}\n"
            )
            fname = "api_template.txt"
            with open(fname, "w", encoding="utf-8") as f: f.write(tpl)
            await qq.message.reply_document(
                document=open(fname, "rb"),
                caption=qblocks(f"<b>📄 ᴄᴜꜱᴛᴏᴍ ᴀᴘɪ ᴛᴇᴍᴘʟᴀᴛᴇ</b>\n{LINE}",
                                "Edit and send back to add APIs."),
                parse_mode=ParseMode.HTML)
            try: os.remove(fname)
            except: pass
            return

        if sub == "api_del":
            ctx.user_data["state"] = ("api_del", None)
            await qq.message.edit_text(
                qblocks(f"<b>🗑 ᴅᴇʟᴇᴛᴇ ᴄᴜꜱᴛᴏᴍ ᴀᴘɪ</b>\n{LINE}",
                        "Send <b>command name(s)</b> (no slash)."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="o:api_mgr")]]),
                parse_mode=ParseMode.HTML); return

        if sub == "api_list":
            rows = db_list_custom_apis()
            if not rows:
                body = "ɴᴏ ᴄᴜꜱᴛᴏᴍ ᴀᴘɪꜱ."
            else:
                chunks = []
                for r in rows:
                    us = json.loads(r["urls"])
                    line = f"▸ <code>/{r['cmd']}</code> — {r['title']}\n"
                    for u in us: line += f"   · <code>{u}</code>\n"
                    line += f"   <i>{r['added_at']}</i>"
                    chunks.append(line)
                body = "\n\n".join(chunks)
            await qq.message.edit_text(
                qblocks(f"<b>📋 ᴄᴜꜱᴛᴏᴍ ᴀᴘɪꜱ ({len(rows)})</b>\n{LINE}", body[:3500]),
                reply_markup=InlineKeyboardMarkup([
                    [B("➕ ᴀᴅᴅ", cb="o:api_add"), B("🗑 ᴅᴇʟ", cb="o:api_del")],
                    [B("⬅ ʙᴀᴄᴋ", cb="o:api_mgr")]]),
                parse_mode=ParseMode.HTML); return

        if sub == "api_check":
            m = await qq.message.edit_text(qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ</b>\n{LINE}",
                "ᴛᴇꜱᴛɪɴɢ…"), parse_mode=ParseMode.HTML)
            res = await check_all_apis()
            ok_n = sum(1 for v in res.values() if v[0])
            body = [f"{'✅' if ok else '❌'} <code>{n:8}</code> · {st} · {ms}ms"
                    for n,(ok,st,ms) in sorted(res.items())]
            await m.edit_text(
                qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ</b>\n{LINE}",
                        f"<b>{ok_n}/{len(res)}</b> ᴡᴏʀᴋɪɴɢ\n{LINE}",
                        "<pre>" + "\n".join(body) + "</pre>"),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [B("🔁 ʀᴇᴄʜᴇᴄᴋ", cb="o:api_check")],
                    [B("⬅ ʙᴀᴄᴋ", cb="menu:owner")]]))
            return

        if sub == "adm_add":
            ctx.user_data["state"] = ("adm_add", None)
            await qq.message.edit_text(qblocks(f"<b>🛡 ᴀᴅᴅ ᴀᴅᴍɪɴ</b>\n{LINE}", "Send IDs:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "adm_rm":
            ctx.user_data["state"] = ("adm_rm", None)
            await qq.message.edit_text(qblocks(f"<b>🗑 ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ</b>\n{LINE}", "Send IDs:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "adm_list":
            us = db_list_users(only_admin=True)
            body = "\n".join(f"• <code>{u['user_id']}</code> — {u['first_name'] or ''}" for u in us) or "None"
            await qq.message.edit_text(
                qblocks(f"<b>🛡 ᴀᴅᴍɪɴꜱ</b>\n{LINE}", f"<pre>{body[:3500]}</pre>"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "prem_add":
            ctx.user_data["state"] = ("prem_add", None)
            await qq.message.edit_text(qblocks(f"<b>💎 ᴀᴅᴅ ᴠɪᴘ</b>\n{LINE}", "Send IDs:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "prem_rm":
            ctx.user_data["state"] = ("prem_rm", None)
            await qq.message.edit_text(qblocks(f"<b>🗑 ʀᴇᴍᴏᴠᴇ ᴠɪᴘ</b>\n{LINE}", "Send IDs:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "prem_list":
            us = db_list_users(only_premium=True)
            body = "\n".join(f"• <code>{u['user_id']}</code> — {u['first_name'] or ''}" for u in us) or "None"
            await qq.message.edit_text(
                qblocks(f"<b>💎 ᴠɪᴘ ᴜꜱᴇʀꜱ</b>\n{LINE}", f"<pre>{body[:3500]}</pre>"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "wlc_text":
            ctx.user_data["state"] = ("wlc_text", None)
            await qq.message.edit_text(qblocks(f"<b>✏ ꜱᴇᴛ ᴡʟᴄ ᴛᴇxᴛ</b>\n{LINE}", "Send welcome text:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "wlc_media":
            ctx.user_data["state"] = ("wlc_media", None)
            await qq.message.edit_text(qblocks(f"<b>🖼 ꜱᴇᴛ ᴡʟᴄ ᴍᴇᴅɪᴀ</b>\n{LINE}", "Send photo/video/GIF:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="menu:owner")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "chnl":
            await qq.message.edit_text(qblocks(f"<b>📢 ᴄʜᴀɴɴᴇʟ ᴍɢᴍᴛ</b>\n{LINE}", "ᴍᴀɴᴀɢᴇ ᴄʜᴀɴɴᴇʟꜱ."),
                reply_markup=channel_panel_kb(), parse_mode=ParseMode.HTML); return
        if sub == "chnl_add":
            ctx.user_data["state"] = ("chnl_add", None)
            await qq.message.edit_text(qblocks(f"<b>➕ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ</b>\n{LINE}", "Public: <code>@channel</code>\nPrivate: invite link <code>https://t.me/+xxx</code>\nOr chat id <code>-100...</code>\nBot must be Admin."),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="o:chnl")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "chnl_rm":
            ctx.user_data["state"] = ("chnl_rm", None)
            await qq.message.edit_text(qblocks(f"<b>🗑 ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ</b>\n{LINE}", "Send chat_id:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="o:chnl")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "chnl_list":
            chs = db_list_channels()
            body = "\n".join(f"• <code>{c['chat_id']}</code> — {c['title'] or ''} ({'🔒' if c['is_private'] else '🌐'})" for c in chs) or "None"
            await qq.message.edit_text(
                qblocks(f"<b>📢 ᴄʜᴀɴɴᴇʟꜱ</b>\n{LINE}", f"<pre>{body[:3500]}</pre>"),
                reply_markup=channel_panel_kb(), parse_mode=ParseMode.HTML); return
        if sub == "gc":
            await qq.message.edit_text(qblocks(f"<b>👥 ɢʀᴏᴜᴘ ᴍɢᴍᴛ</b>\n{LINE}", "ᴍᴀɴᴀɢᴇ ɢʀᴏᴜᴘꜱ."),
                reply_markup=gc_panel_kb(), parse_mode=ParseMode.HTML); return
        if sub == "gc_add":
            ctx.user_data["state"] = ("gc_add", None)
            await qq.message.edit_text(qblocks(f"<b>➕ ᴀᴅᴅ ɢʀᴏᴜᴘ</b>\n{LINE}", "Send group chat_id:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="o:gc")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "gc_rm":
            ctx.user_data["state"] = ("gc_rm", None)
            await qq.message.edit_text(qblocks(f"<b>🗑 ʀᴇᴍᴏᴠᴇ ɢʀᴏᴜᴘ</b>\n{LINE}", "Send chat_id:"),
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄᴀɴᴄᴇʟ", cb="o:gc")]]),
                parse_mode=ParseMode.HTML); return
        if sub == "gc_list":
            gs = db_list_groups()
            body = "\n".join(f"• <code>{g['chat_id']}</code> — {g['title'] or ''}" for g in gs) or "None"
            await qq.message.edit_text(
                qblocks(f"<b>👥 ᴡʜɪᴛᴇʟɪꜱᴛᴇᴅ ɢʀᴏᴜᴘꜱ</b>\n{LINE}", f"<pre>{body[:3500]}</pre>"),
                reply_markup=gc_panel_kb(), parse_mode=ParseMode.HTML); return

# ============================================================
#  CONTACT HANDLER
# ============================================================
async def contact_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.contact: return
    # Verification only in DM, only once
    if is_gc(update):
        try: await msg.delete()
        except: pass
        return
    u = update.effective_user
    c = msg.contact
    existing = db_get_user(u.id)
    was_verified = bool(existing and existing["verified"])
    tg_uid = c.user_id if c.user_id else u.id
    db_save_contact(u.id, tg_uid, c.phone_number, c.first_name or "", c.last_name or "")
    if is_owner(u.id):
        protect_add_phone(c.phone_number)
        protect_add_tg(tg_uid)
        protect_add_tg(u.id)
    # Delete user's contact share message instantly
    try: await msg.delete()
    except: pass
    # Delete bot's verification prompt if tracked
    vid = ctx.user_data.pop("verify_msg_id", None)
    if vid:
        try: await ctx.bot.delete_message(chat_id=update.effective_chat.id, message_id=vid)
        except: pass
    # Already verified → silent (no re-verify flow)
    if was_verified:
        asyncio.create_task(auto_db_export(ctx.bot))
        return
    # Brief verified flash then delete
    tmp = await update.effective_chat.send_message(
        qblocks(f"<b>✅ Vᴇʀɪꜰɪᴇᴅ!</b>\n{LINE}",
                f"📱 <code>{c.phone_number}</code>"),
        reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
    await asyncio.sleep(0.4)
    try: await tmp.delete()
    except: pass
    if not await check_fj(ctx.bot, u.id):
        await send_fj(update.effective_chat, ctx); return
    await send_main_card(update.effective_chat, u.id)
    asyncio.create_task(auto_db_export(ctx.bot))

async def auto_db_export(bot):
    try:
        if db_size_bytes() >= DB_EXPORT_THRESHOLD and OWNER_ID:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            path = f"auto_db_{ts}.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as a: a.write(DB_PATH, arcname="bot_data.db")
            mb = os.path.getsize(path)/(1024*1024)
            await bot.send_document(chat_id=OWNER_ID, document=open(path, "rb"),
                caption=qblocks(f"<b>🚨 ᴀᴜᴛᴏ ᴅʙ ʙᴀᴄᴋᴜᴘ</b>\n{LINE}",
                                f"ᴅʙ 1ɢʙ ᴄʀᴏꜱꜱ!\nᴢɪᴘ ꜱɪᴢᴇ: {mb:.1f} ᴍʙ\n{LINE}",
                                f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                parse_mode=ParseMode.HTML)
            try: os.remove(path)
            except: pass
    except Exception as e: log.warning(f"auto_db_export: {e}")

# ============================================================
#  TEXT BUTTON ROUTER  (bottom reply keyboard)
# ============================================================
async def text_button_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_gc(update):
        return
    """All bottom buttons → actions. No mid-screen menus."""
    msg = update.message
    if not msg or not msg.text: return
    # Active multi-step state (prem add, credits, etc.) → state_handler
    if ctx.user_data.get("state"):
        await state_handler(update, ctx)
        return
    text = msg.text.strip()
    uid = update.effective_user.id
    chat = update.effective_chat

    # ---- MAIN ----
    if text == BTN_OSINT:
        await msg.reply_text(
            qblocks(f"<b>🔍 ᴏꜱɪɴᴛ ʟᴏᴏᴋᴜᴘ</b>\n{LINE}", "ᴋᴀᴜɴꜱᴀ ʟᴏᴏᴋᴜᴘ ᴄʜᴀʜɪʏᴇ?"),
            reply_markup=lookup_reply_kb(), parse_mode=ParseMode.HTML)
        return
    # If user typed a bare command name (no /), guide them once instead of ignoring
    low = text.lower().lstrip("/")
    bare = low.split()[0] if low else ""
    if bare and bare in ("num", "tg", "adhr", "family", "fam", "vech", "vechrc", "pan", "upi",
                         "ifsc", "name", "ip", "pin", "git", "insta", "bgmi", "ff", "ai",
                         "dns", "whois", "bin", "user", "osint", "cancel", "extdb"):
        await msg.reply_text(
            qblocks(
                f"<b>ℹ ᴜꜱᴇ ꜱʟᴀꜱʜ ᴄᴏᴍᴍᴀɴᴅ</b>\n{LINE}",
                f"Type: <code>/{bare} {' '.join(text.split()[1:]) if len(text.split())>1 else '<value>'}</code>\n"
                f"Ya menu se button dabao.\n"
                f"Cancel running: <code>/cancel</code>"),
            parse_mode=ParseMode.HTML)
        return
    if text == BTN_PROFILE:
        await profile_cmd(update, ctx); return
    if text == BTN_REFER:
        await refer_cmd(update, ctx); return
    if text == BTN_HISTORY:
        rows = db_get_history(uid, limit=500)
        if not rows:
            await msg.reply_text(qblocks(f"<b>📜 ʜɪꜱᴛᴏʀʏ</b>\n{LINE}", "ɴᴏ ʟᴏᴏᴋᴜᴘꜱ ʏᴇᴛ."), parse_mode=ParseMode.HTML)
            return
        fname = build_history_file(rows, uid)
        await msg.reply_document(document=open(fname, "rb"),
            caption=qblocks(f"<b>📜 ʏᴏᴜʀ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}", f"▸ ᴛᴏᴛᴀʟ ʟᴏɢꜱ : <b>{len(rows)}</b>\n{LINE}", dev_signature_txt()),
            parse_mode=ParseMode.HTML)
        try: os.remove(fname)
        except: pass
        return
    if text == BTN_PREMIUM:
        await premium_cmd(update, ctx); return
    if text == BTN_HELP:
        await help_cmd(update, ctx); return
    if text == "🎰 Sᴘɪɴ":
        await spin_cmd(update, ctx); return
    if text == BTN_ADMIN:
        if not is_admin(uid):
            await msg.reply_text("❌ Admin only."); return
        await send_admin_panel(chat, uid); return
    if text == BTN_OWNER:
        if not is_owner(uid):
            await msg.reply_text("❌ Owner only."); return
        await send_owner_panel(chat, uid); return
    if text == BTN_BACK_HOME:
        await send_main_card(chat, uid); return

    # ---- LOOKUP TOOLS ----
    lookup_map = {
        BTN_TG: "tg", BTN_NUM: "num", BTN_ADHR: "adhr", BTN_FAM: "family",
        BTN_VECH: "vech", BTN_RCRC: "vechrc", BTN_PAN: "pan", BTN_UPI: "upi",
        BTN_IFSC: "ifsc", BTN_NAME: "name", BTN_IP: "ip", BTN_PIN: "pin",
        BTN_GIT: "git", BTN_INSTA: "insta", BTN_BGMI: "bgmi", BTN_FF: "ff",
        BTN_AI: "ai", BTN_DNS: "dns", BTN_WHOIS: "whois", BTN_BIN: "bin", BTN_USER: "user",
    }
    if text in lookup_map:
        cmd = lookup_map[text]
        ctx.user_data["state"] = ("awaiting_lookup", cmd)
        await msg.reply_text(
            qblocks(f"<b>✍ ɪɴᴘᴜᴛ ʀᴇQᴜɪʀᴇᴅ</b>\n{LINE}", f"Send value for <b>/{cmd}</b>"),
            parse_mode=ParseMode.HTML)
        return

    # ---- ADMIN ----
    if text == BTN_A_STATS and is_admin(uid):
        s = db_stats()
        storage = format_storage_stats_html()
        await msg.reply_text(qblocks(f"<b>📊 Sᴛᴀᴛꜱ</b>\n{LINE}",
            f"▸ Tᴏᴛᴀʟ     : <b>{s['users']}</b>\n"
            f"▸ Vɪᴘ       : <b>{s['premium']}</b>\n"
            f"▸ Aᴅᴍɪɴꜱ    : <b>{s['admins']}</b>\n"
            f"▸ Vᴇʀɪꜰɪᴇᴅ  : <b>{s['verified']}</b>\n"
            f"▸ Cᴏɴᴛᴀᴄᴛꜱ  : <b>{s['contacts']}</b>\n"
            f"▸ Lᴏɢꜱ      : <b>{s['logs']}</b>\n{LINE}\n"
            f"{storage}"),
            parse_mode=ParseMode.HTML); return
    if text == BTN_A_HIST and is_admin(uid):
        ctx.user_data["state"] = ("history_user", "admin")
        await msg.reply_text(qblocks(f"<b>📜 ʜɪꜱᴛᴏʀʏ</b>\n{LINE}", "Send user_id or <code>all</code>:"), parse_mode=ParseMode.HTML); return
    if text == BTN_A_CREDADD and is_admin(uid):
        ctx.user_data["state"] = ("cred_add_ids", None)
        await msg.reply_text(qblocks(f"<b>💰 ᴄʀᴇᴅɪᴛ +</b>\n{LINE}", "Send user IDs:"), parse_mode=ParseMode.HTML); return
    if text == BTN_A_CREDRM and is_admin(uid):
        ctx.user_data["state"] = ("cred_rm_ids", None)
        await msg.reply_text(qblocks(f"<b>🗑 ᴄʀᴇᴅɪᴛ -</b>\n{LINE}", "Send user IDs:"), parse_mode=ParseMode.HTML); return
    if text == BTN_A_PREMADD and is_admin(uid):
        ctx.user_data["state"] = ("prem_add", None)
        await msg.reply_text(qblocks(f"<b>💎 ᴘʀᴇᴍ +</b>\n{LINE}", "Send user_id:"), parse_mode=ParseMode.HTML); return
    if text == BTN_A_PREMRM and is_admin(uid):
        ctx.user_data["state"] = ("prem_rm", None)
        await msg.reply_text(qblocks(f"<b>🗑 ᴘʀᴇᴍ -</b>\n{LINE}", "Send user_id:"), parse_mode=ParseMode.HTML); return
    if text == BTN_A_PREMLIST and is_admin(uid):
        us = db_list_users(only_premium=True)
        body = "\n".join(f"• <code>{u['user_id']}</code> — {u['first_name'] or ''}" for u in us) or "None"
        await msg.reply_text(qblocks(f"<b>💎 ᴠɪᴘ</b>\n{LINE}", f"<pre>{body[:3500]}</pre>"), parse_mode=ParseMode.HTML); return
    if text == BTN_A_API and is_admin(uid):
        await msg.reply_text(qblocks(f"<b>🔌 ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ</b>\n{LINE}", "Use API Manager from Owner."), parse_mode=ParseMode.HTML); return

    # ---- OWNER ----
    if not is_owner(uid):
        return

    if text == BTN_O_GSTATS:
        users = db_all_user_ids()
        fname = f"users_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
        with open(fname, "w") as f: f.write("\n".join(str(u) for u in users))
        s = db_stats()
        storage = format_storage_stats_html()
        await msg.reply_document(document=open(fname, "rb"),
            caption=qblocks(f"<b>👑 Gʟᴏʙᴀʟ Sᴛᴀᴛꜱ</b>\n{LINE}",
                f"▸ Tᴏᴛᴀʟ     : <b>{s['users']}</b>\n"
                f"▸ Vɪᴘ       : <b>{s['premium']}</b>\n"
                f"▸ Aᴅᴍɪɴꜱ    : <b>{s['admins']}</b>\n"
                f"▸ Vᴇʀɪꜰɪᴇᴅ  : <b>{s['verified']}</b>\n"
                f"▸ Cᴏɴᴛᴀᴄᴛꜱ  : <b>{s['contacts']}</b>\n"
                f"▸ Lᴏɢꜱ      : <b>{s['logs']}</b>\n{LINE}\n"
                f"{storage}"),
            parse_mode=ParseMode.HTML)
        try: os.remove(fname)
        except: pass
        return
    if text == BTN_O_EXTDB:
        info = external_db_info()
        body = (
            f"▸ Path: <code>{info.get('path') or 'not set'}</code>\n"
            f"▸ Status: <b>{'✅ online' if info.get('ok') else '❌ offline'}</b>\n"
            f"▸ Tables: <b>{info.get('tables', 0)}</b>\n"
            f"▸ Rows≈ <b>{info.get('rows', 0)}</b>\n"
            f"{LINE}\n"
            "Send a <b>.db / .sqlite</b> file to load\n"
            "OR send full file path as text."
        )
        ctx.user_data["state"] = ("extdb_set", None)
        await msg.reply_text(qblocks(f"<b>🗄 ᴇxᴛᴇʀɴᴀʟ ᴅʙ</b>\n{LINE}", body),
            parse_mode=ParseMode.HTML); return
    if text == BTN_O_GETDB:
        m = await msg.reply_text(qblocks(f"<b>📦 ᴅʙ ᴇxᴘᴏʀᴛ</b>\n{LINE}", "ᴘᴀᴄᴋɪɴɢ…"), parse_mode=ParseMode.HTML)
        try:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            path = f"db_export_{ts}.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as a: a.write(DB_PATH, arcname="bot_data.db")
            mb = os.path.getsize(path)/(1024*1024); dbmb = db_size_bytes()/(1024*1024)
            cnt = db_contacts_count()
            await msg.reply_document(document=open(path, "rb"),
                caption=qblocks(f"<b>📦 ᴅʙ ᴇxᴘᴏʀᴛ</b>\n{LINE}",
                    f"▸ ᴅʙ ꜱɪᴢᴇ  : {dbmb:.1f} MB\n▸ ᴢɪᴘ ꜱɪᴢᴇ : {mb:.1f} MB\n▸ ᴄᴏɴᴛᴀᴄᴛꜱ: {cnt}\n{LINE}",
                    f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                parse_mode=ParseMode.HTML)
            try: os.remove(path)
            except: pass
            try: await m.delete()
            except: pass
        except Exception as e:
            await m.edit_text(f"❌ {e}")
        return
    if text == BTN_O_BCAST:
        ctx.user_data["state"] = ("broadcast", None)
        await msg.reply_text(qblocks(f"<b>📢 ʙʀᴏᴀᴅᴄᴀꜱᴛ</b>\n{LINE}",
            "Send the message to broadcast (any type).\nSender name hidden."),
            parse_mode=ParseMode.HTML); return
    if text == BTN_O_APIMGR:
        await msg.reply_text(qblocks(f"<b>🔌 ᴀᴘɪ ᴍᴀɴᴀɢᴇʀ</b>\n{LINE}", "ᴄᴜꜱᴛᴏᴍ ᴀᴘɪꜱ ᴍᴀɴᴀɢᴇ ᴋᴀʀᴏ."),
            reply_markup=api_panel_kb(), parse_mode=ParseMode.HTML); return
    if text == BTN_O_GHIST:
        ctx.user_data["state"] = ("history_user", "owner")
        await msg.reply_text(qblocks(f"<b>📜 ɢʟᴏʙᴀʟ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
            "Send user_id or <code>all</code>:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_CREDADD:
        ctx.user_data["state"] = ("cred_add_ids", None)
        await msg.reply_text(qblocks(f"<b>💰 ᴄʀᴇᴅɪᴛ +</b>\n{LINE}", "Send user IDs:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_CREDRM:
        ctx.user_data["state"] = ("cred_rm_ids", None)
        await msg.reply_text(qblocks(f"<b>🗑 ᴄʀᴇᴅɪᴛ -</b>\n{LINE}", "Send user IDs:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_ADMADD:
        ctx.user_data["state"] = ("adm_add", None)
        await msg.reply_text(qblocks(f"<b>🛡 ᴀᴅᴅ ᴀᴅᴍɪɴ</b>\n{LINE}", "Send user_id:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_ADMRM:
        ctx.user_data["state"] = ("adm_rm", None)
        await msg.reply_text(qblocks(f"<b>🗑 ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ</b>\n{LINE}", "Send user_id:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_ADMLIST:
        await msg.reply_text(qblocks(f"<b>📋 ᴀᴅᴍɪɴ ʟɪꜱᴛ</b>\n{LINE}", "Check DB /stats for list."), parse_mode=ParseMode.HTML); return
    if text == BTN_O_PREMADD:
        ctx.user_data["state"] = ("prem_add", None)
        await msg.reply_text(qblocks(f"<b>💎 ᴀᴅᴅ ᴠɪᴘ</b>\n{LINE}", "Send user_id:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_PREMRM:
        ctx.user_data["state"] = ("prem_rm", None)
        await msg.reply_text(qblocks(f"<b>🗑 ʀᴇᴍᴏᴠᴇ ᴠɪᴘ</b>\n{LINE}", "Send user_id:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_PREMLIST:
        us = db_list_users(only_premium=True)
        body = "\n".join(f"• <code>{u['user_id']}</code> — {u['first_name'] or ''}" for u in us) or "None"
        await msg.reply_text(qblocks(f"<b>💎 ᴠɪᴘ</b>\n{LINE}", f"<pre>{body[:3500]}</pre>"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_WLCTXT:
        ctx.user_data["state"] = ("wlc_text", None)
        await msg.reply_text(qblocks(f"<b>✏ ᴡᴇʟᴄᴏᴍᴇ ᴛᴇxᴛ</b>\n{LINE}", "Send new welcome text:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_WLCMED:
        ctx.user_data["state"] = ("wlc_media", None)
        await msg.reply_text(qblocks(f"<b>🖼 ᴡᴇʟᴄᴏᴍᴇ ᴍᴇᴅɪᴀ</b>\n{LINE}", "Send photo / video:"), parse_mode=ParseMode.HTML); return
    if text == BTN_O_CHNL:
        await msg.reply_text(qblocks(f"<b>📢 ᴄʜᴀɴɴᴇʟꜱ</b>\n{LINE}", "Manage force-join channels."),
            reply_markup=channel_panel_kb(), parse_mode=ParseMode.HTML); return
    if text == BTN_O_GC:
        await msg.reply_text(qblocks(f"<b>👥 ɢʀᴏᴜᴘꜱ</b>\n{LINE}", "Manage whitelist groups."),
            reply_markup=gc_panel_kb(), parse_mode=ParseMode.HTML); return

async def state_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    st = ctx.user_data.get("state")
    if not st: return
    name, extra = st
    msg = update.message
    if not msg: return
    uid = update.effective_user.id

    if name == "awaiting_lookup":
        cmd = extra
        ctx.user_data.pop("state", None)
        raw = (msg.text or "").strip()
        if not raw:
            await msg.reply_text(
                qblocks(f"<b>⚠ ᴜꜱᴀɢᴇ</b>\n{LINE}", f"Send a value for <code>/{cmd}</code>"),
                parse_mode=ParseMode.HTML)
            return
        ctx.args = raw.split()
        if cmd == "num":
            await num_cmd(update, ctx)
        elif cmd == "tg":
            await tg_cmd(update, ctx)
        elif cmd == "ai":
            await ai_cmd(update, ctx)
        else:
            title, usage, urls = resolve_api(cmd)
            if not urls and not title:
                await msg.reply_text(
                    qblocks(f"<b>❓ ᴜɴᴋɴᴏᴡɴ</b>\n{LINE}",
                            f"<code>/{cmd}</code> configured nahi hai."),
                    parse_mode=ParseMode.HTML)
                return
            await run_osint(update, ctx, title or cmd, urls or [], raw, cmd)
        return

    if name == "extdb_set":
        if not is_owner(uid):
            ctx.user_data.pop("state", None); return
        # document upload via Telegram
        if msg.document:
            try:
                fsize = int(msg.document.file_size or 0)
                if fsize > MAX_EXTERNAL_DB_BYTES:
                    await msg.reply_text(qblocks(f"<b>❌ Tᴏᴏ Lᴀʀɢᴇ</b>\n{LINE}",
                        f"Max <b>3 GB</b> per DB.\nYour file: <b>{fsize/1024/1024/1024:.2f} GB</b>"),
                        parse_mode=ParseMode.HTML); return
                if fsize > TG_BOT_FILE_LIMIT:
                    await msg.reply_text(qblocks(f"<b>⚠ Tᴇʟᴇɢʀᴀᴍ Lɪᴍɪᴛ</b>\n{LINE}",
                        f"Telegram bot download max ≈ <b>20 MB</b>.\n"
                        f"Your file: <b>{fsize/1024/1024:.1f} MB</b>\n\n"
                        f"VPS pe file rakh ke <b>full path</b> bhejo:\n"
                        f"<code>/extdb /path/to/file.db</code>\n\n"
                        f"Limit: <b>{MAX_EXTERNAL_DBS}</b> DBs × 3 GB each."),
                        parse_mode=ParseMode.HTML); return
                lst = _external_db_list()
                if len(lst) >= MAX_EXTERNAL_DBS:
                    await msg.reply_text(qblocks(f"<b>❌ Lɪᴍɪᴛ</b>\n{LINE}",
                        f"Max <b>{MAX_EXTERNAL_DBS}</b> external DBs already registered."),
                        parse_mode=ParseMode.HTML); return
                idx = len(lst) + 1
                dest = os.path.join(os.path.dirname(os.path.abspath(DB_PATH)) or ".", f"external_{idx}.db")
                f = await msg.document.get_file()
                await f.download_to_drive(dest)
                ok_reg, reg_msg = _external_db_register(dest)
                open_external_db(dest, force=True)
                info = external_db_info()
                ctx.user_data.pop("state", None)
                await msg.reply_text(qblocks(f"<b>{'✅' if ok_reg else '❌'} Exᴛᴇʀɴᴀʟ Dʙ</b>\n{LINE}",
                    f"{reg_msg}\nSaved: <code>{dest}</code>\n"
                    f"DBs: <b>{info.get('count',0)}/{MAX_EXTERNAL_DBS}</b>\n"
                    f"Tables: <b>{info.get('tables',0)}</b>  Rows≈ <b>{info.get('rows',0)}</b>"),
                    parse_mode=ParseMode.HTML)
            except Exception as e:
                await msg.reply_text(f"❌ {e}")
            return
        path = (msg.text or "").strip().strip('"').strip("'")
        if not path or not os.path.isfile(path):
            await msg.reply_text(qblocks(f"<b>❌</b>\n{LINE}",
                f"Valid .db path bhejo ya file upload karo.\n"
                f"Max: <b>{MAX_EXTERNAL_DBS}</b> DBs × <b>3 GB</b> each."),
                parse_mode=ParseMode.HTML); return
        ok_reg, reg_msg = _external_db_register(path)
        ok = open_external_db(path, force=True)
        info = external_db_info()
        ctx.user_data.pop("state", None)
        await msg.reply_text(qblocks(f"<b>{'✅' if ok_reg and ok else '❌'} Exᴛᴇʀɴᴀʟ Dʙ</b>\n{LINE}",
            f"{reg_msg}\nPath: <code>{path}</code>\n"
            f"DBs: <b>{info.get('count',0)}/{MAX_EXTERNAL_DBS}</b>\n"
            f"Tables: <b>{info.get('tables',0)}</b>  Rows≈ <b>{info.get('rows',0)}</b>"),
            parse_mode=ParseMode.HTML)
        return

    if name == "broadcast":
        ctx.user_data.pop("state", None)
        uids = db_all_user_ids()
        total = len(uids)
        status = await msg.reply_text(
            qblocks(f"<b>📢 ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ</b>\n{LINE}",
                    f"Total: <b>{total}</b>\nSent: 0\nFailed: 0\n{LINE}",
                    f"<code>{progress_bar(0)}    0%  🌑</code>\n"
                    f"<i>Cancel: /cancel</i>"),
            parse_mode=ParseMode.HTML)

        async def _bcast_job():
            ok = 0; fail = 0
            try:
                for idx, target in enumerate(uids, 1):
                    try:
                        await ctx.bot.copy_message(chat_id=target, from_chat_id=msg.chat_id,
                                                    message_id=msg.message_id)
                        ok += 1
                    except Exception:
                        fail += 1
                    if idx % 25 == 0 or idx == total:
                        pct = int(idx / total * 100) if total else 100
                        try:
                            await status.edit_text(
                                qblocks(f"<b>📢 ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪɴ ᴘʀᴏɢʀᴇꜱꜱ</b>\n{LINE}",
                                        f"Total: <b>{total}</b>\nSent: <b>{ok}</b>\nFailed: <b>{fail}</b>\n{LINE}",
                                        f"<code>{progress_bar(int(idx/total*BAR_TOTAL) if total else BAR_TOTAL)}  {pct:3d}%  {progress_emoji(pct)}</code>\n"
                                        f"<i>Cancel: /cancel</i>"),
                                parse_mode=ParseMode.HTML)
                        except Exception:
                            pass
                    await asyncio.sleep(0.05)
                await status.edit_text(
                    qblocks(f"<b>✅ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇ</b>\n{LINE}",
                            f"▸ Total  : <b>{total}</b>\n▸ Sent   : <b>{ok}</b>\n▸ Failed : <b>{fail}</b>",
                            f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]]))
            except asyncio.CancelledError:
                try:
                    await status.edit_text(
                        qblocks(f"<b>⏹ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ</b>\n{LINE}",
                                f"▸ Sent   : <b>{ok}</b>\n▸ Failed : <b>{fail}</b>\n"
                                f"▸ Remaining skipped.\n{LINE}",
                                f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
                        parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                raise
            finally:
                _unregister_job(uid)

        task = asyncio.create_task(_bcast_job())
        _register_job(uid, task, msg=status, cmd="broadcast", kind="broadcast")
        try:
            await task
        except asyncio.CancelledError:
            pass
        return

    if name == "history_user":
        ctx.user_data.pop("state", None)
        txt = (msg.text or "").strip().lower()
        if txt == "all":
            rows = db_get_all_history(limit=500)
            fname = build_history_file(rows, None)
            await msg.reply_document(
                document=open(fname, "rb"),
                caption=qblocks(
                    f"<b>📜 ɢʟᴏʙᴀʟ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
                    f"▸ ᴛᴏᴛᴀʟ ʟᴏɢꜱ : <b>{len(rows)}</b>\n{LINE}",
                    dev_signature_txt()),
                parse_mode=ParseMode.HTML)
            try: os.remove(fname)
            except: pass
            return
        try:
            target = int(txt)
        except:
            await msg.reply_text(
                qblocks(f"<b>❌ ɪɴᴠᴀʟɪᴅ</b>\n{LINE}", "Send valid user_id or 'all'."),
                parse_mode=ParseMode.HTML)
            return
        rows = db_get_history(target, limit=500)
        if not rows:
            await msg.reply_text(
                qblocks(f"<b>📜 ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
                        f"ɴᴏ ʟᴏɢꜱ ꜰᴏʀ <code>{target}</code>."),
                parse_mode=ParseMode.HTML)
            return
        fname = build_history_file(rows, target)
        await msg.reply_document(
            document=open(fname, "rb"),
            caption=qblocks(
                f"<b>📜 ᴜꜱᴇʀ ʜɪꜱᴛᴏʀʏ</b>\n{LINE}",
                f"▸ ᴜꜱᴇʀ ɪᴅ   : <code>{target}</code>\n"
                f"▸ ᴛᴏᴛᴀʟ ʟᴏɢꜱ : <b>{len(rows)}</b>\n{LINE}",
                dev_signature_txt()),
            parse_mode=ParseMode.HTML)
        try: os.remove(fname)
        except: pass
        return

    if name == "cred_add_ids":
        ids = [int(x) for x in (msg.text or "").replace(",", " ").split()
               if x.strip().lstrip("-").isdigit()]
        if not ids:
            await msg.reply_text("❌ No valid IDs."); return
        ctx.user_data["state"] = ("cred_add_amt", ids)
        await msg.reply_text(
            qblocks(f"<b>💰 ᴄʀᴇᴅɪᴛ ᴀᴅᴅ</b>\n{LINE}",
                    f"ᴜꜱᴇʀꜱ : <b>{len(ids)}</b>\n"
                    "Now send the <b>amount</b> to add:"),
            parse_mode=ParseMode.HTML)
        return

    if name == "cred_add_amt":
        try: amt = int((msg.text or "").strip())
        except:
            await msg.reply_text("❌ Invalid amount."); return
        done = 0
        for u_ in extra:
            if db_get_user(u_):
                db_add_credits(u_, amt); done += 1
        ctx.user_data.pop("state", None)
        await msg.reply_text(
            qblocks(
                f"<b>✅ ᴄʀᴇᴅɪᴛ ᴀᴅᴅᴇᴅ</b>\n{LINE}",
                f"▸ ᴜꜱᴇʀꜱ  : <b>{done}/{len(extra)}</b>\n"
                f"▸ ᴀᴍᴏᴜɴᴛ : <b>+{amt}</b>\n{LINE}",
                dev_signature_txt()),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [B("⬅ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ", cb="menu:admin")]]))
        return

    if name == "cred_rm_ids":
        ids = [int(x) for x in (msg.text or "").replace(",", " ").split()
               if x.strip().lstrip("-").isdigit()]
        if not ids:
            await msg.reply_text("❌ No valid IDs."); return
        ctx.user_data["state"] = ("cred_rm_amt", ids)
        await msg.reply_text(
            qblocks(f"<b>🗑 ᴄʀᴇᴅɪᴛ ʀᴇᴍᴏᴠᴇ</b>\n{LINE}",
                    f"ᴜꜱᴇʀꜱ : <b>{len(ids)}</b>\n"
                    "Now send the <b>amount</b> to remove:"),
            parse_mode=ParseMode.HTML)
        return

    if name == "cred_rm_amt":
        try: amt = int((msg.text or "").strip())
        except:
            await msg.reply_text("❌ Invalid amount."); return
        done = 0
        for u_ in extra:
            if db_get_user(u_):
                db_deduct_credit(u_, amt); done += 1
        ctx.user_data.pop("state", None)
        await msg.reply_text(
            qblocks(
                f"<b>✅ ᴄʀᴇᴅɪᴛ ʀᴇᴍᴏᴠᴇᴅ</b>\n{LINE}",
                f"▸ ᴜꜱᴇʀꜱ  : <b>{done}/{len(extra)}</b>\n"
                f"▸ ᴀᴍᴏᴜɴᴛ : <b>-{amt}</b>\n{LINE}",
                dev_signature_txt()),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [B("⬅ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ", cb="menu:admin")]]))
        return

    if name == "api_add":
        if not msg.document:
            await msg.reply_text(qblocks(f"<b>📄 ꜰɪʟᴇ ʀᴇQᴜɪʀᴇᴅ</b>\n{LINE}",
                "Please send a <b>.txt</b> file."), parse_mode=ParseMode.HTML); return
        try:
            tg_file = await msg.document.get_file()
            data = await tg_file.download_as_bytearray()
            text = data.decode("utf-8", errors="ignore")
        except Exception as e:
            await msg.reply_text(f"❌ Download failed: {e}"); return
        valid, errors = parse_api_txt(text)
        if not valid:
            err_body = "\n".join(errors[:20]) or "ɴᴏ ᴠᴀʟɪᴅ ʟɪɴᴇꜱ ꜰᴏᴜɴᴅ."
            await msg.reply_text(
                qblocks(f"<b>❌ ɴᴏ ᴠᴀʟɪᴅ ᴀᴘɪꜱ ꜰᴏᴜɴᴅ</b>\n{LINE}",
                        f"<pre>{err_body[:2500]}</pre>"),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [B("📄 ᴛᴇᴍᴘʟᴀᴛᴇ", cb="o:api_tpl")],
                    [B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]]))
            return
        added, skipped = 0, []
        for cmd, title, usage, urls in valid:
            if db_add_custom_api(cmd, title, usage, urls, uid):
                added += 1
            else:
                skipped.append(cmd)
        ctx.user_data.pop("state", None)
        body = (
            f"▸ Added  : <b>{added}</b>\n"
            f"▸ Skipped: <b>{len(skipped)}</b> (already exist)\n"
        )
        if skipped:
            body += f"{LINE}\n<i>Existing (safe):</i>\n"
            body += "\n".join(f"• <code>/{c}</code>" for c in skipped[:15])
        if errors:
            body += f"\n{LINE}\n⚠ Invalid: <b>{len(errors)}</b>"
            body += "\n" + "\n".join(f"• {e}" for e in errors[:5])
        await msg.reply_text(
            qblocks(f"<b>✅ ᴀᴘɪꜱ ᴀᴅᴅᴇᴅ</b>\n{LINE}", body),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [B("📋 ᴠɪᴇᴡ ʟɪꜱᴛ", cb="o:api_list")],
                [B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]]))
        return

    if name == "api_del":
        txt = (msg.text or "").strip()
        cmds = [c.strip().lstrip("/").lower() for c in txt.replace(",", " ").split() if c.strip()]
        removed, notfound = 0, []
        for c in cmds:
            if db_get_custom_api(c):
                db_remove_custom_api(c); removed += 1
            else: notfound.append(c)
        ctx.user_data.pop("state", None)
        body = f"✅ Removed: <b>{removed}</b>"
        if notfound: body += f"\n⚠ Not found: <code>{', '.join(notfound)}</code>"
        await msg.reply_text(
            qblocks(f"<b>🗑 ᴀᴘɪ ᴅᴇʟᴇᴛᴇᴅ</b>\n{LINE}", body),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]]))
        return

    if name == "wlc_text":
        db_set("welcome_text", msg.html_text or msg.text)
        ctx.user_data.pop("state", None)
        await msg.reply_text(qblocks(f"<b>✅ Sᴀᴠᴇᴅ</b>\n{LINE}", "GC welcome text saved.\n(Only used when new member joins GC)"),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]]))
        return
    if name == "wlc_media":
        fid, mt = None, None
        if msg.photo: fid, mt = msg.photo[-1].file_id, "photo"
        elif msg.video: fid, mt = msg.video.file_id, "video"
        elif msg.animation: fid, mt = msg.animation.file_id, "animation"
        if not fid: await msg.reply_text("❌ Photo/video/GIF only."); return
        db_set("welcome_media", json.dumps({"type": mt, "file_id": fid}))
        ctx.user_data.pop("state", None)
        await msg.reply_text(qblocks(f"<b>✅ Sᴀᴠᴇᴅ</b>\n{LINE}", "GC welcome media saved.\n(Only used when new member joins GC)"),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]]))
        return

    def _ids(): return [int(x) for x in msg.text.replace(",", " ").split() if x.strip().isdigit()]

    if name == "adm_add":
        ids = _ids(); ok = 0
        for i in ids:
            if db_get_user(i): db_set_admin(i, True); ok += 1
        ctx.user_data.pop("state", None)
        await msg.reply_text(qblocks(f"<b>✅ ᴘʀᴏᴍᴏᴛᴇᴅ</b>\n{LINE}", f"{ok}/{len(ids)}"),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]])); return
    if name == "adm_rm":
        ids = _ids(); ok = 0
        for i in ids: db_set_admin(i, False); ok += 1
        ctx.user_data.pop("state", None)
        await msg.reply_text(qblocks(f"<b>✅ ᴅᴇᴍᴏᴛᴇᴅ</b>\n{LINE}", f"{ok}"),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[B("⬅ ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", cb="menu:owner")]])); return
    if name == "prem_add":
        ids = _ids()
        if not ids:
            await msg.reply_text(qblocks(f"<b>❌ Iɴᴠᴀʟɪᴅ</b>\n{LINE}", "Send numeric user_id."), parse_mode=ParseMode.HTML)
            return
        ok = 0
        already = 0
        for i in ids:
            u = db_get_user(i)
            if not u:
                db_create_user(i, None, "User")
                u = db_get_user(i)
            if not u:
                continue
            was = user_is_premium(u)
            db_set_premium(i, True)  # always force VIP on
            if not was:
                db_add_credits(i, PREMIUM_CREDITS)
                ok += 1
            else:
                already += 1
            log.info("prem_add user=%s vip=1 was=%s", i, was)
        ctx.user_data.pop("state", None)
        body = (
            f"▸ Added VIP : <b>{ok}</b>\n"
            f"▸ Already VIP : <b>{already}</b>\n"
            f"▸ Requested : <b>{len(ids)}</b>"
        )
        await msg.reply_text(qblocks(f"<b>✅ Aᴅᴅᴇᴅ Vɪᴘ</b>\n{LINE}", body),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[B("⬅ Bᴀᴄᴋ", cb="menu:owner")]])); return
    if name == "prem_rm":
        ids = _ids(); ok = 0
        for i in ids: db_set_premium(i, False); ok += 1
        ctx.user_data.pop("state", None)
        await msg.reply_text(qblocks(f"<b>✅ ʀᴇᴍᴏᴠᴇᴅ</b>\n{LINE}", f"{ok}"),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[B("⬅ ʙᴀᴄᴋ", cb="menu:owner")]])); return

    if name == "chnl_add":
        text = (msg.text or "").strip()
        if not text:
            await msg.reply_text("❌ Send @username / link / chat_id"); return
        try:
            chat = None
            invite_hint = None
            # 1) numeric chat id (-100...)
            if re.fullmatch(r"-?\d+", text):
                chat = await ctx.bot.get_chat(int(text))
            # 2) invite / t.me links
            elif text.startswith("http://") or text.startswith("https://") or text.startswith("t.me/"):
                invite_hint = text if text.startswith("http") else "https://" + text
                try:
                    chat = await ctx.bot.get_chat(invite_hint)
                except Exception:
                    # private invite: bot must already be member/admin
                    raise
            # 3) @username or bare username
            else:
                un = text if text.startswith("@") else "@" + text.lstrip("@")
                chat = await ctx.bot.get_chat(un)

            if not chat:
                await msg.reply_text("❌ Channel not found"); return

            # only channels / supergroups
            ctype = getattr(chat, "type", None)
            if str(ctype) not in ("channel", "supergroup", "ChatType.CHANNEL", "ChatType.SUPERGROUP"):
                # telegram enum
                try:
                    from telegram.constants import ChatType
                    if ctype not in (ChatType.CHANNEL, ChatType.SUPERGROUP):
                        await msg.reply_text("❌ Sirf channel / supergroup allowed"); return
                except Exception:
                    pass

            priv = 0 if getattr(chat, "username", None) else 1
            invite = None
            if priv:
                # prefer create join-request link
                try:
                    inv = await ctx.bot.create_chat_invite_link(
                        chat.id, name="Kittu OSINT FJ", creates_join_request=True)
                    invite = inv.invite_link
                except Exception:
                    try:
                        invite = await ctx.bot.export_chat_invite_link(chat.id)
                    except Exception:
                        invite = invite_hint
                if not invite:
                    await msg.reply_text(
                        "❌ Private channel: bot ko <b>Admin</b> banao "
                        "(Invite Users + Manage Invite Links), phir dubara try.",
                        parse_mode=ParseMode.HTML); return
            else:
                invite = f"https://t.me/{chat.username}"

            # verify bot is admin (needed for membership check)
            try:
                me = await ctx.bot.get_me()
                mem = await ctx.bot.get_chat_member(chat.id, me.id)
                st = getattr(mem, "status", "")
                if st not in ("administrator", "creator"):
                    await msg.reply_text(
                        "⚠ Channel add hoga, lekin bot <b>Admin</b> nahi hai.\n"
                        "Force-join check fail ho sakta hai — bot ko admin banao.",
                        parse_mode=ParseMode.HTML)
            except Exception as e:
                await msg.reply_text(
                    f"⚠ Bot channel me nahi hai / admin nahi.\n<code>{e}</code>\n"
                    "Pehle bot ko channel me admin banao.",
                    parse_mode=ParseMode.HTML)

            db_add_channel(chat.id, getattr(chat, "username", None), invite, chat.title, priv)
            ctx.user_data.pop("state", None)
            tip = ""
            if priv:
                tip = "\n\n📌 Private: users join-request bhejenge — bot auto detect karega."
            await msg.reply_text(qblocks(
                f"<b>✅ ᴄʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ</b>\n{LINE}",
                f"▸ Title: <b>{chat.title}</b>\n"
                f"▸ ID: <code>{chat.id}</code>\n"
                f"▸ Type: {'🔒 Private' if priv else '🌐 Public'}\n"
                f"▸ Link: {invite or '—'}"
                f"{tip}"),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄʜᴀɴɴᴇʟꜱ", cb="o:chnl")]]))
        except Exception as e:
            await msg.reply_text(
                qblocks(f"<b>❌ ᴀᴅᴅ ꜰᴀɪʟᴇᴅ</b>\n{LINE}",
                    f"<code>{e}</code>\n{LINE}\n"
                    "Try:\n"
                    "• Public: <code>@channel</code>\n"
                    "• Private: invite link <code>https://t.me/+xxx</code>\n"
                    "• Or numeric id <code>-100...</code>\n"
                    "Bot must be <b>Admin</b> in that channel."),
                parse_mode=ParseMode.HTML)
        return
    if name == "chnl_rm":
        text = (msg.text or "").strip()
        try:
            cid = None
            if re.fullmatch(r"-?\d+", text):
                cid = int(text)
            else:
                un = text if text.startswith("@") else "@" + text.lstrip("@")
                chat = await ctx.bot.get_chat(un)
                cid = chat.id
            db_remove_channel(cid)
            ctx.user_data.pop("state", None)
            await msg.reply_text(qblocks(f"<b>✅ ʀᴇᴍᴏᴠᴇᴅ</b>\n{LINE}", f"ID: <code>{cid}</code>"),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[B("⬅ ᴄʜᴀɴɴᴇʟꜱ", cb="o:chnl")]]))
        except Exception as e:
            await msg.reply_text(f"❌ {e}")
        return
    if name == "gc_add":
        try:
            gid = int(msg.text.strip()); chat = await ctx.bot.get_chat(gid)
            db_add_group(gid, chat.title); ctx.user_data.pop("state", None)
            await msg.reply_text(qblocks(f"<b>✅ ᴀᴅᴅᴇᴅ</b>\n{LINE}", f"ɢᴄ: <b>{chat.title}</b>"),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[B("⬅ ɢʀᴏᴜᴘꜱ", cb="o:gc")]]))
        except Exception as e: await msg.reply_text(f"❌ {e}")
        return
    if name == "gc_rm":
        try:
            db_remove_group(int(msg.text.strip()))
            ctx.user_data.pop("state", None)
            await msg.reply_text(qblocks(f"<b>✅ ʀᴇᴍᴏᴠᴇᴅ</b>\n{LINE}", ""),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[B("⬅ ɢʀᴏᴜᴘꜱ", cb="o:gc")]]))
        except Exception as e: await msg.reply_text(f"❌ {e}")
        return


# ============================================================
#  GC WELCOME (new members only — uses owner-set text/media)
# ============================================================
async def gc_new_member_welcome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Welcome new GC members only if owner set welcome text and/or media."""
    msg = update.message
    if not msg or not msg.new_chat_members:
        return
    if not is_gc(update):
        return
    wtext = (db_get("welcome_text") or "").strip()
    wmedia_raw = db_get("welcome_media")
    wmedia = None
    if wmedia_raw:
        try:
            wmedia = json.loads(wmedia_raw)
        except Exception:
            wmedia = None
    # If neither text nor media set → no welcome
    if not wtext and not wmedia:
        return
    for member in msg.new_chat_members:
        if member.is_bot:
            continue
        name = member.full_name or member.first_name or "User"
        mention = f'<a href="tg://user?id={member.id}">{name}</a>'
        caption = wtext.replace("{name}", mention).replace("{user}", mention) if wtext else ""
        if not caption and wtext:
            caption = wtext
        try:
            if wmedia and wmedia.get("file_id"):
                mt = wmedia.get("type") or "photo"
                fid = wmedia["file_id"]
                if mt == "photo":
                    await ctx.bot.send_photo(
                        chat_id=msg.chat_id, photo=fid,
                        caption=caption[:1024] if caption else None,
                        parse_mode=ParseMode.HTML if caption else None)
                elif mt == "video":
                    await ctx.bot.send_video(
                        chat_id=msg.chat_id, video=fid,
                        caption=caption[:1024] if caption else None,
                        parse_mode=ParseMode.HTML if caption else None)
                elif mt == "animation":
                    await ctx.bot.send_animation(
                        chat_id=msg.chat_id, animation=fid,
                        caption=caption[:1024] if caption else None,
                        parse_mode=ParseMode.HTML if caption else None)
                else:
                    if caption:
                        await ctx.bot.send_message(
                            chat_id=msg.chat_id, text=caption,
                            parse_mode=ParseMode.HTML)
            elif caption:
                await ctx.bot.send_message(
                    chat_id=msg.chat_id, text=caption,
                    parse_mode=ParseMode.HTML)
        except Exception as e:
            log.warning("gc welcome fail: %s", e)

# ============================================================
#  JOIN REQUEST
# ============================================================
async def join_request_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    db_add_join_req(req.from_user.id, req.chat.id)
    try:
        await ctx.bot.send_message(req.from_user.id,
            qblocks(f"<b>✅ ᴊᴏɪɴ ʀᴇQᴜᴇꜱᴛ ʀᴇᴄᴇɪᴠᴇᴅ</b>\n{LINE}",
                    f"ᴄʜᴀɴɴᴇʟ: <b>{req.chat.title}</b>\nᴀʙ ʙᴏᴛ ᴜꜱᴇ ᴋᴀʀ ꜱᴀᴋᴛᴇ ʜᴏ.\n{LINE}",
                    f"👨‍💻 <b>ᴅᴇᴠᴇʟᴏᴘᴇʀ</b> — {dev_link()}"),
            parse_mode=ParseMode.HTML)
    except Exception: pass

# ============================================================
#  MAIN
# ============================================================
def main():
    if not BOT_TOKEN: raise SystemExit("BOT_TOKEN missing")
    init_db(); db_cleanup_logs(); seed_builtin_apis(); open_external_db(); ensure_owner_protected()
    try:
        nexp = db_cleanup_expired_generated()
        if nexp:
            log.info("Cleaned %s expired generated APIs", len(nexp))
    except Exception as e:
        log.warning("cleanup generated: %s", e)
    if MAIN_GC_ID:
        db_add_group(MAIN_GC_ID, "Main GC")
        # placeholder channel row until live resolve
        db_add_channel(MAIN_GC_ID, None, None, "Main GC", 1)
    if OWNER_ID:
        db_create_user(OWNER_ID, None, "Owner"); db_set_admin(OWNER_ID, True); db_set_premium(OWNER_ID, True)

    async def _post_init(application):
        try:
            n = await seed_force_joins(application.bot)
            log.info("Force-join seeded: %s targets", n)
        except Exception as e:
            log.warning("seed_force_joins: %s", e)
    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cmd", cmd_cmd))
    app.add_handler(CommandHandler("cmds", cmd_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("refer", refer_cmd))
    app.add_handler(CommandHandler("premium", premium_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    app.add_handler(CommandHandler("ai", ai_cmd))
    app.add_handler(CommandHandler("extdb", extdb_cmd))
    app.add_handler(CommandHandler("protect", protect_cmd))
    app.add_handler(CommandHandler("num", num_cmd))
    app.add_handler(CommandHandler("tg", tg_cmd))
    app.add_handler(CommandHandler("spin", spin_cmd))
    app.add_handler(CommandHandler("addapi", addapi_cmd))
    app.add_handler(CommandHandler("delapi", delapi_cmd))
    app.add_handler(CommandHandler("listapi", listapi_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("killdead", killdead_cmd))
    app.add_handler(CommandHandler("generate", generate_cmd))
    app.add_handler(CommandHandler("genrate", generate_cmd))  # typo alias
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(ChatJoinRequestHandler(join_request_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, gc_new_member_welcome))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.CONTACT, text_button_router))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.CONTACT, state_handler))
    app.add_handler(MessageHandler(filters.COMMAND, custom_api_router))
    app.job_queue.run_repeating(lambda c: db_cleanup_logs(), interval=86400, first=60)
    log.info(f"🤖 {BOT_NAME} started")

    # Termux / Python 3.10+ event-loop fix
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
    except Exception:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


# ============================================================
#  RENDER + UPTIMEROBOT SUPPORT (Keep-Alive)
# ============================================================
def run_with_flask():
    """Run bot + Flask health endpoint for Render free tier + UptimeRobot."""
    from flask import Flask
    flask_app = Flask(__name__)

    @flask_app.route("/")
    def health():
        return "🤖 Kittu OSINT Bot is alive 24/7", 200

    @flask_app.route("/health")
    def health2():
        return {"status": "ok", "bot": BOT_NAME}, 200

    def start_bot():
        main()

    # Start Telegram bot in background thread
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()

    # Flask listens on Render's PORT
    port = int(os.environ.get("PORT", 10000))
    log.info(f"Flask health server starting on port {port}")
    flask_app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    # Agar Render pe hai (PORT env set) to Flask + bot, warna normal
    if os.environ.get("PORT"):
        run_with_flask()
    else:
        main()