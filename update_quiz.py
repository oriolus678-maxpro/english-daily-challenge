import os
import json
import re
from google import genai

# 1. 初始化最新版 Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("找不到 GEMINI_API_KEY 環境變數，請確認 GitHub Secrets 設定。")

client = genai.Client(api_key=API_KEY)

QUIZ_FILE = "quizData.json"

# 2. 讀取現有題庫
if os.path.exists(QUIZ_FILE):
    with open(QUIZ_FILE, "r", encoding="utf-8") as f:
        quiz_data = json.load(f)
else:
    quiz_data = {"vocabulary": [], "grammar": [], "reading": []}

current_vocab_count = len(quiz_data.get("vocabulary", []))
current_grammar_count = len(quiz_data.get("grammar", []))
current_reading_count = len(quiz_data.get("reading", []))

# 計算下一個題目的起始 ID
next_v_id = current_vocab_count + 1
next_g_id = current_grammar_count + 1
next_a_id = current_reading_count + 1

# 3. 設定生成提示詞
prompt = f"""
你是一位專業的台灣國中英語命題專家。請根據 CEFR A2 等級（台灣國中程度），生成全新題目。
要求：
1. 詞彙題 10 題：題號從 'v{next_v_id}' 到 'v{next_v_id + 9}'。
2. 文法題 5 題：題號從 'g{next_g_id}' 到 'g{next_g_id + 4}'。
3. 閱讀測驗 1 篇（5 小題）：文章編號為 'a{next_a_id}'，題目 ID 從 'r{(next_a_id-1)*5 + 1}' 到 'r{next_a_id*5}'。

所有題目必須包含繁體中文翻譯、必考單字、例句、文法重點與片語。
必須以嚴格的 JSON 格式輸出，不得包含任何額外的 Markdown 解釋文字（如 ```json 等標籤）。

JSON 結構範例：
{{
  "vocabulary": [
    {{
      "id": "v{next_v_id}",
      "question": "題目描述 ________.",
      "options": ["A. 選項1", "B. 選項2", "C. 選項3", "D. 選項4"],
      "correct": "A",
      "explanation": {{
        "translation": "整句中文翻譯",
        "vocabulary": [{{"word": "單字", "pos": "n.", "meaning": "意思", "example": "例句"}}],
        "grammar": "文法重點說明",
        "phrase": "實用片語 (無則填 None)"
      }}
    }}
  ],
  "grammar": [],
  "reading": [
    {{
      "articleId": "a{next_a_id}",
      "articleText": "短文內容...",
      "questions": [
        {{
          "id": "r{(next_a_id-1)*5 + 1}",
          "question": "問題描述?",
          "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
          "correct": "B",
          "explanation": {{
            "translation": "翻譯",
            "vocabulary": [{{"word": "單字", "pos": "v.", "meaning": "意思", "example": "例句"}}],
            "grammar": "解析",
            "phrase": "None"
          }}
        }}
      ]
    }}
  ]
}}
"""

print("正在請求最新版 Gemini 2.5 API 生成新題目...")
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt
)
clean_text = response.text.strip()

# 清除可能包裹的 markdown 標籤
clean_text = re.sub(r"^```json\s*", "", clean_text)
clean_text = re.sub(r"\s*```$", "", clean_text)

new_content = json.loads(clean_text)

# 4. 合併新舊題庫
quiz_data.setdefault("vocabulary", []).extend(new_content.get("vocabulary", []))
quiz_data.setdefault("grammar", []).extend(new_content.get("grammar", []))
quiz_data.setdefault("reading", []).extend(new_content.get("reading", []))

with open(QUIZ_FILE, "w", encoding="utf-8") as f:
    json.dump(quiz_data, f, ensure_ascii=False, indent=2)

print(f"成功更新題庫！目前總數：詞彙 {len(quiz_data['vocabulary'])} 題、文法 {len(quiz_data['grammar'])} 題、閱讀 {len(quiz_data['reading'])} 篇。")
