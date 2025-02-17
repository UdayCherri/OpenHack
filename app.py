from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from parser import get_parsed_report
from highlights import create_blood_test_plots
from insights import get_medical_insights_n_recommendataions
import logging
import google.generativeai as genai
from langchain_groq import ChatGroq
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure API keys and models
genai.configure(api_key='AIzaSyAFTm-mUcFxAakOw_qks3luweKHLmGhNlQ')
os.environ['GROQ_API_KEY'] = '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'
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model_name='deepseek-r1-distill-llama-70b', groq_api_key=groq_api_key)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
PLOTS_FOLDER = 'static/plots'  # Changed from abnormal_param_plots to plots
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PLOTS_FOLDER'] = PLOTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLOTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/plots/<path:filename>')
def serve_plot(filename):
    return send_from_directory(app.config['PLOTS_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"File saved: {filepath}")
        
        # Parse the report
        parsed_report = get_parsed_report(filepath)
        logger.info("Report parsed successfully")
        
        # Generate plots
        try:
            create_blood_test_plots(parsed_report, app.config['PLOTS_FOLDER'])
            logger.info("Plots generated successfully")
        except Exception as e:
            logger.error(f"Error generating plots: {str(e)}")
            
        # Generate insights
        try:
            insights = get_medical_insights_n_recommendataions(parsed_report)
            logger.info("Insights generated successfully")
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            insights = {"error": str(e)}
        
        # Prepare response
        response_data = {
            'patient_info': parsed_report.patient_info,
            'lab_info': parsed_report.lab_info,
            'test_name': parsed_report.test_name,
            'lab_results': parsed_report.lab_results,
            'medical_personnel': parsed_report.medical_personnel,
            'insights': insights
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up uploaded file
        if 'filepath' in locals():
            try:
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Error removing file: {str(e)}")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message')
        role = data.get('role', 'patient')
        
        # Create chat prompt
        prompt = f"""
        Role: {role}
        Question: {message}
        
        Please provide a clear and helpful response based on the medical context and the user's role.
        If you're unsure about anything, please acknowledge that and suggest consulting with a healthcare provider.
        """
        
        # Generate response using the LLM
        response = llm.invoke(prompt)
        
        return jsonify({'response': response.content})
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)