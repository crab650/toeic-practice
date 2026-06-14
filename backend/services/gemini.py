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
