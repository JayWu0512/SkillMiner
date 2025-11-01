
import os, time, sys
import pandas as pd
import gradio as gr
from openai import OpenAI
from PyPDF2 import PdfReader
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime


LOG_FILE = Path(__file__).with_name("chat_logs.json")

def save_chat_log(user_input, assistant_reply):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_input,
        "assistant_message": assistant_reply
    }

    # Append to file: create file if doesn't exist
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                json.dump([log_entry], f, indent=2)
        else:
            with open(LOG_FILE, "r+") as f:
                data = json.load(f)
                data.append(log_entry)
                f.seek(0)
                json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Logging error: {e}")

# -------- Data (needs pyarrow/fastparquet installed in THIS interpreter) --------
# data = pd.read_parquet("database/data/gold/role_skills_by_title.parquet", engine="pyarrow")

# -------- OpenAI client (use env var, don't hard-code) --------

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are a helpful career assistant. Ask the user to upload their resume "
    "and then provide 3 concrete, personalized improvement suggestions. "
    "Also suggest 3 matching firms that hire for recruiter-facing roles."
)

# Initial bot message that appears immediately on load (no API call needed)
INITIAL_BOT_MSG = (
    "Hi! 👋 Please upload your resume (PDF) or paste your text. "
    "I’ll give you 3 targeted improvements and suggest 3 matching firms."
)

def message_form(role, content):
    return {"role": role, "content": content}

with gr.Blocks() as demo:
    gr.Markdown("### Career Chat — upload your resume to get tailored advice")

    # Chatbot starts with a bot-only message: (None, <assistant_text>)
    chatbot = gr.Chatbot(value=[(None, INITIAL_BOT_MSG)], height=460)

    with gr.Row():
        resume_file = gr.File(label="Upload resume (PDF optional)", file_types=[".pdf"], interactive=True)
    msg = gr.Textbox(placeholder="Type here or paste resume text…", lines=2)
    clear = gr.Button("Clear")

    # Keep a short rolling prompt history
    prompts = [message_form("system", SYSTEM_PROMPT)]

    # We'll stash parsed resume text if a PDF is uploaded
    resume_text_state = gr.State("")

    # --- Parse uploaded PDF ---
    def parse_resume(pdf):
        if not pdf:
            return ""
        try:
            reader = PdfReader(pdf.name)
            txt = []
            for page in reader.pages:
                t = page.extract_text() or ""
                txt.append(t)
            return "\n".join(txt).strip()
        except Exception as e:
            return f"(Note: could not parse PDF: {e})"

    resume_file.upload(fn=parse_resume, inputs=resume_file, outputs=resume_text_state)

    # --- Submit: add user's message to chat, then stream model reply ---
    def user_submit(message, chat_history):
        # append empty assistant slot we’ll stream into
        chat_history = chat_history + [(message, "")]
        return "", chat_history

    def stream_reply(chat_history, resume_text):
        """
        Streams the assistant’s reply into the last (empty) assistant slot.
        """
        # Build OpenAI messages from UI history + optional resume text context
        messages = [message_form("system", SYSTEM_PROMPT)]

        # If we have parsed resume text, prepend it as context before the user's latest message
        if resume_text:
            messages.append(message_form("user", f"Here is my resume text:\n{resume_text}"))

        # Reconstruct chat turns (last 10 pairs is plenty)
        for human, assistant in chat_history[-10:]:
            if human:
                messages.append(message_form("user", human))
            if assistant:
                messages.append(message_form("assistant", assistant))

        partial = ""
        # Call OpenAI with streaming

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=messages,
                stream=True,
            )

        # Stream tokens into the last bot message
        
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                partial += delta
                # Replace the last tuple with the growing assistant text
                chat_history[-1] = (chat_history[-1][0], partial)
                time.sleep(0.01)
                yield chat_history

        finally:
        # Log whatever we have (even partial)
            last_user_message = chat_history[-1][0]
            final_response = chat_history[-1][1]
            try:
                save_chat_log(last_user_message, final_response)
            except Exception as e:
                print("log error:", e)

    submit = msg.submit(user_submit, [msg, chatbot], [msg, chatbot])
    submit.then(stream_reply, [chatbot, resume_text_state], chatbot)

    # Clear resets to the initial greeting
    def reset_chat():
        return [(None, INITIAL_BOT_MSG)], "", ""

    clear.click(reset_chat, None, [chatbot, msg, resume_text_state])

demo.queue()
demo.launch()
