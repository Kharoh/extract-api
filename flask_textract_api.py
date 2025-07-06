"""
Flask API for Document Text Extraction using Textract
=====================================================

This API provides endpoints for uploading documents and extracting text using the textract library.
Supports various document formats including PDF, DOCX, TXT, JPEG, PNG, and more.
"""

import os
import logging
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import textract
from pathlib import Path
import mimetypes
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Supported file extensions based on textract capabilities
ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'doc', 'txt', 'rtf', 'odt',
    'jpeg', 'jpg', 'png', 'tiff', 'tif', 'gif',
    'pptx', 'xlsx', 'xls', 'csv', 'eml', 'epub', 'html', 'htm'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(file_path):
    """Get file information including size and MIME type"""
    try:
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        return {
            'size': file_size,
            'mime_type': mime_type,
            'size_mb': round(file_size / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return None

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'message': 'Maximum file size is 16MB',
        'status': 'error'
    }), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred during processing',
        'status': 'error'
    }), 500

@app.route('/', methods=['GET'])
def home():
    """Health check and API information endpoint"""
    return jsonify({
        'service': 'Document Text Extraction API',
        'status': 'running',
        'version': '1.0.0',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': '16MB',
        'endpoints': {
            'POST /extract': 'Extract text from uploaded document',
            'GET /health': 'Health check endpoint',
            'GET /': 'API information'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': str(Path(__file__).stat().st_mtime)
    })

@app.route('/extract', methods=['POST'])
def extract_text():
    """
    Extract text from uploaded document using textract

    Expected request:
    - multipart/form-data with 'file' field containing the document

    Returns:
    - JSON response with extracted text and metadata
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload a file using the "file" field',
                'status': 'error'
            }), 400

        file = request.files['file']

        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a file to upload',
                'status': 'error'
            }), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Unsupported file format',
                'message': f'Supported formats: {", ".join(ALLOWED_EXTENSIONS)}',
                'status': 'error',
                'filename': file.filename
            }), 400

        # Secure the filename
        filename = secure_filename(file.filename)   

        # Read file content into memory
        file_bytes = file.read()
        file_size = len(file_bytes)
        mime_type, _ = mimetypes.guess_type(filename)
        file_info = {
            'size': file_size,
            'mime_type': mime_type,
            'size_mb': round(file_size / (1024 * 1024), 2)
        }

        logger.info(f"Processing file: {filename} ({file_info['size_mb']}MB)")

        try:
            # Extract text using textract from a temporary file (Windows compatible)
            ext = filename.rsplit('.', 1)[-1].lower()
            extension = f'.{ext}'
            temp = tempfile.NamedTemporaryFile(dir="./temp", delete=False, suffix=extension)
            try:
                temp.write(file_bytes)
                temp.flush()
                temp.close()
                extracted_text = textract.process(temp.name, extension=extension)
            finally:
                os.unlink(temp.name)

            # Decode bytes to string if necessary
            if isinstance(extracted_text, bytes):
                extracted_text = extracted_text.decode('utf-8')

            # Prepare response
            response_data = {
                'status': 'success',
                'filename': filename,
                'extracted_text': extracted_text.strip(),
                'text_length': len(extracted_text.strip()),
                'file_info': file_info,
                'message': 'Text extraction completed successfully'
            }

            logger.info(f"Successfully extracted {len(extracted_text.strip())} characters from {filename}")

            return jsonify(response_data)

        except Exception as extraction_error:
            logger.error(f"Text extraction failed for {filename}: {str(extraction_error)}")
            return jsonify({
                'error': 'Text extraction failed',
                'message': f'Could not extract text from file: {str(extraction_error)}',
                'status': 'error',
                'filename': filename
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error in extract_text: {str(e)}")
        return jsonify({
            'error': 'Unexpected error',
            'message': str(e),
            'status': 'error'
        }), 500

@app.route('/formats', methods=['GET'])
def supported_formats():
    """Get detailed information about supported file formats"""
    format_details = {
        'documents': ['pdf', 'docx', 'doc', 'txt', 'rtf', 'odt'],
        'presentations': ['pptx'],
        'spreadsheets': ['xlsx', 'xls', 'csv'],
        'images': ['jpeg', 'jpg', 'png', 'tiff', 'tif', 'gif'],
        'web': ['html', 'htm'],
        'email': ['eml'],
        'ebooks': ['epub']
    }

    return jsonify({
        'supported_formats': format_details,
        'total_formats': len(ALLOWED_EXTENSIONS),
        'max_file_size': '16MB',
        'note': 'Some formats may require additional system dependencies'
    })

if __name__ == '__main__':
    print("Starting Document Text Extraction API...")
    print("Supported formats:", ', '.join(ALLOWED_EXTENSIONS))
    print("Maximum file size: 16MB")
    print("\nAPI Endpoints:")
    print("  GET  /           - API information")
    print("  GET  /health     - Health check")
    print("  POST /extract    - Extract text from document")
    print("  GET  /formats    - Supported file formats")
    print("\nStarting server on http://localhost:5002...")

    app.run(debug=True, host='0.0.0.0', port=5002)
