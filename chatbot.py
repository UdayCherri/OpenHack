import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
from PIL import Image
import cv2
import numpy as np
import io,os
import json
import google.generativeai as genai
genai.configure(api_key='AIzaSyAFTm-mUcFxAakOw_qks3luweKHLmGhNlQ')
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.pydantic_v1 import BaseModel, Field
import warnings as warn
warn.filterwarnings("ignore")
from langchain_core.output_parsers import StrOutputParser
from typing import Optional
from langchain_groq import ChatGroq
os.environ['GROQ_API_KEY'] = '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'
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model_name='deepseek-r1-distill-llama-70b',groq_api_key = groq_api_key)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

def initiate_chat(parsed_report):
    system_prompt = """
    You are a helpful assistant that provides information about blood reports.

    You will receive queries from two types of users:

    1. Doctors: Provide detailed, technical explanations and recommendations.
    2. Patients: Provide simple, easy-to-understand explanations and advice.

    Here is the parsed blood report:

    {blood_report}

    Respond to the user's query based on their role:

    - If the user is a doctor, provide detailed medical explanations and recommendations.
    - If the user is a patient, provide simple, non-technical explanations and advice.

    User Role: {role}
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    model = ChatGroq(model="Gemma2-9b-It", groq_api_key=groq_api_key)

    chain = (
        RunnablePassthrough.assign(blood_report=lambda x: x["blood_report"])
        | prompt
        | model
    )

    store = {}

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="messages",
    )
    parsed_blood_report = parsed_report

    print("Welcome to the Blood Report Assistant Chatbot!")
    print("Are you a 'doctor' or a 'patient'? Type your role:")

    role = input().strip().lower()
    if role not in ["doctor", "patient"]:
        print("Invalid role. Please restart and enter either 'doctor' or 'patient'.")
        exit()

    print(f"\nHello {role.capitalize()}! You can ask about the blood report.")
    print("Type 'stop' or 'exit' to end the conversation.\n")

    session_id = "chat1"

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["stop", "exit"]:
            print("Ending conversation. Have a great day!")
            break

        user_message = HumanMessage(content=user_input)

        response = with_message_history.invoke(
            {
                "blood_report": parsed_blood_report,
                "messages": [user_message],
                "role": role,
            },
            config={"configurable": {"session_id": session_id}},
        )

        print("\nBot:", response.content, "\n")

