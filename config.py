"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY GEORGIAN"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "GEORGIAN"
HANDLE = "@velocitygeorgian"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'ka',
 'name': 'Georgian',
 'native_name': 'ქართული',
 'history_key': 'georgian',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'ka-GE-GiorgiNeural',
 'native_fallback_voice': 'ka-GE-EkaNeural',
 'native_engine': 'edge',
 'native_lang_code': 'ka',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'ქართული',
 'translit_label': 'SAY IT LIKE',
 'flag': 'ge',
 'greeting': 'გამარჯობა!',
 'encouragement': 'შესანიშნავია!',
 'rtl': False,
 'char_tiles': False,
 'script_font': 'Script.ttf',
 'glyphs': 'აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'მოტივაცია',
 'Love': 'სიყვარული',
 'Success': 'წარმატება',
 'Wisdom': 'სიბრძნე',
 'Happiness': 'ბედნიერება',
 'Self Improvement': 'თვითგანვითარება',
 'Gratitude': 'მადლიერება',
 'Friendship': 'მეგობრობა',
 'Hope': 'იმედი',
 'Creativity': 'კრეატიულობა',
 'Inner Peace': 'შინაგანი სიმშვიდე',
 'Confidence': 'თავდაჯერებულობა',
 'Perseverance': 'გამძლეობა',
 'Inspiration': 'შთაგონება',
 'Positive Life': 'პოზიტიური ცხოვრება',
 'Courage': 'გამბედაობა',
 'Kindness': 'სიკეთე',
 'Patience': 'მოთმინება',
 'Forgiveness': 'პატიება',
 'Strength': 'ძალა',
 'Joy': 'სიხარული',
 'Balance': 'ბალანსი',
 'Growth': 'ზრდა',
 'Purpose': 'მიზანი',
 'Mindfulness': 'ცნობიერება',
 'Travel & Airport': 'მოგზაურობა და აეროპორტი',
 'Ordering Food & Dining': 'საკვების შეკვეთა და კვება',
 'Shopping & Prices': 'შოპინგი და ფასები',
 'Asking for Directions': 'გზის კითხვა',
 'Hotel & Accommodation': 'სასტუმრო და განთავსება',
 'Daily Routine': 'ყოველდღიური რუტინა',
 'Meeting People & Greetings': 'ადამიანებთან შეხვედრა და მისალმება',
 'Emergency & Health': 'სასწრაფო დახმარება და ჯანმრთელობა',
 'Public Transportation': 'საზოგადოებრივი ტრანსპორტი',
 'Work & Office': 'სამსახური და ოფისი',
 'Weather & Small Talk': 'ამინდი და უბრალო საუბარი',
 'Coffee Shop & Bakery': 'ყავის სახლი და საკონდიტრო',
 'Family & Home': 'ოჯახი და სახლი',
 'Hobbies & Free Time': 'ჰობი და თავისუფალი დრო',
 'Dating & Romance': 'შეყვარებულობა და რომანტიკა',
 'Phone Calls & Messages': 'სატელეფონო ზარები და შეტყობინებები',
 'Banking & Money': 'ბანკი და ფული',
 'Doctor & Pharmacy': 'ექიმი და აფთიაქი',
 'Sports & Fitness': 'სპორტი და ფიტნესი',
 'Celebrations & Parties': 'ზეიმები და წვეულებები',
 'Feelings & Emotions': 'გრძნობები და ემოციები',
 'Agreeing & Disagreeing': 'შეთანხმება და უთანხმოება',
 'Making Plans': 'გეგმების შედგენა',
 'Common Native Slang': 'საერთო ადგილობრივი ჟარგონი',
 'Cultural Traditions': 'კულტურული ტრადიციები'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learngeorgian',
 '#georgianlessons',
 '#georgianforbeginners',
 '#languagelearning',
 '#georgianvocabulary',
 '#velocitygeorgian',
 '#dailygeorgian',
 '#georgian',
 '#learnlanguages',
 '#speakgeorgian']
# ==== HASHTAGS END ====
