# ---------------------------------------------------------
#                   ECHOVERSE FINAL BACKEND (FIXED)
#   Full features: OCR + Docs + Web Search + Voice + RAG
# ---------------------------------------------------------

from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import os, json, re, uuid, tempfile, logging, requests
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from pathlib import Path

# LLM
import google.generativeai as genai

# SerpApi (optional)
try:
    from serpapi import GoogleSearch
except Exception:
    GoogleSearch = None

# Files / OCR / TTS
import docx2txt
import PyPDF2
from PIL import Image
import pytesseract
from gtts import gTTS

# ---------------- CONFIG ----------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SERPAPI_KEY    = os.getenv("SERPAPI_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

MODEL_LIST = ["gemini-2.0-flash-exp", "gemini-2.5-flash"]
_MODELS = []
for m in MODEL_LIST:
    try:
        _MODELS.append(genai.GenerativeModel(m))
    except Exception as e:
        logging.warning(f"Model init failed: {m}: {e}")

def _llm(prompt: str) -> str:
    for model in _MODELS:
        try:
            out = model.generate_content(prompt)
            t = getattr(out, "text", None)
            if t:
                return t.strip()
        except Exception as e:
            logging.warning(f"LLM call failed: {e}")
    return "I couldn't process that right now."

# ---------------- FILES ----------------
BASE = Path(__file__).parent
HISTORY   = BASE / "chathistory.json"
DOC       = BASE / "doc.txt"
IMG       = BASE / "img.txt"
REMINDERS = BASE / "reminders.json"
TTS_DIR   = BASE / "static" / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)

def _ensure(p: Path, default):
    if not p.exists():
        if isinstance(default, (dict, list)):
            p.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            p.write_text(str(default), encoding="utf-8")

_ensure(HISTORY, [])
_ensure(REMINDERS, [])

def read_txt(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""

def write_txt(p: Path, s: str):
    p.write_text(s, encoding="utf-8")

def load_json(p: Path, fb):
    try:
        raw = read_txt(p)
        return json.loads(raw) if raw.strip() else fb
    except Exception:
        return fb

def save_json(p: Path, obj):
    write_txt(p, json.dumps(obj, indent=2, ensure_ascii=False))

# ---------------- PERSONALITY / LANGUAGE ----------------
PERSONALITY = {
    "default": "Friendly and natural.",
    "educational": "Clear teacher tone with examples.",
    "developer": "Technical and precise. Short and direct.",
    "fun": "Playful and expressive.",
    "professional": "Formal and concise.",
    "motivational": "Positive and uplifting."
}

LANG_MAP = {
    "en":"English",
    "hi":"Hindi",
    "hinglish":"Hinglish",
    "es":"Spanish",
    "fr":"French",
    "auto":None
}

def translate(text: str, lang: str, mode: str) -> str:
    if not text or lang == "auto":
        return text
    target = LANG_MAP.get(lang)
    tone   = PERSONALITY.get(mode, PERSONALITY["default"])

    if lang == "hinglish":
        prompt = f"Convert the following to Hinglish (Hindi in English letters). No Devanagari.\n\nTEXT:\n{text}"
        return _llm(prompt) or text

    prompt = f"Translate to {target} using tone: {tone}\n\nTEXT:\n{text}"
    return _llm(prompt) or text

def is_smalltalk(text: str) -> bool:
    if not text:
        return False
    t = text.lower().strip()
    return t in [
        "hi","hello","hey","hola","namaste",
        "how are you","how r u","how ru","how are u",
        "kaise ho","kya haal hai","whats up","what's up"
    ]

# ---------------- OCR / DOC QA ----------------
def is_ocr_query(text: str) -> bool:
    if not text: return False
    t = text.lower()
    keys = [
        "read text", "read the text", "read text given",
        "text in image", "what is written", "what is the text",
        "what is the text given", "image me", "photo me",
        "ocr", "image text", "image mein", "image ke text"
    ]
    return any(k in t for k in keys)

def doc_answer(q: str, txt: str):
    if not txt.strip():
        return None
    prompt = f"""
From this DOCUMENT, answer the QUESTION.
If answer not found, reply exactly: Not in document.

QUESTION: {q}

DOCUMENT:
{txt[:7000]}
"""
    return _llm(prompt)

# ---------------- SEARCH ----------------
def serp(q: str):
    if not SERPAPI_KEY or GoogleSearch is None:
        return []
    try:
        r = GoogleSearch({"q": q, "api_key": SERPAPI_KEY, "num": 7}).get_dict()
        return r.get("organic_results", []) or []
    except Exception as e:
        logging.warning(f"SerpApi failed: {e}")
        return []

def wiki_fallback(q: str):
    try:
        sr = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action":"query","list":"search","srsearch":q,"format":"json"},
            timeout=8
        ).json()
        hits = sr.get("query",{}).get("search",[])
        if not hits: return None
        title = hits[0]["title"]
        pg = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(title),
            timeout=8
        ).json()
        return pg.get("extract")
    except Exception:
        return None

def web_answer(q: str) -> str:
    items = serp(q)
    if items:
        ctx = "\n".join([f"- {i.get('title')}: {i.get('snippet')}" for i in items[:5]])
        prompt = f"Use ONLY this WEB context:\n{ctx}\n\nAnswer: {q}"
        return _llm(prompt)

    wiki = wiki_fallback(q)
    if wiki:
        return wiki

    return _llm(f"Answer briefly: {q}")

# ---------------- REMINDERS ----------------
def add_reminder(task: str, minutes_from_now: int = 1):
    items = load_json(REMINDERS, [])
    due = datetime.now(timezone.utc) + timedelta(minutes=minutes_from_now)

    items.append({
        "id": str(uuid.uuid4()),
        "task": task,
        "due_ts": due.isoformat(),
        "delivered": False
    })
    save_json(REMINDERS, items)
    return due.isoformat()

def list_due_reminders():
    items = load_json(REMINDERS, [])
    now = datetime.now(timezone.utc)
    return [x for x in items if not x.get("delivered") and _parse_ts(x.get("due_ts")) <= now]

def _parse_ts(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.now(timezone.utc)

# ---------------- TTS ----------------
GTT_LANG = {"en":"en","hi":"hi","hinglish":"en","es":"es","fr":"fr","auto":"en"}

_EMOJI_RX = re.compile(
    "[" 
    "\U0001F300-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]+", flags=re.UNICODE
)

def _clean_for_tts(s: str) -> str:
    if not s: return " "
    s = _EMOJI_RX.sub(" ", s)
    s = re.sub(r"[^\w\s\.\,\!\?\-\:;\'\"/()\[\]]", " ", s)
    return re.sub(r"\s+", " ", s).strip() or " "

def make_tts(text: str, lang: str):
    try:
        clip = _clean_for_tts(text)
        if len(clip) > 4000:
            clip = clip[:4000]
        tts = gTTS(text=clip, lang=GTT_LANG.get(lang, "en"))
        fname = f"tts_{uuid.uuid4().hex}.mp3"
        path = TTS_DIR / fname
        tts.save(str(path))
        return f"/static/tts/{fname}"
    except Exception:
        return None

# ---------------- FLASK APP ----------------
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    return jsonify(load_json(REMINDERS, []))

@app.route("/reminders-due")
def reminders_due():
    due = list_due_reminders()
    return Response(json.dumps(due), mimetype="application/json")

@app.route("/reminders-ack", methods=["POST"])
def reminders_ack():
    data = request.get_json(silent=True) or {}
    rid = data.get("id")
    snooze = data.get("snooze_minutes")

    items = load_json(REMINDERS, [])
    for it in items:
        if it["id"] == rid:
            if snooze:
                it["due_ts"] = (datetime.now(timezone.utc) + timedelta(minutes=int(snooze))).isoformat()
                it["delivered"] = False
            else:
                it["delivered"] = True

    save_json(REMINDERS, items)
    return jsonify({"ok": True})

# ---------------- CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        msg = (data.get("message") or "").strip()
        lang = (data.get("language") or "auto").lower()
        mode = data.get("mode","default")
        voice = bool(data.get("voice_enabled", False))

        if not msg:
            return jsonify({"reply":"Say something.", "audio_url":None})

        # Reset
        if msg.lower() in ["new chat","reset","clear","clear chat"]:
            save_json(HISTORY,[])
            if DOC.exists(): DOC.unlink()
            if IMG.exists(): IMG.unlink()
            save_json(REMINDERS, [])
            return jsonify({"reply":"✨ New chat started!", "audio_url": None})

        # Reminder
        if msg.lower().startswith(("remind me","set reminder")):
            m = re.search(r"in\s+(\d+)\s*(sec|secs|seconds|min|mins|minutes|hour|hours)", msg.lower())
            minutes = 1

            if m:
                n = int(m.group(1)); unit = m.group(2)
                if unit.startswith("sec"):
                    minutes = max(1, int(round(n/60)))
                elif unit.startswith("hour"):
                    minutes = n * 60
                else:
                    minutes = n

            due = add_reminder(msg, minutes)
            return jsonify({"reply": f"🗓 Reminder added! (due: {due})", "audio_url": None})

        # OCR
        if is_ocr_query(msg):
            if IMG.exists():
                text = read_txt(IMG)
                rep = translate(text or "Image unreadable.", lang, mode)
                audio = make_tts(rep, lang) if voice else None
                _log_history(msg, rep)
                return jsonify({"reply":rep, "audio_url":audio})
            else:
                rep = translate("Upload an image first.", lang, mode)
                return jsonify({"reply":rep, "audio_url":None})

        # Small talk
        if is_smalltalk(msg):
            rep = translate("Hello! How can I help you?", lang, mode)
            audio = make_tts(rep, lang) if voice else None
            _log_history(msg, rep)
            return jsonify({"reply":rep, "audio_url":audio})

        # DOC QA
        reply = None
        if DOC.exists():
            ans = doc_answer(msg, read_txt(DOC))
            if ans and ans.strip().lower() != "not in document":
                reply = ans

        # Web
        if reply is None:
            reply = web_answer(msg)

        reply = translate(reply, lang, mode)
        audio = make_tts(reply, lang) if voice else None

        _log_history(msg, reply)
        return jsonify({"reply":reply, "audio_url":audio})

    except Exception as e:
        logging.exception("CHAT ERROR")
        return jsonify({"error":str(e)}), 500

def _log_history(u, b):
    hist = load_json(HISTORY, [])
    ts = datetime.now(timezone.utc).isoformat()
    hist.append({"who":"user","text":u,"ts":ts})
    hist.append({"who":"bot","text":b,"ts":ts})
    save_json(HISTORY, hist[-200:])

# ---------------- UPLOAD ----------------
@app.route("/upload-doc", methods=["POST"])
def upload_doc():
    try:
        if "file" not in request.files:
            return jsonify({"error":"No file uploaded"}),400

        f = request.files["file"]
        ext = f.filename.lower().split(".")[-1]
        text = ""

        if ext == "txt":
            text = f.read().decode("utf-8","ignore")

        elif ext == "pdf":
            reader = PyPDF2.PdfReader(f)
            chunks = []
            for p in reader.pages:
                try: chunks.append(p.extract_text() or "")
                except: pass
            text = "\n".join(chunks)

        elif ext in ["doc","docx"]:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".docx") as tmp:
                f.save(tmp.name)
                text = docx2txt.process(tmp.name) or ""

        else:
            return jsonify({"error":"Unsupported file"}),400

        write_txt(DOC, text)
        summary = _llm("Summarize in 5 bullets:\n" + text[:2000])
        return jsonify({"message":"✅ Document uploaded","analysis":summary})
    except Exception as e:
        logging.exception("UPLOAD DOC ERROR")
        return jsonify({"error":str(e)}),500

@app.route("/upload-image", methods=["POST"])
def upload_image():
    try:
        if "file" not in request.files:
            return jsonify({"error":"No file uploaded"}),400

        img = Image.open(request.files["file"].stream).convert("RGB")
        ocr = pytesseract.image_to_string(img)
        write_txt(IMG, ocr)

        return jsonify({"message":"✅ Image processed","ocr_text":ocr})
    except Exception as e:
        logging.exception("UPLOAD IMAGE ERROR")
        return jsonify({"error":str(e)}),500

# ---------------- EXPORT / DELETE ----------------
@app.route("/export-data")
def export_data():
    data = read_txt(HISTORY)
    return Response(data or "[]", mimetype="application/json",
        headers={"Content-Disposition":"attachment; filename=chat_history.json"})

@app.route("/delete-data", methods=["DELETE"])
def delete_data():
    save_json(HISTORY, [])
    if DOC.exists(): DOC.unlink()
    if IMG.exists(): IMG.unlink()
    save_json(REMINDERS, [])
    return jsonify({"ok":True})

# ---------------- RUN (FIXED) ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True, threaded=True)
