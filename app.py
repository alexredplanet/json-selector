from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import zipfile
from collections import defaultdict
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import logging
import sys

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({
        'error': 'Upload size too large. Please upload fewer files or smaller files. Maximum size is 1GB.'
    }), 413

# No cleanup needed - all processing is done in memory

def extract_all_fields(json_data, prefix=""):
    """Recursively extract all field paths from a JSON object"""
    fields = set()
    
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            fields.add(current_path)
            
            if isinstance(value, (dict, list)):
                fields.update(extract_all_fields(value, current_path))
    
    elif isinstance(json_data, list) and json_data:
        # For arrays, analyze the first item to get structure
        if isinstance(json_data[0], (dict, list)):
            fields.update(extract_all_fields(json_data[0], f"{prefix}[0]" if prefix else "[0]"))
    
    return fields

def build_field_hierarchy(fields):
    """Build a hierarchical structure from flat field paths"""
    hierarchy = {}
    
    for field in sorted(fields):
        parts = field.split('.')
        current = hierarchy
        
        for i, part in enumerate(parts):
            # Clean array notation for display
            clean_part = part.replace('[0]', '[]')
            
            if clean_part not in current:
                current[clean_part] = {
                    'path': '.'.join(parts[:i+1]),
                    'children': {},
                    'is_leaf': i == len(parts) - 1,
                    'has_children': False
                }
            
            if i < len(parts) - 1:
                current[clean_part]['has_children'] = True
                current[clean_part]['is_leaf'] = False
            
            current = current[clean_part]['children']
    
    return hierarchy

def get_nested_value(data, path):
    """Get value from nested JSON using dot notation path"""
    try:
        keys = path.split('.')
        current = data
        
        for key in keys:
            if '[0]' in key:
                # Handle array access
                key = key.replace('[0]', '')
                if key:
                    current = current[key]
                if isinstance(current, list) and current:
                    current = current[0]
            else:
                current = current[key]
        
        return current
    except (KeyError, IndexError, TypeError):
        return None

def set_nested_value(data, path, value):
    """Set value in nested dict using dot notation path"""
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if '[0]' in key:
            key = key.replace('[0]', '')
            if key:
                if key not in current:
                    current[key] = [{}]
                current = current[key][0]
            else:
                # This is a root array case
                if not isinstance(current, list):
                    current = [{}]
                current = current[0]
        else:
            if key not in current:
                current[key] = {}
            current = current[key]
    
    # Set the final value
    final_key = keys[-1].replace('[0]', '')
    if '[0]' in keys[-1] and final_key:
        if final_key not in current:
            current[final_key] = []
        if not current[final_key]:
            current[final_key].append(value)
        else:
            current[final_key][0] = value
    else:
        current[final_key] = value

@app.route('/')
@app.route('/json-selector')
@app.route('/json-selector/')
def index():
    return render_template('index.html')

@app.route('/default-path')
@app.route('/json-selector/default-path')
def get_default_path():
    return jsonify({
        'path': '/json-selector'
    })

@app.route('/upload', methods=['POST'])
@app.route('/json-selector/upload', methods=['POST'])
def upload_files():
    logger.info(f"Upload request received from {request.remote_addr}")
    logger.info(f"Request path: {request.path}")
    logger.info(f"Request files: {list(request.files.keys())}")
    
    if 'files' not in request.files:
        logger.warning("No files in request")
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    logger.info(f"Found {len(files)} files in request")
    
    if not files or all(f.filename == '' for f in files):
        logger.warning("No valid files selected")
        return jsonify({'error': 'No files selected'}), 400
    
    json_files = []
    all_fields = set()
    invalid_files = []
    file_data = {}  # Store file data in memory
    
    for file in files:
        if file and file.filename.endswith('.json'):
            filename = secure_filename(file.filename)
            
            try:
                # Read file content directly from memory
                content = file.read().decode('utf-8')
                data = json.loads(content)
                
                # Store in memory for later processing
                file_data[filename] = data
                json_files.append(filename)
                all_fields.update(extract_all_fields(data))
                
            except json.JSONDecodeError as e:
                invalid_files.append(f"{filename}: {str(e)}")
                continue
            except Exception as e:
                invalid_files.append(f"{filename}: {str(e)}")
                continue
    
    if not json_files:
        return jsonify({'error': 'No valid JSON files found'}), 400
    
    field_hierarchy = build_field_hierarchy(all_fields)
    
    # Store file data in session or cache for processing
    # For simplicity, we'll use a global variable (in production, use Redis or similar)
    app.config['CURRENT_FILES'] = file_data
    
    response_data = {
        'files': json_files,
        'fields': sorted(list(all_fields)),
        'hierarchy': field_hierarchy
    }
    
    if invalid_files:
        response_data['warnings'] = {
            'message': f'Some files could not be processed ({len(invalid_files)} files)',
            'details': invalid_files
        }
        logger.warning(f"Invalid files: {invalid_files}")
    
    logger.info(f"Successfully processed {len(json_files)} files with {len(all_fields)} fields")
    return jsonify(response_data)

def create_hierarchical_output(original_data, selected_fields):
    """Create output that maintains hierarchical structure for selected fields"""
    filtered_data = {}
    
    # Sort fields to process parents before children
    sorted_fields = sorted(selected_fields, key=lambda x: (x.count('.'), x))
    
    for field in sorted_fields:
        value = get_nested_value(original_data, field)
        if value is not None:
            # Check if this field is a parent of other selected fields
            child_fields = [f for f in selected_fields if f.startswith(field + '.') or f.startswith(field + '[')]
            
            if child_fields:
                # This is a parent field with selected children
                # Only include the selected child fields, not the entire parent
                parent_structure = {}
                for child_field in child_fields:
                    child_value = get_nested_value(original_data, child_field)
                    if child_value is not None:
                        # Get the relative path from parent to child
                        relative_path = child_field[len(field):].lstrip('.')
                        if relative_path:  # Only if there's actually a child path
                            set_nested_value(parent_structure, relative_path, child_value)
                
                if parent_structure:
                    set_nested_value(filtered_data, field, parent_structure)
                else:
                    # No valid children, include the parent value
                    set_nested_value(filtered_data, field, value)
            else:
                # This is a leaf field or parent with no selected children
                set_nested_value(filtered_data, field, value)
    
    return filtered_data



@app.route('/process', methods=['POST'])
@app.route('/json-selector/process', methods=['POST'])
def process_files():
    """Original endpoint for browser download fallback"""
    data = request.get_json()
    selected_fields = data.get('fields', [])
    
    if not selected_fields:
        return jsonify({'error': 'No fields selected'}), 400
    
    # Get file data from memory
    file_data = app.config.get('CURRENT_FILES', {})
    if not file_data:
        return jsonify({'error': 'No files available. Please upload files first.'}), 400
    
    results = []
    
    for filename, original_data in file_data.items():
        try:
            # Create filtered object maintaining hierarchical structure
            filtered_data = create_hierarchical_output(original_data, selected_fields)
            
            results.append({
                'filename': filename,
                'data': filtered_data
            })
            
        except Exception as e:
            # Skip files that can't be processed
            continue
    
    # Create content string
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content_lines = [
        f"// Generated on: {timestamp}",
        f"// Selected fields: {len(selected_fields)}",
        f"// Processed files: {len(results)}",
        ""
    ]
    
    for result in results:
        content_lines.append(f"// File: {result['filename']}")
        content_lines.append(json.dumps(result['data'], indent=2, ensure_ascii=False))
        content_lines.append("")
    
    content = '\n'.join(content_lines)
    
    # Return content as downloadable file
    from flask import Response
    timestamp_filename = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return Response(
        content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=filtered_results_{timestamp_filename}.txt'
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
