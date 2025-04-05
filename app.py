from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging
from model import PDFChatProcessor  

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

try:
    processor = PDFChatProcessor() 
except ValueError as e:
    app.logger.error(f"Failed to initialize PDFChatProcessor: {str(e)}")
    raise

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        app.logger.error("No file part in the request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        app.logger.error("No file selected")
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        app.logger.error("File type not allowed")
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(file_path)
        
        if not os.path.exists(file_path):
            raise Exception("File was not saved properly")
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            os.remove(file_path)
            raise Exception("Uploaded file has 0 bytes size")
        
        processor.load_pdf(file_path)
        
        return jsonify({
            "message": "PDF uploaded successfully",
            "filename": filename,
            "size_bytes": file_size
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error processing upload: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat_with_pdf():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        if not processor.current_file: 
            return jsonify({"error": "No PDF has been loaded. Please upload a PDF first."}), 400

        response = processor.process_query(message)
        return jsonify({"response": response}), 200
    except Exception as e:
        app.logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def check_status():
    files = os.listdir(app.config['UPLOAD_FOLDER']) if os.path.exists(app.config['UPLOAD_FOLDER']) else []
    return jsonify({
        "pdf_loaded": bool(processor.current_file),
        "upload_folder": app.config['UPLOAD_FOLDER'],
        "files": files
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)