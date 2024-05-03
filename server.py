import base64
import io
import json
import os
import openai
import pandas as pd
import requests
from deep_translator import GoogleTranslator
import uvicorn
import datetime
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from openai import AssistantEventHandler
from typing_extensions import override
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

question =  ""
file = ""


async def get_file_stream(file):
    print(".xlsx")
    file_content = await file.read()
    df = pd.read_excel(io.BytesIO(file_content), sheet_name=0)
    csv_string = df.to_csv(index=False)
    csv_bytes = csv_string.encode()
    file_stream = io.BytesIO(csv_bytes)
    return file_stream

client = openai.OpenAI()
file_stream = get_file_stream(file)
xfile = client.files.create(
file=file_stream,
purpose='assistants'
)
thread = client.beta.threads.create()
assistant = client.beta.assistants.create(
    instructions="You are a personal data analyst. \
        ",
    model="gpt-4-turbo",
    tools=[{"type": "code_interpreter"}],
    tool_resources={
        "code_interpreter": {
        "file_ids": [xfile.id]
        }
    }
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="You have been provided a csv file of which the first row corresponds to its columns. \
                When asked a question related to the data provided, write and run code to answer the question. \
                Do not ask any confirming questions. Assume all that is necessary. \
                Do not mention anything insinuating that a file has been uploaded. Answer the following question: " + question,
    )

if run.status == 'completed': 
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    contents = messages.data[0].content
    print(contents)