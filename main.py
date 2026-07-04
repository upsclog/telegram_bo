import random
import re
import time
import requests
from google import genai
import os
from dotenv import load_dotenv


# ========= CONFIG =========

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHAT_IDS = [
    "@upsclog",
    "@upsc_daily_pyq"
]
client = genai.Client(api_key=GEMINI_API_KEY)   #freelancer.srijay@gmail.com API key
# ========= LOAD TOPICS =========
with open("topics.txt", "r", encoding="utf-8") as f:
    topics = [line.strip() for line in f if line.strip()]
MAX_RETRIES = 5
RETRY_DELAY = 30


def generate_fact():
    topic = random.choice(topics)
    prompt = f"""
You are an expert story teller and a factual guru.
Generate ONE high-quality UPSC-oriented fact on the topic "{topic}".
Rules:
- Maximum 10 words.
- Suitable for UPSC syllabus.
- Focus on constitutional provisions, historical significance, geography,
  economy, environment, science & technology, governance,
  international relations, committees, reports, Acts, important personalities,
  landmark judgments or institutions whenever relevant.
- The presentation much be necessarily catchy and cool and interesting include one relevant emoji at the very begining
- Avoid textbook definitions and obvious facts.
- Output ONLY the fact
"""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Generating fact... ({attempt+1}/{MAX_RETRIES})")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            fact = response.text.strip()
            if fact:
                return fact
        except Exception as e:
            print(e)
        if attempt != MAX_RETRIES - 1:
            print(f"Retrying in {RETRY_DELAY} seconds...\n")
            time.sleep(RETRY_DELAY)
    return None


def send_fact(fact):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"""\n\n{fact}👈\n\n"""
    for chat_id in CHAT_IDS:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message,
            },
        )
        print(response.json())


# ========= POLL (TRUE/FALSE) LOGIC =========

def generate_poll():
    """
    Asks Gemini for a UPSC-oriented True/False statement, along with the
    correct answer. Returns a tuple (statement, correct_answer_bool) or
    None if it failed to produce a valid, parseable response after retries.
    """
    topic = random.choice(topics)
    prompt = f"""
You are an expert UPSC quiz master.
Generate ONE True/False statement on the topic "{topic}" suitable for a UPSC quiz poll.
Rules:
- The statement must be a single factual claim (either definitely true or definitely false).
- Maximum 20 words.
- Make it catchy and interesting, and include one relevant emoji at the end of the statement.
- Be certain the statement's truth value is unambiguous and factually verifiable.
- Output STRICTLY in this exact format, nothing else, no extra commentary:
STATEMENT: <the statement text with emoji>
ANSWER: True
(or)
STATEMENT: <the statement text with emoji>
ANSWER: False
"""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Generating poll... ({attempt+1}/{MAX_RETRIES})")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = response.text.strip()

            statement_match = re.search(r"STATEMENT:\s*(.+)", text)
            answer_match = re.search(r"ANSWER:\s*(True|False)", text, re.IGNORECASE)

            if statement_match and answer_match:
                statement = statement_match.group(1).strip()
                answer_str = answer_match.group(1).strip().lower()
                correct_answer = (answer_str == "true")
                if statement:
                    return statement, correct_answer

            print(f"⚠️ Could not parse a valid STATEMENT/ANSWER pair from response:\n{text}\n")
        except Exception as e:
            print(e)
        if attempt != MAX_RETRIES - 1:
            print(f"Retrying in {RETRY_DELAY} seconds...\n")
            time.sleep(RETRY_DELAY)
    return None


def send_poll(statement, correct_answer):
    """
    Sends a quiz-style True/False poll to Telegram, with the correct
    option pre-marked so Telegram validates answers itself.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    correct_option_id = 0 if correct_answer else 1  # 0 = True, 1 = False
    for chat_id in CHAT_IDS:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "question": statement,
                "options": '["True", "False"]',
                "type": "quiz",
                "correct_option_id": correct_option_id,
                "is_anonymous": True,
            },
        )
        print(response.json())


if __name__ == "__main__":
    # Sequence: 3 facts -> poll -> 3 facts -> poll -> 4 facts (12 items total)
    sequence = (
        ["fact"] * 3 + ["poll"] +
        ["fact"] * 3 + ["poll"] +
        ["fact"] * 4
    )

    MIN_GAP = 20   # seconds
    MAX_GAP = 65   # seconds

    posted_count = 0
    total = len(sequence)

    for i, item_type in enumerate(sequence):
        print(f"\n===== Item {i+1}/{total} ({item_type}) =====")

        if item_type == "fact":
            fact = generate_fact()
            if fact:
                send_fact(fact)
                posted_count += 1
                print(f"✅ Fact posted successfully.")
            else:
                print(f"❌ Could not generate fact after multiple retries. Skipping.")

        elif item_type == "poll":
            poll_data = generate_poll()
            if poll_data:
                statement, correct_answer = poll_data
                send_poll(statement, correct_answer)
                posted_count += 1
                print(f"✅ Poll posted successfully. (Correct answer: {correct_answer})")
            else:
                print(f"❌ Could not generate poll after multiple retries. Skipping.")

        # Don't sleep after the very last item
        if i != total - 1:
            gap = random.uniform(MIN_GAP, MAX_GAP)
            print(f"Waiting {gap:.1f} seconds before next post...")
            time.sleep(gap)

    print(f"\n🎉 Done. {posted_count}/{total} items posted successfully.")
