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

def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)[1]
    processed_path = "/content/preprocessed.jpg"
    cv2.imwrite(processed_path, image)
    return processed_path
def get_parsed_text_using_tesseract(image_path):
    image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(image)
    return extracted_text
def get_parsed_text_using_pypdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    extracted_text = "\n".join([doc.page_content for doc in documents])
    return extracted_text
def get_parsed_text_using_gemini(file_path):
    try:
        # raise Exception("Error")
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        file_id = genai.upload_file(path=file_path)
        user_input = """
        Extract the text from the uploaded blood report file!
        """
        response = model.generate_content([file_id, user_input])
        return response.text
    except Exception as e:
        print(e)
        if 'pdf' in file_path:
            return get_parsed_text_using_pypdf(file_path)
        else:
            processed_image = preprocess_image(file_path)
            extracted_text = get_parsed_text_using_tesseract(processed_image)
            return extracted_text
class LabTestReport(BaseModel):
    patient_info: dict = Field(..., description="Basic details of the patient.")
    lab_info: dict = Field(..., description="Details about the laboratory.")
    test_name: str = Field(..., description="Name of the test performed.")
    lab_results: dict = Field(..., description="Structured representation of blood test results.")
    medical_personnel: dict = Field(..., description="Details of medical professionals who processed the report.")
structured_llm = llm.with_structured_output(LabTestReport)

def generate_structured_report(parsed_text: str) -> LabTestReport:
    """
    Converts extracted OCR text from a blood report into a structured JSON format.
    """
    prompt_template = f"""
    Given the following extracted blood report text:
    {parsed_text}

    Your Task:
    - Analyze the text carefully and extract the relevant details in a structured manner.
    - Fill the following JSON format with appropriate values from the extracted text.

    Response Format:
    {{
      "patient_info": {{
        "name": "",  # Extract the patient’s name
        "age": "",  # Extract the age
        "gender": "",  # Extract gender
        "patient_id": "",  # Extract patient ID if available
        "sample_collected_at": "",  # Extract sample collection location
        "referred_by": "",  # Doctor who referred the test
        "registered_on": "",  # Registration date
        "collected_on": "",  # Sample collection date
        "reported_on": ""  # Date when report was generated
      }},
      "lab_info": {{
        "lab_name": "",  # Extract lab name
        "lab_contact": {{
          "phone": "",  # Extract lab phone number if available
          "email": ""  # Extract lab email if available
        }},
        "lab_address": "",  # Extract full address of the lab
        "website": "",  # Extract website if available
        "instruments": "",  # Instruments used for testing
        "generated_on": ""  # Report generation date
      }},
      "test_name": "",  # Extract the test name
      "lab_results": {{
          "param_name_1": {{
            "value": "",  # Extract parameter value
            "unit": "",  # Extract unit (e.g., g/dL, cells/cumm)
            "reference_range": "",  # Extract reference range
            "status": ""  # Indicate if value is Normal, High, or Low
          }},
          // Like this, extract all available test parameters in the report
      }},
      "medical_personnel": {{
        "medical_lab_technician": "",  # Extract name of lab technician
        "pathologists": [
          {{
            "name": "",  # Extract name of pathologist
            "qualification": ""  # Extract qualification (e.g., MD Pathology)
          }},
          {{
            "name": "",  # Extract name of additional pathologist if available
            "qualification": ""
          }}
        ]
      }}
    }}
    """

    structured_response = structured_llm.invoke(prompt_template)
    return structured_response
def get_parsed_report(file_path):
  ehr = get_parsed_text_using_gemini(file_path)
  parsed_report = generate_structured_report(ehr)
  return parsed_report