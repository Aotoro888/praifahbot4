from flask import Flask, request, abort, render_template
from dotenv import load_dotenv
import os, psycopg2
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# Connect to PostgreSQL
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, user_id TEXT, message TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()

@app.route("/")
def home():
    cur.execute("SELECT user_id, message, timestamp FROM messages ORDER BY timestamp DESC LIMIT 50")
    messages = cur.fetchall()
    return render_template("index.html", messages=messages)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"คุณพิมพ์ว่า: {text}"))
    cur.execute("INSERT INTO messages (user_id, message) VALUES (%s, %s)", (user_id, text))
    conn.commit()

if __name__ == "__main__":
    app.run(debug=True)
