import random
import re
import os 
import asyncio
import time
from google import genai
from telegram import Bot, Poll
from dotenv import load_dotenv
import os

load_dotenv()



# ====== Google GenAI client ======
google_token = os.getenv("GOOGLE_TOKEN")


# ====== Telegram bot setup ======


TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

# ====== Read topics from file ======
file_path = "topics.txt"
with open(file_path, "r", encoding="utf-8") as f:
    topics = [t.strip() for t in f.readlines() if t.strip()]

chat_id_mcq = "@ssc_cgl_g"
chat_id_monk = "@visioniasx"

chat_listt = [chat_id_mcq ,chat_id_monk]

# ====== Main loop ======
async def main():
    client = genai.Client(api_key=google_token)
    i = 0
    while True:
        try:
            topic = random.choice(topics)
            prompt = f"""
Generate a SSC themed, strictly factual and easy exam type multiple-choice question on the topic "{topic}". 
The question must be based on direct general knowledge, no reasoning and analysis.

Output ONLY the following Python variables, strictly nothing else:

question = "..."
options = ["Option1", "Option2", "Option3", "Option4"]
correct_answer = "..."

The correct_answer must strictly match exactly one of the options. 
Do NOT include explanations, extra text, or numbering. 
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            text = response.text
            question_match = re.search(r'question\s*=\s*"(.*?)"', text, re.DOTALL)
            options_match = re.search(r'options\s*=\s*\[(.*?)\]', text, re.DOTALL)
            answer_match = re.search(r'correct_answer\s*=\s*"(.*?)"', text, re.DOTALL)

            if question_match and options_match and answer_match:
                question = question_match.group(1).strip()
                options = [opt.strip().strip('"') for opt in options_match.group(1).split(',')]
                correct_answer = answer_match.group(1).strip()


                for chat_id in chat_listt:
                    await bot.send_poll(
                        chat_id=chat_id,
                        question=question,
                        options=options,
                        type=Poll.QUIZ,
                        correct_option_id=options.index(correct_answer),
                        is_anonymous=True
                    )
                i += 1
                print(f"MCQ {i} posted successfully!")
                if i%5 == 0:
                    for idss in chat_listt:
                        await bot.send_message(chat_id=idss , text="🌻 #upsc #ssc #ssccgl #uppcs daily MCQs \nGk, GS, Current Affairs Quiz, E-books, PDF & All the Important One Liner Question for #UPSC #CDS Railways SSC UPPCS #SSCGD #SSCCGL #SSC #SSCMTS Etc. \nCompetitive Exams....")
                        print("Text printed successfully")
                    break
                
            else:
                print(f"Failed to extract variables for MCQ {i+1}. Raw response:\n{text}")

        except Exception as e:
            print(f"Error posting MCQ {i+1}: {e}")

        print("pause : 120s")

        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(main())
