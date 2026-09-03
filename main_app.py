import http.server
import socketserver
import json
import os
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8000
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(DATA_DIR, "static")
INCIDENTS_FILE = os.path.join(DATA_DIR, "incidents.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# Regional Language Translations Dictionary
REGIONAL_TRANSLATIONS = {
    "hi": {
        "calm_lead": "कृपया एक पल रुकिए, गहरी सांस लीजिए।",
        "electricity_warning": "शांत हो जाइए। असली बिजली विभाग या बैंक कभी भी व्हाट्सएप मैसेज पर 1 घंटे में बिजली काटने की धमकी देकर पैसे नहीं मांगते। यह एक जाना-माना फ्रॉड है। आप बिल्कुल सुरक्षित हैं; घबराकर पैसे न भेजें।",
        "family_warning": "एक गहरी सांस लीजिए। स्कैमर्स अक्सर बच्चों या पोते-पोतियों की आवाज की नकल करके या इमरजेंसी का बहाना बनाकर पैसे मांगते हैं। कोई भी पैसा भेजने से पहले अपने बच्चे को उनके असली नंबर पर कॉल करके पुष्टि करें।",
        "police_warning": "रुकिए! असली पुलिस, सीबीआई या कस्टम कभी भी व्हाट्सएप कॉल पर 'डिजिटल अरेस्ट' नहीं करते और न ही सरकारी खातों में पैसे ट्रांसफर करने को कहते हैं। यह डराने का तरीका है।",
        "general_urgent_warning": "कृपया रुकिए। यह मैसेज आपको डराने और जल्दबाजी में गलत फैसला करवाने के लिए भेजा गया है। कोई भी सरकारी या प्राइवेट संस्था ऐसे अचानक पैसे नहीं मांगती। अपने परिवार से बात किए बिना पिन दर्ज न करें।",
        "safe_message": "सब कुछ सामान्य और सुरक्षित लग रहा है। कोई मनोवैज्ञानिक दबाव या धोखाधड़ी नहीं पाई गई। आप सुरक्षित पिन दर्ज कर सकते हैं।",
        "tactics": {
            "Artificial Urgency (Rush Pressure)": "नकली जल्दबाजी (दबाव बनाना)",
            "Fear & Panic Induction": "डर और दहशत पैदा करना",
            "Authority Impersonation": "अधिकारी बनकर धोखा देना",
            "Family Emergency Impersonation": "परिवार का नाम लेकर इमरजेंसी का बहाना",
            "Unsafe Technical Action (Personal Call / Screen Share / Secret PIN)": "संदिग्ध फोन कॉल या स्क्रीन शेयरिंग",
            "Phantom Reward / Fake Lottery": "नकली लॉटरी या इनाम का लालच"
        },
        "actions": [
            "अपना यूपीआई पिन, एटीएम पिन या पासवर्ड बिल्कुल दर्ज न करें।",
            "नीचे 'परिवार को कॉल करें' बटन दबाकर अपने बच्चे से बात करें।",
            "आधिकारिक बिल या ऐप पर जाकर पुष्टि करें।"
        ]
    },
    "ta": {
        "calm_lead": "தயவுசெய்து ஒரு கணம் நில்லுங்கள், நிதானமாக இருங்கள்.",
        "electricity_warning": "பயப்பட வேண்டாம். உண்மையான மின்சார வாரியமோ அல்லது வங்கியோ வாட்ஸ்அப் மூலம் 1 மணிநேரத்தில் மின் இணைப்பைத் துண்டிப்பதாக மிரட்டி பணம் கேட்காது. இது ஒரு மோசடி. நீங்கள் பாதுகாப்பாக இருக்கிறீர்கள்.",
        "family_warning": "நிதானமாக இருங்கள். குடும்பத்தினர் அல்லது பேரப்பிள்ளைகள் ஆபத்தில் இருப்பதாகப் போலியாக நடித்துப் பணம் பறிக்கும் மோசடி இது. பணம் அனுப்பும் முன் உங்கள் குடும்பத்தினரை அவர்களின் பழைய எண்ணில் அழைத்து உறுதிப்படுத்தவும்.",
        "police_warning": "நில்லுங்கள்! உண்மையான காவல்துறை அல்லது சிபிஐ ஒருபோதும் வாட்ஸ்அப்பில் 'டிஜிட்டல் கைது' செய்யாது, பணமும் கேட்காது. இது உங்களை மிரட்டும் தந்திரம்.",
        "general_urgent_warning": "தயவுசெய்து அவசரப்படாதீர்கள். இந்த செய்தி உங்களை பயமுறுத்தி அவசரமாக பணம் அனுப்ப வைக்க வடிவமைக்கப்பட்டுள்ளது. உங்கள் குடும்பத்தினரிடம் பேசாமல் எந்த பின் எண்ணையும் உள்ளிட வேண்டாம்.",
        "safe_message": "அனைத்தும் பாதுகாப்பாகவும் சாதாரணமாகவும் உள்ளது. எந்தவித மோசடி அச்சுறுத்தலும் இல்லை. நீங்கள் தொடரலாம்.",
        "tactics": {
            "Artificial Urgency (Rush Pressure)": "செயற்கை அவசரம் (அழுத்தம் தருதல்)",
            "Fear & Panic Induction": "பயத்தை ஏற்படுத்துதல்",
            "Authority Impersonation": "அதிகாரி போல் ஆள்மாறாட்டம்",
            "Family Emergency Impersonation": "குடும்ப அவசரநிலை ஆள்மாறாட்டம்",
            "Unsafe Technical Action (Personal Call / Screen Share / Secret PIN)": "பாதுகாப்பற்ற அழைப்பு / ஸ்கிரீன் ஷேரிங்",
            "Phantom Reward / Fake Lottery": "போலி பரிசு / லாட்டரி ஆசை"
        },
        "actions": [
            "உங்கள் UPI PIN அல்லது வங்கி கடவுச்சொல்லை உள்ளிட வேண்டாம்.",
            "கீழே உள்ள 'குடும்பத்தை அழைக்கவும்' பொத்தானை அழுத்தவும்.",
            "அதிகாரப்பூர்வ பயன்பாட்டில் நேரடியாக சரிபார்க்கவும்."
        ]
    },
    "te": {
        "calm_lead": "దయచేసి ఒక్క క్షణం ఆగండి, ప్రశాంతంగా ఉండండి.",
        "electricity_warning": "కంగారు పడకండి. నిజమైన విద్యుత్ శాఖ లేదా బ్యాంకులు వాట్సాప్ సందేశాల ద్వారా గంటలో విద్యుత్ కట్ చేస్తామని బెదిరించి డబ్బులు అడగవు. ఇది సైబర్ మోసం. మీరు పూర్తిగా సురక్షితంగా ఉన్నారు.",
        "family_warning": "ప్రశాంతంగా ఆలోచించండి. బంధువులు లేదా పిల్లలు అత్యవసర పరిస్థితిలో ఉన్నారని నకిలీ సందేశాలు పంపే మోసం ఇది. ఎవరికీ డబ్బు పంపే ముందు మీ కుటుంబ సభ్యులకు నేరుగా కాల్ చేసి మాట్లాడండి.",
        "police_warning": "ఆగండి! నిజమైన పోలీసులు లేదా సీబీఐ వాట్సాప్‌లో 'డిజిటల్ అరెస్ట్' చేయరు లేదా డబ్బు డిమాండ్ చేయరు. ఇది మిమ్మల్ని భయపెట్టే కుట్ర.",
        "general_urgent_warning": "దయచేసి ఆగండి. మిమ్మల్ని తొందరపెట్టి భయంతో డబ్బులు చెల్లించేలా చేయడానికి ఈ సందేశం పంపబడింది. కుటుంబ సభ్యులతో మాట్లాడకుండా పిన్ నంబర్ నమోదు చేయవద్దు.",
        "safe_message": "అంతా సురక్షితంగా మరియు సాధారణంగా కనిపిస్తోంది. ఎటువంటి మోసం లేదు. మీరు లావాదేవీని కొనసాగించవచ్చు.",
        "tactics": {
            "Artificial Urgency (Rush Pressure)": "నకిలీ తొందరపాటు (ఒత్తిడి)",
            "Fear & Panic Induction": "భయం మరియు ఆందోళన కలిగించడం",
            "Authority Impersonation": "అధికారిలా మోసం చేయడం",
            "Family Emergency Impersonation": "కుటుంబ అత్యవసర పరిస్థితి నకిలీ",
            "Unsafe Technical Action (Personal Call / Screen Share / Secret PIN)": "అనుమానాస్పద కాల్ లేదా స్క్రీన్ షేర్",
            "Phantom Reward / Fake Lottery": "నకిలీ లాటరీ లేదా బహుమతి"
        },
        "actions": [
            "మీ UPI పిన్ లేదా పాస్‌వర్డ్ ఎవరికీ చెప్పవద్దు, నమోదు చేయవద్దు.",
            "క్రింద ఉన్న 'కుటుంబానికి కాల్ చేయండి' బటన్ నొక్కండి.",
            "అధికారిక బిల్లు వివరాలు నేరుగా పరిశీలించండి."
        ]
    },
    "mr": {
        "calm_lead": "कृपया एक क्षण थांबा, शांतपणे विचार करा.",
        "electricity_warning": "घाबरू नका. वीज महावितरण किंवा बँक कधीही व्हॉट्सअॅपवर १ तासात वीज कापण्याची धमकी देऊन पैशांची मागणी करत नाही. हा एक ज्ञात सायबर स्कॅम आहे. तुम्ही सुरक्षित आहात.",
        "family_warning": "शांत राहा. स्कॅमर्स अनेकदा मुले किंवा नातवंडे संकटात असल्याचे नाटक करून पैसे उकळतात. कोणतेही पैसे पाठवण्यापूर्वी तुमच्या मुलाला थेट त्यांच्या मूळ नंबरवर फोन करा.",
        "police_warning": "थांबा! खरी पोलीस यंत्रणा किंवा सीबीआय कधीही व्हॉट्सअॅपवर 'डिजिटल अटक' करत नाही आणि पैसे ट्रान्सफर करायला सांगत नाही. हा भीती दाखवण्याचा प्रकार आहे.",
        "general_urgent_warning": "कृपया घाई करू नका. हा संदेश तुम्हाला घाबरवून त्वरित निर्णय घेण्यास भाग पाडण्यासाठी पाठवला गेला आहे. कुटुंबाशी बोलल्याशिवाय पिन टाकू नका.",
        "safe_message": "सर्व काही सामान्य आणि सुरक्षित वाटत आहे. कोणताही फसवणुकीचा धोका आढळला नाही. तुम्ही पुढे जाऊ शकता.",
        "tactics": {
            "Artificial Urgency (Rush Pressure)": "कृत्रिम घाई (मानसिक दबाव)",
            "Fear & Panic Induction": "भीती व दहशत निर्माण करणे",
            "Authority Impersonation": "अधिकारी असल्याचा बनाव",
            "Family Emergency Impersonation": "कुटुंबातील व्यक्तीचे सोंग",
            "Unsafe Technical Action (Personal Call / Screen Share / Secret PIN)": "संशयास्पद कॉल किंवा स्क्रीन शेअरिंग",
            "Phantom Reward / Fake Lottery": "खोट्या लॉटरीचे आमिष"
        },
        "actions": [
            "तुमचा यूपीआय पिन किंवा बँक पासवर्ड अजिबात टाकू नका.",
            "खालील 'कुटुंबाशी संपर्क साधा' बटण दाबून खात्री करा.",
            "अधिकृत वीज बिल किंवा ॲपवर जाऊन माहिती तपासा."
        ]
    },
    "bn": {
        "calm_lead": "দয়া করে এক মুহূর্ত থামুন, শান্ত হোন।",
        "electricity_warning": "আতঙ্কিত হবেন না। আসল বিদ্যুৎ দপ্তর বা ব্যাঙ্ক কখনও হোয়াটসঅ্যাপে ১ ঘণ্টার মধ্যে বিদ্যুৎ সংযোগ কাটার হুমকি দিয়ে টাকা দাবি করে না। এটি একটি প্রতারণা। আপনি সুরক্ষিত আছেন।",
        "family_warning": "শান্তভাবে চিন্তা করুন। প্রতারকরা প্রায়শই সন্তান বা নাতি-নাতনি বিপদে পড়েছে বলে অভিনয় করে টাকা চায়। টাকা পাঠানোর আগে আপনার পরিবারকে সরাসরি ফোন করুন।",
        "police_warning": "থামুন! আসল পুলিশ বা সিবিআই কখনও হোয়াটসঅ্যাপে 'ডিজিটাল অ্যারেস্ট' করে না বা টাকা দাবি করে না। এটি ভয় দেখানোর চক্রান্ত।",
        "general_urgent_warning": "দয়া করে তাড়াহুড়ো করবেন না। এই বার্তাটি আপনাকে ভয় দেখিয়ে দ্রুত টাকা পাঠানোর জন্য তৈরি করা হয়েছে। পরিবারের সাথে কথা না বলে পিন দেবেন না।",
        "safe_message": "সবকিছু স্বাভাবিক ও নিরাপদ দেখাচ্ছে। কোনো প্রতারণার লক্ষণ নেই। আপনি পিন দিতে পারেন।",
        "tactics": {
            "Artificial Urgency (Rush Pressure)": "কৃত্রিম তাড়া (মানসিক চাপ)",
            "Fear & Panic Induction": "ভয় ও আতঙ্ক সৃষ্টি",
            "Authority Impersonation": "আধিকারিক সেজে প্রতারণা",
            "Family Emergency Impersonation": "পারিবারিক বিপদের ভান",
            "Unsafe Technical Action (Personal Call / Screen Share / Secret PIN)": "সন্দেহজনক কল বা স্ক্রিন শেয়ার",
            "Phantom Reward / Fake Lottery": "ভুয়ো লটারির লোভ"
        },
        "actions": [
            "আপনার ইউপিআই পিন বা ব্যাঙ্কের পাসওয়ার্ড দেবেন না।",
            "নিচে 'পরিবারকে ফোন করুন' বাটনে ক্লিক করে কথা বলুন।",
            "অফিসিয়াল বিলিং পোর্টালে সরাসরি যাচাই করুন।"
        ]
    }
}

# Default caregiver settings
DEFAULT_SETTINGS = {
    "caregiver_name": "Rahul Sharma (Son)",
    "caregiver_phone": "+91 98765 43210",
    "risk_threshold": 70,
    "voice_mode_enabled": True,
    "senior_mode_default": True
}

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filepath}: {e}")

# Cognitive Heuristic Scam Engine
def cognitive_scam_analysis(text: str, amount: float, recipient: str = "", lang: str = "en") -> dict:
    """
    Analyzes incoming text for psychological manipulation tactics commonly
    used to defraud senior citizens and vulnerable users, with native regional language support.
    """
    text_lower = text.lower()
    
    tactics = []
    red_flags = []
    score = 5

    # 1. Artificial Urgency
    urgency_patterns = [
        r"\b(urgent|urgently|immediately|immediate|hurry|quick|fast|now)\b",
        r"\b(1 hour|2 hours|30 mins|tonight|today|by tonight|before midnight|in \d+ (minutes|hours|mins))\b",
        r"\b(at \d{1,2}(:\d{2})?\s*(am|pm)?)\b",
        r"\b(deadline|time is running out|last chance|final notice|expires|unpaid)\b"
    ]
    for pattern in urgency_patterns:
        if re.search(pattern, text_lower):
            tactics.append("Artificial Urgency (Rush Pressure)")
            red_flags.append("Creates an artificial time deadline to prevent you from thinking calmly.")
            score += 25
            break

    # 2. Fear & Coercion / Service Cutoff
    fear_patterns = [
        r"\b(police|cbi|ed|court|fir|arrest|digital arrest|warrant|jail|prison)\b",
        r"\b(illegal|narcotics|customs|contraband|penalty|legal action|fine)\b",
        r"\b(blocked|frozen|suspended|deactivated|cancelled|locked)\b",
        r"\b(cut off|disconnect|disconnection|terminated|shut off)\b",
        r"\b(power|electricity|water|gas|sim|service)\b.{0,25}\b(cut|stop|suspend|terminate|off)\b"
    ]
    for pattern in fear_patterns:
        if re.search(pattern, text_lower):
            tactics.append("Fear & Panic Induction")
            red_flags.append("Threatens punishment, arrest, or service disconnection to scare you into paying.")
            score += 30
            break

    # 3. Authority Impersonation
    authority_patterns = [
        r"\b(electricity|power|bijli|board|dept|department|office|officer|discom|bses|uppcl|tneb|mseb|bescom|wbsetcl)\b",
        r"\b(sbi|hdfc|icici|pnb|axis|rbi|bank manager|kyc officer|telecom|trai|income tax)\b",
        r"\b(cbi|cyber crime|customs|delhi police|mumbai police|police officer|inspector)\b"
    ]
    for pattern in authority_patterns:
        if re.search(pattern, text_lower):
            tactics.append("Authority Impersonation")
            red_flags.append("Claims to represent a government agency, police, or bank without official channel proof.")
            score += 25
            break

    # 4. Family Distress / Impersonation (Grandson/Son Scam)
    family_patterns = [
        r"\b(accident|hospital|emergency|stuck|bail|bail out|lost phone)\b",
        r"\b(son|daughter|grandson|granddaughter|dad|mom|grandpa|grandma|uncle|aunt)\b",
        r"\b(don't tell|don't call my old number|new number|friend's phone|secret)\b"
    ]
    family_matches = 0
    for pattern in family_patterns:
        if re.search(pattern, text_lower):
            family_matches += 1
    if family_matches >= 2:
        tactics.append("Family Emergency Impersonation")
        red_flags.append("Pretends to be a relative in trouble asking for secretive money.")
        score += 35

    # 5. Dangerous Channel / Coercion Mechanisms
    tech_coercion_patterns = [
        r"\b(anydesk|teamviewer|rustdesk|quicksupport|screen share)\b",
        r"\b(apk|download app|click this link|bit\.ly|tinyurl|wa\.me)\b",
        r"\b(share otp|enter pin|card details|cvv|secret code)\b",
        r"\b(contact|call|reach|message)\b.{0,30}\b(officer|helpline|number|desk|\d{5,})\b"
    ]
    for pattern in tech_coercion_patterns:
        if re.search(pattern, text_lower):
            tactics.append("Unsafe Technical Action (Personal Call / Screen Share / Secret PIN)")
            red_flags.append("Asks you to download apps, call a random mobile number, or share confidential codes.")
            score += 25
            break

    # 6. Phantom Reward / Lottery
    lottery_patterns = [
        r"\b(lottery|won|winner|cash prize|jackpot|reward point|cashback|kbc)\b"
    ]
    for pattern in lottery_patterns:
        if re.search(pattern, text_lower):
            tactics.append("Phantom Reward / Fake Lottery")
            red_flags.append("Offers sudden unearned prizes or refunds requiring a processing deposit.")
            score += 25
            break

    # Financial Exposure Weighting
    if amount >= 25000:
        score += 15
    elif amount >= 5000:
        score += 10
    elif amount >= 2000:
        score += 5

    # Clamp score
    score = min(98, max(5, score))

    # Determine risk category
    if score >= 70:
        risk_level = "CRITICAL_HAZARD"
        is_blocked = True
    elif score >= 40:
        risk_level = "SUSPICIOUS"
        is_blocked = False
    else:
        risk_level = "SAFE"
        is_blocked = False

    # Generate tailored empathetic warning (with regional language support)
    trans = REGIONAL_TRANSLATIONS.get(lang)

    if trans:
        calm_lead = trans["calm_lead"]
        if "Family Emergency Impersonation" in tactics:
            empathetic_warning = f"{calm_lead} {trans['family_warning']}"
        elif "Fear & Panic Induction" in tactics or "Authority Impersonation" in tactics:
            empathetic_warning = f"{calm_lead} {trans['electricity_warning']}"
        elif score >= 70:
            empathetic_warning = f"{calm_lead} {trans['general_urgent_warning']}"
        elif score >= 40:
            empathetic_warning = f"{calm_lead} {trans['general_urgent_warning']}"
        else:
            empathetic_warning = trans["safe_message"]

        # Localized tactics
        localized_tactics = [trans["tactics"].get(t, t) for t in tactics] if tactics else ["सुरक्षित (Authentic)"]
        actionable_steps = trans["actions"] if is_blocked else [trans["actions"][0]]
    else:
        if "Family Emergency Impersonation" in tactics:
            empathetic_warning = (
                "Take a deep breath. Scammers frequently use AI voice cloning or fake text messages "
                "pretending to be children or grandchildren in an emergency. Real emergencies are handled "
                "through official hospital or police numbers. Please call your family member directly on their "
                "saved phone number before sending a single rupee."
            )
        elif "Authority Impersonation" in tactics and "Fear & Panic Induction" in tactics:
            empathetic_warning = (
                "Hold on for just a moment. Genuine government bodies, police departments, and electricity boards "
                "never disconnect your power within 1 hour or demand instant money transfers over WhatsApp. "
                "This is a known high-pressure scam. You are completely safe; do not rush into this payment."
            )
        elif "Artificial Urgency (Rush Pressure)" in tactics or score >= 70:
            empathetic_warning = (
                "Please pause and take a calm breath. The message you received is deliberately engineered to create "
                "intense urgency and panic. Legitimate utilities and organizations send official postal notices or "
                "monthly billing cycles, never sudden instant payment ultimatums. Let's verify this together with your family."
            )
        elif score >= 40:
            empathetic_warning = (
                "Notice: This message contains unusual urgency cues. While it might be valid, it's wise to double check "
                "the official app or bill statement before entering your confidential PIN."
            )
        else:
            empathetic_warning = (
                "Everything looks normal and calm. No psychological manipulation or rush tactics were detected. "
                "You can proceed safely with your secure PIN."
            )

        localized_tactics = tactics if tactics else ["None (Authentic Tone)"]
        actionable_steps = []
        if is_blocked:
            actionable_steps.append("Do NOT enter your UPI PIN, ATM PIN, or Net Banking password.")
            actionable_steps.append("Tap 'Call Trusted Family' below to speak with your child or caregiver.")
            actionable_steps.append("Check your official utility bill on the official provider website or physical bill.")
        else:
            actionable_steps.append("Confirm the recipient name matches your expected vendor.")
            actionable_steps.append("Enter your PIN securely without showing your screen to anyone.")

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "is_blocked": is_blocked,
        "manipulation_tactics": localized_tactics,
        "red_flags": red_flags,
        "empathetic_warning": empathetic_warning,
        "actionable_steps": actionable_steps,
        "lang": lang,
        "engine": "FinAngel Cognitive Heuristic Engine",
        "timestamp": datetime.now().isoformat()
    }

# LLM Gemini Integration if API key is provided
def call_gemini_analysis(text: str, amount: float, api_key: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    system_prompt = (
        "You are FinAngel, an empathetic AI guardian integrated into a banking app for senior citizens. "
        "Analyze the user's incoming text and transaction context for psychological manipulation: "
        "artificial urgency, fear induction, fake utility threats, police/digital arrest threats, or impersonation of loved ones. "
        "Output ONLY raw JSON with keys: 'risk_score' (0-100 integer), 'manipulation_tactics' (array of strings), "
        "'empathetic_warning' (warm, calm, comforting explanation in simple language explaining why to pause without technical jargon), "
        "'actionable_steps' (array of 2-3 simple steps)."
    )
    payload = {
        "contents": [{
            "parts": [{
                "text": f"System: {system_prompt}\n\nIncoming Context: '{text}'\nTransaction Amount: ₹{amount}"
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
        candidate_text = result["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(candidate_text)
        score = int(parsed.get("risk_score", 50))
        return {
            "risk_score": score,
            "risk_level": "CRITICAL_HAZARD" if score >= 70 else ("SUSPICIOUS" if score >= 40 else "SAFE"),
            "is_blocked": score >= 70,
            "manipulation_tactics": parsed.get("manipulation_tactics", []),
            "red_flags": ["LLM-detected cognitive manipulation marker"],
            "empathetic_warning": parsed.get("empathetic_warning", ""),
            "actionable_steps": parsed.get("actionable_steps", ["Call a trusted family member.", "Do not enter your PIN."]),
            "engine": "Google Gemini 2.5 Flash",
            "timestamp": datetime.now().isoformat()
        }

# Realistic Presets
SCAM_PRESETS = [
    {
        "id": "electricity_scam",
        "title": "⚡ Electricity Disconnection Threat",
        "badge": "Very Common Scam",
        "amount": 4850,
        "recipient": "PowerDesk Helpline",
        "text": "URGENT: Your electricity power will be cut off tonight at 9:30 PM from electricity office because your previous month bill was not updated. Please immediately contact our power officer at 98112-XXXXX or pay ₹4,850 now to avoid disconnection."
    },
    {
        "id": "digital_arrest",
        "title": "🚔 Fake CBI 'Digital Arrest' Threat",
        "badge": "High Pressure Police Threat",
        "amount": 50000,
        "recipient": "Cyber Crime Verification Acct",
        "text": "OFFICIAL NOTICE from CBI / Mumbai Police: A courier parcel containing illegal passports and drugs has been intercepted under your Aadhaar number. A warrant for Digital Arrest has been issued. Transfer ₹50,000 security bond immediately to government verification account to avoid immediate physical arrest."
    },
    {
        "id": "grandson_emergency",
        "title": "🏥 Grandchild Hospital Emergency",
        "badge": "Family Impersonation",
        "amount": 25000,
        "recipient": "Emergency Clinic Dr. Mehta",
        "text": "Grandma, please don't panic! It's Rohit. I met with a small scooter accident and my phone screen shattered. I am at the emergency clinic and need ₹25,000 for hospital deposit right now. Don't call mom or dad yet, they will get too worried. Please send it urgently to this clinic UPI."
    },
    {
        "id": "kyc_suspension",
        "title": "🏦 Bank Account / KYC Frozen Threat",
        "badge": "Banking Phishing",
        "amount": 9999,
        "recipient": "SBI FastKYC Desk",
        "text": "Dear Customer, Your SBI bank account services will be blocked within 24 hours because PAN-KYC is not updated. Click here wa.me/9188888 or transfer ₹9,999 refundable verification deposit to re-activate your net banking access immediately."
    },
    {
        "id": "safe_grocery",
        "title": "🥦 Normal Grocery / Milk Payment",
        "badge": "Legitimate Safe Transaction",
        "amount": 450,
        "recipient": "Sharmaji Fresh Vegetables",
        "text": "Monthly milk and fresh vegetables total: ₹450. Thank you for your continued patronage! GPay / PhonePe to 98765-XXXXX when convenient."
    }
]

class FinAngelHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if parsed_url.path == "/api/presets":
            self.send_json_response(SCAM_PRESETS)
        elif parsed_url.path == "/api/settings":
            settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
            self.send_json_response(settings)
        elif parsed_url.path == "/api/incidents":
            incidents = load_json(INCIDENTS_FILE, [])
            self.send_json_response(incidents)
        elif parsed_url.path == "/api/whatsapp/webhook":
            # Standard Meta WhatsApp Cloud API Webhook Handshake
            hub_challenge = query_params.get("hub.challenge", [""])[0]
            if hub_challenge:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(hub_challenge.encode("utf-8"))
            else:
                self.send_json_response({"status": "FinAngel WhatsApp Webhook Active", "challenge_required": False})
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        try:
            data = json.loads(body) if body else {}
        except Exception as e:
            print(f"JSON decode warning: {e} - Raw body: {body[:100]}")
            self.send_error(400, f"Invalid JSON payload: {e}")
            return

        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path == "/api/analyze":
            text = data.get("text", "")
            amount = float(data.get("amount", 0))
            recipient = data.get("recipient", "")
            lang = data.get("lang", "en")
            api_key = os.environ.get("GEMINI_API_KEY", "").strip() or data.get("gemini_api_key", "").strip()

            result = None
            if api_key:
                try:
                    result = call_gemini_analysis(text, amount, api_key)
                except Exception as e:
                    print(f"Gemini API fallback to Heuristic Engine: {e}")
            
            if not result:
                result = cognitive_scam_analysis(text, amount, recipient, lang)

            # Auto log incident
            incidents = load_json(INCIDENTS_FILE, [])
            incident_entry = {
                "id": f"INC-{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                "recipient": recipient or "Unknown Recipient",
                "amount": amount,
                "risk_score": result["risk_score"],
                "risk_level": result["risk_level"],
                "is_blocked": result["is_blocked"],
                "tactics": result["manipulation_tactics"],
                "text_snippet": (text[:90] + "...") if len(text) > 90 else text
            }
            incidents.insert(0, incident_entry)
            save_json(INCIDENTS_FILE, incidents[:50])

            self.send_json_response(result)

        elif parsed_url.path == "/api/whatsapp/bot":
            # Dedicated WhatsApp Bot response for incoming forwarded messages
            incoming_msg = data.get("message", "").strip()
            lang = data.get("lang", "en")
            
            # Extract possible amount if mentioned in message (e.g. ₹5,000 or Rs 5000)
            amt_match = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+)", incoming_msg, re.IGNORECASE)
            detected_amount = 5000
            if amt_match:
                try:
                    detected_amount = float(amt_match.group(1).replace(",", ""))
                except Exception:
                    pass

            result = cognitive_scam_analysis(incoming_msg, detected_amount, "WhatsApp Forward", lang)
            
            settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
            caregiver_name = settings.get("caregiver_name", "Rahul (Son)")
            caregiver_phone = settings.get("caregiver_phone", "+919876543210")
            clean_phone = re.sub(r"[^\d+]", "", caregiver_phone)

            # Pre-generate SOS WhatsApp URL for the caregiver
            sos_text = (
                f"🚨 *FinAngel Safety Alert on Dad's Phone*\n\n"
                f"A scam message was detected:\n"
                f"\"{incoming_msg[:80]}...\"\n\n"
                f"⚠️ *Risk Score:* {result['risk_score']}/100 ({result['risk_level']})\n"
                f"🛑 *Threats:* {', '.join(result['manipulation_tactics'])}\n"
                f"💡 *Action:* Please call Dad immediately to check."
            )
            sos_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(sos_text)}"

            bot_reply = {
                "risk_score": result["risk_score"],
                "risk_level": result["risk_level"],
                "is_blocked": result["is_blocked"],
                "empathetic_warning": result["empathetic_warning"],
                "tactics": result["manipulation_tactics"],
                "actionable_steps": result["actionable_steps"],
                "sos_url": sos_url,
                "caregiver_name": caregiver_name,
                "caregiver_phone": caregiver_phone
            }
            self.send_json_response(bot_reply)

        elif parsed_url.path == "/api/whatsapp/webhook":
            # Incoming Webhook from Twilio or Meta WhatsApp Business API
            print(f"Received WhatsApp webhook POST payload: {body[:200]}")
            self.send_json_response({"status": "received", "handled_by": "FinAngel Guardian Webhook"})

        elif parsed_url.path == "/api/settings":
            settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
            settings.update(data)
            save_json(SETTINGS_FILE, settings)
            self.send_json_response({"status": "success", "settings": settings})

        elif parsed_url.path == "/api/call_family":
            settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
            contact_name = settings.get("caregiver_name", "Rahul Sharma (Son)")
            contact_phone = settings.get("caregiver_phone", "+91 98765 43210")
            clean_phone = re.sub(r"[^\d+]", "", contact_phone)
            
            # Format real wa.me dispatch URL
            sos_text = (
                f"🚨 *FinAngel Guardian Alert*\n\n"
                f"High-risk transaction of ₹{data.get('amount', 0)} for '{data.get('recipient', 'recipient')}' "
                f"was just intercepted on your parent's phone.\n"
                f"Please verify with them right now."
            )
            wa_link = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(sos_text)}"

            self.send_json_response({
                "status": "connected",
                "contact_name": contact_name,
                "contact_phone": contact_phone,
                "wa_link": wa_link,
                "message": f"Calling {contact_name} ({contact_phone}). Please hold the phone to your ear."
            })
        else:
            self.send_error(404, "Endpoint Not Found")

    def send_json_response(self, obj):
        response_bytes = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

def run_server():
    server_address = ("", PORT)
    with socketserver.TCPServer(server_address, FinAngelHandler) as httpd:
        print(f"\n========================================================")
        print(f" 🛡️  FinAngel Guardian AI Shield Running at: http://localhost:{PORT}")
        print(f" Active Protections: Cognitive Scam Blocker, Voice Guardian, Family Alert")
        print(f" Press Ctrl+C to stop the server")
        print(f"========================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down FinAngel Guardian...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
