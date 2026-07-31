"""
YouTube Long-Form Video Automation - Bilingual English/Georgian Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Georgian translations (Mkhedruli script)
CATEGORIES_GEORGIAN = {
    "Motivation": "მოტივაცია",
    "Love": "სიყვარული",
    "Success": "წარმატება",
    "Wisdom": "სიბრძნე",
    "Happiness": "ბედნიერება",
    "Self Improvement": "თვითგანვითარება",
    "Gratitude": "მადლიერება",
    "Friendship": "მეგობრობა",
    "Hope": "იმედი",
    "Creativity": "კრეატიულობა",
    "Inner Peace": "შინაგანი სიმშვიდე",
    "Confidence": "თავდაჯერებულობა",
    "Perseverance": "გამძლეობა",
    "Inspiration": "შთაგონება",
    "Positive Life": "პოზიტიური ცხოვრება",
    "Courage": "გამბედაობა",
    "Kindness": "სიკეთე",
    "Patience": "მოთმინება",
    "Forgiveness": "პატიება",
    "Strength": "ძალა",
    "Joy": "სიხარული",
    "Balance": "ბალანსი",
    "Growth": "ზრდა",
    "Purpose": "მიზანი",
    "Mindfulness": "ცნობიერება",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "ka-GE-EkaNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "georgian": phrase["georgian"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_georgian = CATEGORIES_GEORGIAN[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Georgian.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - STRICTLY ENFORCE:
The "english" field must contain PURE ENGLISH words only. ZERO Georgian/Mkhedruli.
The "georgian" field contains the Georgian translation in Mkhedruli script.
The "pronunciation" field is phonetic English spelling.

WRONG (mixed language): {{"english": "Sheni otsneba aaket, believe in yourself", ...}}
WRONG (Georgian in english): {{"english": "Follow your otsnebi and success will come", ...}}
CORRECT: {{"english": "Make your dreams come true, believe in yourself.", "georgian": "გაახდენე შენი ოცნებები, გჯეროდეს საკუთარი თავის.", "pronunciation": "ga-akh-de-ne she-ni ots-ne-be-bi, gje-ro-des sa-ku-ta-ri ta-vis."}}

The english field MUST be 100% English words only. NO Georgian words allowed.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Georgian) with commas for natural pauses
2. Georgian translation (Mkhedruli script only)
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "georgian": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a viral Georgian teacher. CRITICAL: The 'english' field must contain PURE ENGLISH words ONLY. NO Georgian in english field. Georgian goes in the 'georgian' field. This is strictly enforced."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "georgian": "გჯეროდეს საკუთარი თავის.", "pronunciation": "gje-ro-des sa-ku-ta-ri ta-vis."},
            {"english": "You are capable of amazing things.", "georgian": "შენ შეგიძლია საოცარი რაღაცები.", "pronunciation": "shen she-gidz-li-a sa-o-tsa-ri ra-gha-tse-bi."},
            {"english": "Dream big, start small.", "georgian": "იოცნებე დიდად, დაიწყე პატარით.", "pronunciation": "i-ots-ne-be di-dad, dai-tsq-e pa-ta-rit."},
            {"english": "Your future is created by your actions.", "georgian": "შენი მომავალი შენი ქმედებებით იქმნება.", "pronunciation": "she-ni mo-ma-va-li she-ni km-de-be-bit ikm-ne-ba."},
            {"english": "Never give up on your dreams.", "georgian": "არასოდეს თქვა უარი შენს ოცნებებზე.", "pronunciation": "a-ra-so-des tkva ua-ri shens ots-ne-beb-ze."},
            {"english": "Small steps lead to big changes.", "georgian": "პატარა ნაბიჯები დიდ ცვლილებებამდე მიგვიყვანს.", "pronunciation": "pa-ta-ra na-bi-dzhe-bi did tsvi-li-le-ba-mde mi-gvi-qvans."},
            {"english": "You are stronger than you think.", "georgian": "შენ უფრო ძლიერი ხარ, ვიდრე გგონია.", "pronunciation": "shen up-ro dzli-e-ri khar, vi-dre ggo-ni-a."},
        ],
        "Love": [
            {"english": "Love yourself first.", "georgian": "ჯერ საკუთარი თავი გიყვარდეს.", "pronunciation": "jer sa-ku-ta-ri ta-vi giq-var-des."},
            {"english": "Love makes everything possible.", "georgian": "სიყვარული ყველაფერს შესაძლებელს ხდის.", "pronunciation": "siq-va-ru-li qve-la-pers she-sa-dzle-bels khdis."},
            {"english": "My heart beats for you.", "georgian": "ჩემი გული შენთვის ცემს.", "pronunciation": "che-mi gu-li shen-tvis tsems."},
            {"english": "You are my everything.", "georgian": "შენ ხარ ჩემი ყველაფერი.", "pronunciation": "shen khar che-mi qve-la-pe-ri."},
            {"english": "Together forever, hand in hand.", "georgian": "სამუდამოდ ერთად, ხელი ხელში.", "pronunciation": "sa-mu-da-mod er-tad, khe-li khel-shi."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "georgian": "წარმატება შრომის შედეგია.", "pronunciation": "tsar-ma-te-ba shro-mis she-de-gi-a."},
            {"english": "Keep going, you're getting there.", "georgian": "განაგრძე, შენ იქ ხარ.", "pronunciation": "ga-na-grdze, shen ik khar."},
            {"english": "Winners never quit.", "georgian": "გამარჯვებულები არასოდეს ნებდებიან.", "pronunciation": "ga-mar-jve-bu-le-bi a-ra-so-des neb-de-bi-an."},
            {"english": "Your effort will pay off.", "georgian": "შენი ძალისხმევა გამოიღებს ნაყოფს.", "pronunciation": "she-ni dza-lis-khme-va ga-moi-ghebs na-qops."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "georgian": "ცოდნა ძალაა.", "pronunciation": "tsod-na dzal-aa."},
            {"english": "Learn from yesterday, live for today.", "georgian": "ისწავლე გუშინდელისგან, იცხოვრე დღევანდელისთვის.", "pronunciation": "ists-av-le gu-shin-de-li-sgan, its-kho-vre dghe-van-de-lis-tvis."},
            {"english": "Think before you act.", "georgian": "იფიქრე სანამ იმოქმედებ.", "pronunciation": "i-fi-kre sa-nam i-mok-me-deb."},
            {"english": "Experience is the best teacher.", "georgian": "გამოცდილება საუკეთესო მასწავლებელია.", "pronunciation": "ga-mots-di-le-ba sa-u-ke-te-so mas-tsav-le-be-li-a."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "georgian": "ბედნიერება არჩევანია.", "pronunciation": "bed-ni-e-re-ba ar-che-va-ni-a."},
            {"english": "Find joy in the little things.", "georgian": "იპოვე სიხარული პატარა რაღაცეებში.", "pronunciation": "i-po-ve si-kha-ru-li pa-ta-ra ra-gha-tse-eb-shi."},
            {"english": "Smile, it makes others happy.", "georgian": "გაიღიმე, ეს სხვებს აბედნიერებს.", "pronunciation": "gai-ghi-me, es skhvebs a-bed-ni-e-rebs."},
            {"english": "Today is a gift.", "georgian": "დღევანდელი დღე საჩუქარია.", "pronunciation": "dghe-van-de-li dghe sa-chu-ka-ri-a."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "georgian": "იყავი გუშინდელზე უკეთესი.", "pronunciation": "i-qa-vi gu-shin-del-ze u-ke-te-si."},
            {"english": "Grow through what you go through.", "georgian": "გაიზარდე იმით, რასაც გადიხარ.", "pronunciation": "gai-zar-de i-mit, ra-sats ga-di-khar."},
            {"english": "Invest in yourself daily.", "georgian": "ყოველდღე ჩადე ინვესტიცია საკუთარ თავში.", "pronunciation": "qo-vel-dghe cha-de in-ves-ti-tsi-a sa-ku-tar tav-shi."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "georgian": "მადლობა ყველაფრისთვის.", "pronunciation": "mad-lo-ba qve-la-pri-s-tvis."},
            {"english": "I appreciate your help.", "georgian": "ვაფასებ შენს დახმარებას.", "pronunciation": "va-fa-seb shens da-khma-re-bas."},
            {"english": "Grateful for this moment.", "georgian": "მადლიერი ვარ ამ მომენტისთვის.", "pronunciation": "mad-li-e-ri var am mo-men-tis-tvis."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "georgian": "მეგობრები სამუდამოდ, რაც არ უნდა მოხდეს.", "pronunciation": "me-gob-re-bi sa-mu-da-mod, rats ar unda mokh-des."},
            {"english": "You are my best friend.", "georgian": "შენ ხარ ჩემი საუკეთესო მეგობარი.", "pronunciation": "shen khar che-mi sa-u-ke-te-so me-go-ba-ri."},
            {"english": "True friends stick together.", "georgian": "ნამდვილი მეგობრები ერთად არიან.", "pronunciation": "nam-dvi-li me-gob-re-bi er-tad a-ri-an."},
        ],
        "Hope": [
            {"english": "There is always hope.", "georgian": "იმედი ყოველთვის არსებობს.", "pronunciation": "i-me-di qo-vel-tvis ar-se-bobs."},
            {"english": "Better days are coming.", "georgian": "უკეთესი დღეები მოდის.", "pronunciation": "u-ke-te-si dghe-e-bi mo-dis."},
            {"english": "Keep faith, keep going.", "georgian": "შეინარჩუნე რწმენა, განაგრძე.", "pronunciation": "shei-nar-chu-ne rtsme-na, ga-na-grdze."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "georgian": "შექმენი რაღაც ლამაზი დღეს.", "pronunciation": "shek-me-ni ra-gha-ts la-ma-zi dghes."},
            {"english": "Your imagination is unlimited.", "georgian": "შენი ფანტაზია შეუზღუდავია.", "pronunciation": "she-ni fan-ta-zi-a she-uz-ghu-da-vi-a."},
            {"english": "Art comes from the heart.", "georgian": "ხელოვნება გულიდან მოდის.", "pronunciation": "khe-lov-ne-ba gu-li-dan mo-dis."},
            {"english": "Express yourself freely.", "georgian": "გამოხატე საკუთარი თავი თავისუფლად.", "pronunciation": "ga-mo-kha-te sa-ku-ta-ri ta-vi ta-vi-sup-lad."},
            {"english": "Innovation starts with curiosity.", "georgian": "ინოვაცია ცნობისმოყვარეობით იწყება.", "pronunciation": "i-no-va-tsi-a tsno-bis-mo-qva-re-o-bit its-qe-ba."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "georgian": "იპოვე სიმშვიდე საკუთარ თავში.", "pronunciation": "i-po-ve sim-shvi-de sa-ku-tar tav-shi."},
            {"english": "Breathe, relax, let go.", "georgian": "ისუნთქე, დაისვენე, გაუშვი.", "pronunciation": "i-sun-tqe, dai-sve-ne, gau-shvi."},
            {"english": "Calm mind, happy heart.", "georgian": "მშვიდი გონება, ბედნიერი გული.", "pronunciation": "m-shvi-di go-ne-ba, bed-ni-e-ri gu-li."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "georgian": "შენ საკმარისი ხარ, ისეთი როგორიც ხარ.", "pronunciation": "shen sak-ma-ri-si khar, i-se-ti ro-go-rits khar."},
            {"english": "Stand tall, speak up.", "georgian": "იდექი მაღლა, ილაპარაკე ხმამაღლა.", "pronunciation": "i-de-ki magh-la, i-la-pa-ra-ke khma-magh-la."},
            {"english": "Believe in your abilities.", "georgian": "გჯეროდეს შენი შესაძლებლობების.", "pronunciation": "gje-ro-des she-ni she-sa-dzle-bl-o-be-bis."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "georgian": "არასოდეს დანებდე, განაგრძე წინსვლა.", "pronunciation": "a-ra-so-des da-neb-de, ga-na-grdze tsin-svla."},
            {"english": "Storms make trees take deeper roots.", "georgian": "ქარიშხლები ხეებს უფრო ღრმა ფესვებს აჩენს.", "pronunciation": "ka-rish-khle-bi khe-ebs up-ro ghrm-a pe-svebs a-chens."},
            {"english": "Patience and persistence win.", "georgian": "მოთმინება და გამძლეობა იმარჯვებს.", "pronunciation": "mot-mi-ne-ba da gam-dzle-o-ba i-mar-jvebs."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "georgian": "დაუშვი შენი შუქი კაშკაშა იყოს.", "pronunciation": "dau-shvi she-ni shu-ki kash-ka-sha i-qos."},
            {"english": "Inspire others by your actions.", "georgian": "შთააგონე სხვები შენი ქმედებებით.", "pronunciation": "shta-a-go-ne skhve-bi she-ni km-de-be-bit."},
            {"english": "Be the change you want to see.", "georgian": "იყავი ის ცვლილება, რომლის ნახვაც გინდა.", "pronunciation": "i-qa-vi is tsvi-li-e-ba, rom-lis nakh-vats gin-da."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "georgian": "აირჩიე პოზიტიურობა ყოველ დღე.", "pronunciation": "air-chi-e po-zi-tiu-ro-ba qo-vel dghe."},
            {"english": "Good vibes only.", "georgian": "მხოლოდ კარგი ვიბრაციები.", "pronunciation": "mkho-lod kar-gi vib-ra-tsi-e-bi."},
            {"english": "Life is what you make it.", "georgian": "ცხოვრება ისაა, რასაც შენ შექმნი.", "pronunciation": "tskhov-re-ba i-saa, ra-sats shen shekm-ni."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "georgian": "იყავი მამაცი, გადადგი პირველი ნაბიჯი.", "pronunciation": "i-qa-vi ma-ma-tsi, ga-dad-gi pir-ve-li na-bi-dzhi."},
            {"english": "Courage is not the absence of fear.", "georgian": "გამბედაობა არ ნიშნავს შიშის არ ქონას.", "pronunciation": "gam-be-da-o-ba ar nish-navs shi-shis ar kho-nas."},
            {"english": "Face your fears head on.", "georgian": "შეხვდი შენს შიშებს პირისპირ.", "pronunciation": "shekh-vi shens shi-shebs pi-ris-pir."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "georgian": "იყავი კეთილი ყველას მიმართ, ვისაც ხვდები.", "pronunciation": "i-qa-vi ke-ti-li qve-las mi-mart, vi-sats khvde-bi."},
            {"english": "Kindness costs nothing, means everything.", "georgian": "სიკეთე არაფერი ღირს, მაგრამ ყველაფერს ნიშნავს.", "pronunciation": "si-ke-te a-ra-pe-ri ghirs, ma-gram qve-la-pers nish-navs."},
            {"english": "Spread kindness wherever you go.", "georgian": "გაავრცელე სიკეთე, სადაც არ უნდა წახვიდე.", "pronunciation": "gaa-vr-tse-le si-ke-te, sa-dats ar unda tsa-khvi-de."},
        ],
        "Patience": [
            {"english": "Good things take time.", "georgian": "კარგ რაღაცეებს დრო სჭირდება.", "pronunciation": "karg ra-gha-tse-ebs dro sch-ir-de-ba."},
            {"english": "Wait patiently, trust the process.", "georgian": "დაელოდე მოთმინებით, ენდე პროცესს.", "pronunciation": "da-e-lo-de mot-mi-ne-bit, en-de pro-tsess."},
            {"english": "Rome wasn't built in a day.", "georgian": "რომი არ აშენებულა ერთ დღეში.", "pronunciation": "ro-mi ar a-she-ne-bu-la er-t dghe-shi."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "georgian": "აპატიე და გაათავისუფლე საკუთარი თავი.", "pronunciation": "a-pa-ti-e da gaa-ta-vi-sup-le sa-ku-ta-ri ta-vi."},
            {"english": "Let go of grudges, find peace.", "georgian": "დაივიწყე წყენა, იპოვე სიმშვიდე.", "pronunciation": "dai-vits-qe tsqe-na, i-po-ve sim-shvi-de."},
            {"english": "Forgiveness is a gift to yourself.", "georgian": "პატიება საჩუქარია საკუთარი თავისთვის.", "pronunciation": "pa-ti-e-ba sa-chu-ka-ri-a sa-ku-ta-ri ta-vis-tvis."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "georgian": "შენ უფრო ძლიერი ხარ, ვიდრე თვლი.", "pronunciation": "shen up-ro dzli-e-ri khar, vi-dre tvli."},
            {"english": "Inner strength comes from within.", "georgian": "შინაგანი ძალა შიგნიდან მოდის.", "pronunciation": "shi-na-ga-ni dza-la shig-ni-dan mo-dis."},
            {"english": "Challenges make you stronger.", "georgian": "გამოწვევები გაძლიერებს.", "pronunciation": "ga-mots-ve-ve-bi gadz-li-e-rebs."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "georgian": "იპოვე სიხარული ყოველ წამში.", "pronunciation": "i-po-ve si-kha-ru-li qo-vel tsam-shi."},
            {"english": "Joy is contagious, spread it.", "georgian": "სიხარული გადამდებია, გაავრცელე ის.", "pronunciation": "si-kha-ru-li ga-dam-de-bi-a, gaa-vr-tse-le is."},
            {"english": "Dance like nobody's watching.", "georgian": "იცეკვე ისე, თითქოს არავინ გიყურებს.", "pronunciation": "i-tse-kve i-se, tit-qos a-ra-vin gi-qu-rebs."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "georgian": "იპოვე ბალანსი შენს ცხოვრებაში.", "pronunciation": "i-po-ve ba-lan-si shens tskhov-re-ba-shi."},
            {"english": "Work hard, rest well.", "georgian": "იმუშავე ბევრი, დაისვენე კარგად.", "pronunciation": "i-mu-sha-ve bev-ri, dai-sve-ne kar-gad."},
            {"english": "Too much of anything is not good.", "georgian": "ნებისმიერი რამის ზედმეტობა კარგი არ არის.", "pronunciation": "ne-bis-mi-e-ri ra-mis zed-me-to-ba kar-gi ar a-ris."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "georgian": "ზრდა ხდება შენი კომფორტის ზონის გარეთ.", "pronunciation": "zrda khde-ba she-ni kom-for-tis zo-nis ga-ret."},
            {"english": "Embrace change, grow stronger.", "georgian": "ჩაეხვიე ცვლილებას, გაიზარდე ძლიერად.", "pronunciation": "cha-e-khvi-e tsvi-li-le-bas, gai-zar-de dzli-e-rad."},
            {"english": "Every challenge is a chance to grow.", "georgian": "ყოველი გამოწვევა ზრდის შესაძლებლობაა.", "pronunciation": "qo-ve-li ga-mots-ve-va zr-dis she-sa-dzle-bl-o-ba-a."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "georgian": "იპოვე შენი მიზანი, მიჰყევი მას.", "pronunciation": "i-po-ve she-ni mi-za-ni, mih-qe-vi mas."},
            {"english": "Your life has meaning.", "georgian": "შენს ცხოვრებას აქვს აზრი.", "pronunciation": "shens tskhov-re-bas akvs az-ri."},
            {"english": "Live with intention, not accident.", "georgian": "იცხოვრე განზრახვით, არა შემთხვევით.", "pronunciation": "its-kho-vre gan-zrakh-vit, a-ra shem-tkhve-vit."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "georgian": "იყავი აწმყოში ამ მომენტში.", "pronunciation": "i-qa-vi ats-mqo-shi am mo-ment-shi."},
            {"english": "Breathe deeply, stay grounded.", "georgian": "ისუნთქე ღრმად, დარჩი ფეხზე მყარად.", "pronunciation": "i-sun-tqe ghr-mad, dar-chi pekh-ze mqa-rad."},
            {"english": "Notice the little things around you.", "georgian": "შეამჩნიე პატარა რაღაცეები შენს გარშემო.", "pronunciation": "she-am-chni-e pa-ta-ra ra-gha-tse-e-bi shens gar-she-mo."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["georgian"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        str(BASE_DIR / "fonts" / "NotoSansGeorgian-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansGeorgian-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    georgian = phrase_data.get("georgian", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(georgian, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Georgian Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY GEORGIAN"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_georgian: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansGeorgian-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER GEORGIAN", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_georgian, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 ESSENTIAL PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY GEORGIAN", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_georgian: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Georgian in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_georgian})",
        f"60 Georgian Phrases for {category_english} | Speak Georgian Like a Native! ({category_georgian})",
        f"Master Georgian {category_english} | 60 Essential Georgian Phrases with Pronunciation | Velocity Georgian",
        f"Georgian Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Georgian Fluently | {category_english} Phrases | English + Georgian + Pronunciation",
    ]

    description = f"""🇬🇪 Learn Georgian with Velocity Georgian! 🇬🇪

In this video, you'll learn 60 essential Georgian phrases about {category_english} ({category_georgian}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Georgian
• Correct pronunciation guide
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
📝 ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Georgian: {phrase['georgian']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += """
🎯 PERFECT FOR:
• Georgian beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Georgian language and culture
• Language enthusiasts and polyglots
• Students preparing for exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Georgian learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY GEORGIAN:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Georgian Motivation Phrases
• Georgian Love Expressions
• Basic Georgian Greetings

#LearnGeorgian #GeorgianPhrases #GeorgianLanguage #{category_english.replace(' ', '')} #VelocityGeorgian #GeorgianForBeginners #SpeakGeorgian #GeorgianVocabulary #Pronunciation #LanguageLearning #Georgian101 #GeorgianLesson

---
© Velocity Georgian - Making Georgian learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Georgian",
            "Georgian Phrases",
            "Georgian Language",
            category_english,
            "Velocity Georgian",
            "Georgian for Beginners",
            "Speak Georgian",
            "Georgian Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Georgian 101",
            "Georgian Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_georgian": category_georgian,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_GEORGIAN[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['georgian']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_GEORGIAN[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Georgian: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Georgian", "Georgian Phrases", "Georgian", category_english, "Velocity Georgian"],
        "category_english": category_english,
        "category_georgian": CATEGORIES_GEORGIAN[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Georgian")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Georgian YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY GEORGIAN - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_GEORGIAN[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
