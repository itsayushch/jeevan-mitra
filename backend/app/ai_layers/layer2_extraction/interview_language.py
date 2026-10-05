"""Natural reply interpretation and varied, one-question follow-ups."""
import re

NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
    'twelve': 12, 'fifteen': 15, 'twenty': 20, 'thirty': 30, 'fifty': 50,
    'hundred': 100, 'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5,
    'पाँच': 5, 'छह': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
    'ग्यारह': 11, 'बारह': 12, 'बीस': 20, 'पचास': 50,
    'ek': 1, 'do': 2, 'teen': 3, 'chaar': 4, 'panch': 5, 'paanch': 5,
    'aath': 8, 'nau': 9, 'das': 10, 'dus': 10, 'bees': 20,
}
ORDINALS = {
    'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
    'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
    'eleventh': 11, 'twelfth': 12, 'पांचवीं': 5, 'पाँचवीं': 5,
    'आठवीं': 8, 'नौवीं': 9, 'दसवीं': 10, 'ग्यारहवीं': 11, 'बारहवीं': 12,
    'panchvi': 5, 'aathvi': 8, 'nauvi': 9, 'dasvi': 10, 'barahvi': 12,
}
UNKNOWN = re.compile(r"^(?:i (?:don't|do not) know|don't know|do not know|not sure|unknown|skip|no idea|पता नहीं|मालूम नहीं|नहीं पता|pata nahi)[.!।\s]*$", re.I)

FIELD_PATTERNS = {
    'district': r'\bdistrict\b|जिल', 'block': r'\bblock\b|ब्लॉक|विकासखंड',
    'education': r'education|school|class|stud(?:y|ied)|पढ़|पढ|कक्षा|पढ़ाई',
    'interests': r'like to learn|want to learn|interest|enjoy.*learn|work.*(?:enjoy|try)|सीख|रुचि|काम.*(?:अच्छा|पसंद)',
    'mobility': r'kilomet|\bkm\b|travel|distance|किलोमीटर|दूरी|यात्रा',
    'self_employment_or_wage_preference': r'self.employ|own business|prefer.*job|job.*either|job or|नौकरी|स्वरोजगार',
    'traditional_or_existing_skills': r'already.*skill|skills.*already|पहले से.*कौशल',
    'current_work': r'currently.*work|work.*currently|अभी.*काम',
    'access_needs': r'accessibility|पहुँच.*सहायता',
}

def question_field(turn):
    if turn.get('field') in FIELD_PATTERNS:
        return turn['field']
    text = turn.get('text', '').lower()
    sentences = [part.strip() for part in re.split(r'[.!?।]', text) if part.strip()]
    for sentence in reversed(sentences or [text]):
        field = next((field for field, pattern in FIELD_PATTERNS.items() if re.search(pattern, sentence)), None)
        if field: return field
    return None

def spoken_number(text):
    """Accept a single explicit number, including number words, without guessing ranges."""
    text = text.lower().strip()
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    numbers += [str(NUMBER_WORDS[word]) for word in re.split(r'[\s,;.!?।]+', text) if word in NUMBER_WORDS]
    if len(numbers) != 1:
        return None
    return float(numbers[0])

def distance_answer(text):
    # A range needs clarification; choosing either end would invent a constraint.
    number_token = r'(?:-?\d+(?:\.\d+)?|' + '|'.join(re.escape(word) for word in NUMBER_WORDS) + r')'
    if re.search(r'(?<!\w)' + number_token + r'\s*(?:to|से|[-–])\s*' + number_token, text, re.I): return None
    unit = re.search(r'(-?\d+(?:\.\d+)?|[^\s,;.!?।]+)\s*(?:km\b|kilomet(?:re|er)s?\b|किमी|किलोमीटर)', text, re.I)
    return spoken_number(unit.group(1) if unit else text)

def education_answer(text, direct=False):
    if not isinstance(text, str): return None
    lower = text.lower().strip(' .!?।')
    if UNKNOWN.fullmatch(lower): return None
    if re.search(r'no formal education|never went to school|did not (?:go|attend).*school|अनपढ़|स्कूल नहीं|पढ़ाई नहीं', lower): return 'No formal education'
    if re.search(r'post.?graduate|masters|एम\.?ए|स्नातकोत्तर', lower): return 'Post Graduate'
    if re.search(r'graduate|bachelor|\b(?:b\.?a\.?|b\.?sc|b\.?com|b\.?tech)\b|स्नातक', lower): return 'Graduate'
    if re.search(r'\biti\b|diploma|डिप्लोमा|आईटीआई', lower): return 'ITI / Diploma'
    if re.search(r'\bmatric(?:ulation)?\b|\bssc\b', lower): return 'Class 10'
    if re.search(r'\bintermediate\b|\bhsc\b', lower): return 'Class 12'
    # A failed/current class is not evidence of completing that class.
    if re.search(r'failed|studying|currently|फेल|पढ़ रहा|पढ़ रही', lower): return None
    explicit = re.search(r'(?:class|grade|कक्षा)\s*(\d{1,2})\b|\b(\d{1,2})(?:st|nd|rd|th)\b', lower)
    if explicit:
        number = int(explicit.group(1) or explicit.group(2))
        return f'Class {number}' if 1 <= number <= 12 else None
    school_context = direct or bool(re.search(r'class|grade|school|studied|passed|पढ़|पढ|पास|कक्षा', lower))
    ordinal = next((value for word, value in ORDINALS.items() if re.search(r'(?<!\w)' + re.escape(word) + r'(?!\w)', lower)), None)
    number = spoken_number(re.sub(r'(?<=\d)(?:st|nd|rd|th)\b', '', lower))
    if ordinal is not None: return f'Class {ordinal}'
    if school_context and number is not None and number.is_integer() and 1 <= number <= 12: return f'Class {int(number)}'
    return None

def preference_answer(text):
    if not isinstance(text, str): return None
    text = text.lower().strip()
    if re.search(r'\bboth\b|\beither\b|anything.*(?:fine|okay)|no preference|दोनों|कोई भी|koi bhi|dono', text): return 'both'
    if re.search(r'self.employ|own (?:business|work|shop)|business|स्वरोजगार|अपना.*(?:काम|व्यवसाय|दुकान)|khud ka|apna kaam', text): return 'self_employment'
    if re.search(r'\bwage\b|\bjob\b|\bsalar(?:y|ied)\b|नौकरी|naukri', text): return 'wage'
    return None

FOLLOWUPS = {
    'district': (
        ('What is the name of your district? Just its name is enough.', 'आपके जिले का नाम क्या है? केवल नाम बताना भी ठीक है।'),
        ('Which district is your village or town in?', 'आपका गाँव या शहर किस जिले में है?'),
        ('Could you tell me your district in your own words?', 'अपने जिले का नाम जैसे बोलते हैं, वैसे बता सकते हैं?')),
    'block': (
        ('What is your block called? A short name is fine.', 'आपके ब्लॉक का नाम क्या है? केवल नाम बता दें।'),
        ('Which development block does your village come under?', 'आपका गाँव किस विकासखंड में आता है?'),
        ('Do you know the block name used for your village?', 'आपके गाँव के लिए कौन सा ब्लॉक नाम इस्तेमाल होता है?')),
    'education': (
        ('What was the last class you passed? You can say just the class number.', 'आपने आखिरी कौन सी कक्षा पास की है? केवल कक्षा का नंबर भी बता सकते हैं।'),
        ('How far did you study? School, ITI or a degree are all okay to mention.', 'आपने कहाँ तक पढ़ाई की है? स्कूल, आईटीआई या डिग्री, जो किया हो बता दें।'),
        ('What schooling or qualification have you completed?', 'आपने कौन सी पढ़ाई या योग्यता पूरी की है?')),
    'interests': (
        ('What work sounds interesting to you? Tell me in your own words.', 'आपको कौन सा काम अच्छा लगता है? अपने शब्दों में बताएँ।'),
        ('What would you enjoy learning to do?', 'आप किस काम को सीखना पसंद करेंगे?'),
        ('Is there a kind of work you would like to try?', 'क्या कोई काम है जिसे आप सीखकर करना चाहेंगे?')),
    'mobility': (
        ('Roughly how far can you travel? A number is fine, or say if you cannot travel.', 'आप लगभग कितनी दूर जा सकते हैं? नंबर बता दें, या कहें कि यात्रा नहीं कर सकते।'),
        ('About how many kilometres would be comfortable for you?', 'आपके लिए लगभग कितने किलोमीटर जाना आसान होगा?'),
        ('What travel distance would work for you, even approximately?', 'आप कितनी दूरी तक जा सकते हैं? अंदाज़ा भी ठीक है।')),
    'self_employment_or_wage_preference': (
        ('Would you like to work for someone, do your own work, or keep both options open?', 'आप किसी के यहाँ काम करेंगे, अपना काम करेंगे या दोनों विकल्प खुले रखेंगे?'),
        ('What suits you better: a job or your own business? Either is okay too.', 'आपको नौकरी अच्छी लगेगी या अपना काम? दोनों भी कह सकते हैं।'),
        ('Are you leaning towards a job, your own work, or either?', 'आप नौकरी, अपना काम या दोनों में से किसके लिए तैयार हैं?')),
}

def next_question(values, missing, history, language, questions, suggested=None):
    if not missing:
        return 'कृपया अपनी जानकारी जाँचें और पुष्टि करें।' if language == 'hi' else 'Please review and correct your profile before confirming your matches.'
    field = missing[0]
    previous = [turn.get('text', '') for turn in history if turn.get('speaker') != 'user' and question_field(turn) == field]
    if suggested and question_field({'text': suggested}) == field and not any(
        re.sub(r'\W+', '', old.lower()) in re.sub(r'\W+', '', suggested.lower()) for old in previous if old
    ):
        return suggested
    if not previous: return questions[field][1 if language == 'hi' else 0]
    variants = FOLLOWUPS[field]
    offset = (len(previous) - 1) % len(variants)
    # Avoid identical text even after several attempts.
    for step in range(len(variants)):
        candidate = variants[(offset + step) % len(variants)][1 if language == 'hi' else 0]
        if candidate != previous[-1]: break
    latest = history[-1].get('text', '') if history and history[-1].get('speaker') == 'user' else ''
    prefix = ('कोई बात नहीं। ' if language == 'hi' else 'No problem. ') if UNKNOWN.fullmatch(latest.strip()) else ''
    return prefix + candidate
