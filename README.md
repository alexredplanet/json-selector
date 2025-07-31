# JSON Field Selector

A simple web application that allows users to upload JSON files and select specific fields to extract from each file. The application analyzes the JSON structure and provides an intuitive interface for field selection.

## Features

- **Upload Multiple JSON Files**: Drag and drop or click to upload multiple JSON files
- **Automatic Field Detection**: Analyzes all uploaded files to detect available fields
- **Interactive Field Selection**: Choose which fields to keep with checkboxes
- **Nested Field Support**: Handles nested objects and arrays with dot notation
- **Export Results**: Downloads filtered data as a text file
- **Docker Ready**: Packaged as a Docker container for easy deployment

## Quick Start

### Using Docker (Recommended)

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually:**
   ```bash
   docker build -t json-selector .
   docker run -p 5000:5000 json-selector
   ```

3. **Access the application:**
   Open your browser and go to `http://localhost:5000`

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   Open your browser and go to `http://localhost:5000`

## How to Use

1. **Upload JSON Files**: 
   - Click the upload area or drag and drop your JSON files
   - The application will analyze all files and extract available fields

2. **Select Fields**:
   - Review the list of detected fields
   - Use checkboxes to select which fields you want to keep
   - Use "Select All" or "Deselect All" for convenience

3. **Generate Results**:
   - Click "Generate Filtered Results"
   - The application will process all files and download a text file
   - Each file's filtered data will be included in the output

## Field Path Format

The application uses dot notation for nested fields:
- `name` - Top-level field
- `user.email` - Nested object field
- `items[0].title` - Array element field

## Output Format

The generated text file contains:
```
// File: example1.json
{
  "selected_field1": "value1",
  "selected_field2": "value2"
}

// File: example2.json
{
  "selected_field1": "value3",
  "selected_field2": "value4"
}
```

## Docker Deployment

### Environment Variables

- `FLASK_ENV`: Set to `production` for production deployment
- `FLASK_APP`: Application entry point (default: `app.py`)

### Ports

- The application runs on port 5000 inside the container
- Map to any external port: `-p 8080:5000`

### Volumes

- Mount `./uploads` to persist uploaded files between container restarts
- Example: `-v $(pwd)/uploads:/app/uploads`

## Technical Details

- **Framework**: Flask (Python)
- **Frontend**: Vanilla JavaScript with modern CSS
- **File Handling**: Supports JSON files up to 16MB
- **Field Detection**: Recursive analysis of JSON structure
- **Export Format**: Plain text with JSON objects

## Security Notes

- Files are temporarily stored in the `uploads` directory
- Previous uploads are cleared when new files are uploaded
- No persistent storage of user data
- File size limited to 16MB per upload

## Browser Compatibility

- Modern browsers with JavaScript enabled
- Drag and drop file upload support
- Responsive design for mobile and desktop
