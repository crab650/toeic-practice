import json
import urllib.error
import urllib.request

from ..config import DEFAULT_GEMINI_MODEL


def build_gemini_url(api_key, model_name):
    model = (model_name or DEFAULT_GEMINI_MODEL).strip()
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"


def call_gemini(api_key, model_name, prompt):
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        },
    }

    try:
        req = urllib.request.Request(
            build_gemini_url(api_key, model_name),
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST',
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            return json.loads(text_response)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_msg)
            message = err_json.get('error', {}).get('message', str(e))
        except Exception:
            message = err_msg
        if "quota" in message.lower() or "limit" in message.lower() or e.code == 429:
            raise Exception("您的 Gemini API 金鑰已達免費額度限制或請求過於頻繁。請稍候再試。")
        raise Exception(f"Google API Error: {message}")
    except Exception as e:
        raise Exception(f"Gemini Translation failed: {str(e)}")


def explain_part5_question(api_key, model_name, question_data):
    prompt = f"""
You are an expert English teacher preparing students for the TOEIC exam.
Provide a high-quality translation and educational analysis for the following TOEIC Part 5 question.

Question: {question_data['question']}
Options:
(A) {question_data['option_a']}
(B) {question_data['option_b']}
(C) {question_data['option_c']}
(D) {question_data['option_d']}
Correct Answer: ({question_data['answer']})

Please output your response in JSON format with exactly two keys: "chinese" and "explanation".
The "chinese" key must contain the Traditional Chinese translation of the correct completed sentence.
The "explanation" key must contain a structured, educational breakdown in Traditional Chinese. It should include:
- Core analysis
- Option analysis for A, B, C, and D
- Key vocabulary and phrases

Do not include any markdown fences (like ```json) or explanation text outside the JSON object.
"""
    return call_gemini(api_key, model_name, prompt)


def explain_part2_question(api_key, model_name, question_data):
    prompt = f"""
You are an expert English teacher preparing students for the TOEIC exam.
Translate the following TOEIC Listening Part 2 (Question-Response) question and its three response options into Traditional Chinese.
Also, explain why the correct response is correct, and why other options are incorrect or inappropriate as responses.

Question/Statement: {question_data['question']}
Options:
(A) {question_data['option_a']}
(B) {question_data['option_b']}
(C) {question_data['option_c']}
Correct Response: ({question_data['answer']})

Please output your response in JSON format with exactly two keys: "chinese" and "explanation".
The "chinese" key must contain the Traditional Chinese translation of the Question/Statement, followed by the translations of options (A), (B), and (C).
The "explanation" key must contain a concise explanation of the response logic and why the correct answer fits, in Traditional Chinese.
Do not include any markdown fences (like ```json) or explanation text outside the JSON object.
"""
    return call_gemini(api_key, model_name, prompt)


def is_vietnamese(text):
    if not text:
        return False
    # Vietnamese-specific diacritics
    vi_chars = set("đáàảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệíìỉĩịóòỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ")
    return any(c in vi_chars for c in text.lower())


def explain_sentence(api_key, model_name, sentence_data):
    sentence = sentence_data['english']
    is_vi = is_vietnamese(sentence)

    if is_vi:
        prompt = f"""
You are an expert Vietnamese teacher helping a Traditional Chinese speaker understand Vietnamese sentence grammar.
Analyze this sentence for practical learning, not for a linguistics textbook.

Vietnamese sentence: {sentence}
Existing Traditional Chinese translation: {sentence_data.get('chinese', '')}

Please output JSON with exactly these keys:
"chinese", "grammar_note", "vocabulary_note", "common_mistakes", "example".

Requirements:
- Use Traditional Chinese.
- "chinese": a natural Traditional Chinese translation.
- "grammar_note": explain the sentence structure, grammar particles, classifiers (lượng từ), tenses (like đã, đang, sẽ), pronoun usage (like tôi, bạn, anh, chị), and why the word order works.
- "vocabulary_note": 必須詳細條列出該越南語句子中的「每一個單字與詞彙」（包含代名詞、助詞、量詞、虛詞等，絕對不可遺漏任何一個單字）。格式必須為清晰的條列，例如：「[單字] - [繁體中文意思]（詞性/說明）」，讓學習者能完全看懂每個單字的含意。
- "common_mistakes": list likely mistakes a learner may make with this sentence (such as wrong pronouns, misplaced modifiers, or pronunciation tones).
- "example": provide one short similar Vietnamese sentence and its Traditional Chinese translation.
- Keep each field concise but useful.

Do not include markdown fences or any text outside the JSON object.
"""
    else:
        prompt = f"""
You are an expert English teacher helping a Traditional Chinese speaker understand sentence grammar.
Analyze this sentence for practical learning, not for a linguistics textbook.

English sentence: {sentence}
Existing Traditional Chinese translation: {sentence_data.get('chinese', '')}

Please output JSON with exactly these keys:
"chinese", "grammar_note", "vocabulary_note", "common_mistakes", "example".

Requirements:
- Use Traditional Chinese.
- "chinese": a natural Traditional Chinese translation.
- "grammar_note": explain the sentence structure, clauses, tense, important grammar patterns, and why the word order works.
- "vocabulary_note": explain important words, phrases, collocations, or prepositions in this sentence.
- "common_mistakes": list likely mistakes a learner may make with this sentence.
- "example": provide one short similar English sentence and its Traditional Chinese translation.
- Keep each field concise but useful.

Do not include markdown fences or any text outside the JSON object.
"""
    return call_gemini(api_key, model_name, prompt)


def lookup_word_pronunciation(api_key, model_name, word, sentence=""):
    context_line = f"Context sentence: {sentence}" if sentence else "No context sentence provided."
    is_vi = is_vietnamese(word) or is_vietnamese(sentence)

    if is_vi:
        prompt = f"""
You are an expert Vietnamese pronunciation coach for Traditional Chinese speakers.
Analyze the word/phrase below and provide pronunciation help (including tones).

Vietnamese word/phrase: {word}
{context_line}

Please output JSON with exactly these keys:
"word", "ipa", "syllables", "stress", "meaning_zh", "pronunciation_note", "example".

Requirements:
- Use Traditional Chinese except the Vietnamese word/phrase and example sentence.
- "ipa": provide phonetic guide or spelling (e.g. Northern or Southern pronunciation differences, tones like Sắc, Huyền, Hỏi, Ngã, Nặng, Ngang).
- "syllables": split the word/phrase into syllables/morphemes if applicable.
- "stress": explain the tone of the syllable (e.g. Hỏi tone, Sắc tone, etc.) and tone contours.
- "meaning_zh": explain the meaning that fits the context if a context sentence is provided.
- "pronunciation_note": practical tips for pronouncing this word, especially tone transitions and vowel lengths for Chinese speakers.
- "example": one short Vietnamese example sentence plus Traditional Chinese translation.

Do not include markdown fences or any text outside the JSON object.
"""
    else:
        prompt = f"""
You are an expert English pronunciation coach for Traditional Chinese speakers.
Analyze the word below and provide IPA and pronunciation help.

Word: {word}
{context_line}

Please output JSON with exactly these keys:
"word", "ipa", "syllables", "stress", "meaning_zh", "pronunciation_note", "example".

Requirements:
- Use Traditional Chinese except the English word, IPA, syllables, and example sentence.
- "ipa": provide standard IPA. If both American and British pronunciations are common, include both clearly.
- "syllables": split the word into syllables.
- "stress": explain which syllable is stressed.
- "meaning_zh": explain the meaning that fits the context if a context sentence is provided.
- "pronunciation_note": practical tips for common pronunciation problems.
- "example": one short English example sentence plus Traditional Chinese translation.

Do not include markdown fences or any text outside the JSON object.
"""
    return call_gemini(api_key, model_name, prompt)
