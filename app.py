"""
Flask Web Application for PPT Generation
Provides a web interface for generating presentations from documentation.
"""
import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
import traceback

# Load environment variables from .env file
load_dotenv(override=True)

from src.core.graph_pipeline2 import create_pipeline2_graph
from src.utils.registry_helper import load_all_registries
from src.core.state import PPTState
from langchain_core.runnables import RunnableConfig

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['OUTPUT_FOLDER'] = 'data/outputs'

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get list of available templates."""
    try:
        templates_dir = 'data/templates'
        registry_dir = 'data/registry'
        
        if not os.path.exists(templates_dir):
            return jsonify({'error': 'Templates directory not found'}), 404
        
        templates = []
        for file in os.listdir(templates_dir):
            if file.endswith('.pptx'):
                template_name = os.path.splitext(file)[0]
                registry_file = os.path.join(registry_dir, f"{template_name}.json")
                
                templates.append({
                    'name': file,
                    'displayName': template_name.replace('_', ' ').title(),
                    'hasRegistry': os.path.exists(registry_file)
                })
        
        return jsonify({'templates': templates})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate_presentation():
    """Generate a presentation from the provided documentation."""
    try:
        data = request.json
        documentation = data.get('documentation', '').strip()
        template_name = data.get('template', 'template2.pptx')
        
        if not documentation:
            return jsonify({'error': 'Documentation text is required'}), 400
        
        if len(documentation) < 50:
            return jsonify({'error': 'Documentation text is too short (minimum 50 characters)'}), 400
        
        # Load all template registries
        combined_registry = load_all_registries()
        
        if not combined_registry:
            return jsonify({
                'error': 'No templates found in registry. Please run Pipeline 1 first to index templates.'
            }), 400
        
        # Get the registry for the selected template
        template_key = os.path.splitext(template_name)[0]
        
        if template_key not in combined_registry:
            return jsonify({
                'error': f'Registry for {template_name} not found. Please index this template first.'
            }), 400
        
        target_registry = combined_registry[template_key]
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"presentation_{timestamp}.pptx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Setup initial state
        initial_state = PPTState(
            raw_docs=documentation,
            primary_master_path=f"data/templates/{template_name}",
            registry=target_registry,
            content_map=None,
            slide_plans=[],
            manifest=[],
            final_file_path=output_path,
            validation_errors=[],
            thread_id=f"web_gen_{timestamp}",
            current_step="start"
        )
        
        # Initialize and run the graph
        app_graph = create_pipeline2_graph()
        config_obj = RunnableConfig(configurable={"thread_id": f"web_gen_{timestamp}"})
        
        print(f"--- 🚀 Starting Web Generation for: {template_name} ---")
        final_state = app_graph.invoke(initial_state, config=config_obj)
        
        if final_state.get("final_file_path") and os.path.exists(final_state["final_file_path"]):
            return jsonify({
                'success': True,
                'message': 'Presentation generated successfully!',
                'filename': output_filename,
                'downloadUrl': f'/api/download/{output_filename}'
            })
        else:
            errors = final_state.get('validation_errors', [])
            error_msg = '; '.join(errors) if errors else 'Unknown error occurred'
            return jsonify({
                'error': f'Failed to generate presentation: {error_msg}'
            }), 500
    
    except Exception as e:
        print(f"Error generating presentation: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a generated presentation."""
    try:
        # Secure the filename to prevent directory traversal
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get list of previously generated presentations."""
    try:
        outputs_dir = app.config['OUTPUT_FOLDER']
        
        if not os.path.exists(outputs_dir):
            return jsonify({'presentations': []})
        
        presentations = []
        for file in os.listdir(outputs_dir):
            if file.endswith('.pptx'):
                file_path = os.path.join(outputs_dir, file)
                stat = os.stat(file_path)
                
                presentations.append({
                    'filename': file,
                    'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'downloadUrl': f'/api/download/{file}'
                })
        
        # Sort by creation time (newest first)
        presentations.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({'presentations': presentations})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("🚀 Starting PPT Generation Web Server...")
    print("📍 Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
