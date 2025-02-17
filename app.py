from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from parser import get_parsed_report
from highlights import create_blood_test_plots
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
PLOTS_FOLDER = 'static/plots'
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
        
        # Parse the report
        parsed_report = get_parsed_report(filepath)
        
        # Generate plots
        create_blood_test_plots(parsed_report, app.config['PLOTS_FOLDER'])
        
        # Prepare response
        response_data = {
            'patient_info': parsed_report.patient_info,
            'lab_info': parsed_report.lab_info,
            'test_name': parsed_report.test_name,
            'lab_results': parsed_report.lab_results,
            'medical_personnel': parsed_report.medical_personnel
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message')
        role = data.get('role', 'patient')
        
        # Add your chatbot logic here
        response = "This is a test response"  # Replace with actual chatbot response
        
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)