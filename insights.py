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

def get_medical_insights_n_recommendataions(parsed_report):
  class ParameterRecommendation(BaseModel):
      parameter: str = Field(..., description="Name of the abnormal blood test parameter.")
      status: str = Field(..., description="Indicates whether the parameter is high or low.")
      possible_disease: list = Field(..., description="Possible health effects.")
      possible_causes: list = Field(..., description="Possible reasons for the abnormality.")
      dietary_suggestions: list = Field(..., description="Recommended foods to normalize levels.")
      lifestyle_changes: list = Field(..., description="Exercise, hydration, and other lifestyle recommendations.")
      medical_advice: str = Field(..., description="When to consult a doctor or take further medical action.")
  class HealthInsights(BaseModel):
      abnormal_parameters: list[ParameterRecommendation] = Field(..., description="List of insights for all abnormal parameters.")
  llm = ChatGroq(model_name='deepseek-r1-distill-llama-70b',groq_api_key = groq_api_key)
  structured_llm = llm.with_structured_output(HealthInsights)
  def generate_health_recommendations_n_insights(abnormal_results: dict):
      """
      Generates insights & recommendations for all abnormal blood parameters in a single call.
      """
      formatted_params = "\n".join([f"- {param}: {status}" for param, status in abnormal_results.items()])
      prompt_template = f"""
      The following blood test parameters are abnormal:
      {formatted_params}
      For each abnormal parameter, generate structured health insights in the following format:
      {{
        "abnormal_parameters": [
          {{
            "parameter": "Parameter Name",
            "status": "High/Low",
            "possible_disease": ["List possible health conditions"],
            "possible_causes": ["List of possible reasons"],
            "dietary_suggestions": ["Foods to normalize levels"],
            "lifestyle_changes": ["Exercise, hydration, sleep recommendations"],
            "medical_advice": "When to consult a doctor?"
          }}
        ]
      }}
      """
      structured_response = structured_llm.invoke(prompt_template)
      return structured_response.dict()
  blood_results = parsed_report.lab_results
  abnormal_results = abnormal_results = {param: details['status'] for param, details in blood_results.items() if details['status'] != "Normal"}
  recommendations_n_insights = generate_health_recommendations_n_insights(abnormal_results)
  # print(json.dumps(recommendations_n_insights, indent=2))
  return recommendations_n_insights
