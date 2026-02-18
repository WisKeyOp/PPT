"""
Streamlit Web Application for PPT Generation
Provides an intuitive web interface for generating EY presentations from documentation.
"""
import os
import sys
import json
import importlib
import streamlit as st
from datetime import datetime
from pathlib import Path
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# CRITICAL: Force reload of modified modules to ensure defensive fixes are active
# (Prevents Python module caching from using old code)
for mod_name in [
    'src.nodes.pipeline_2_generation.injector',
    'src.nodes.pipeline_2_generation.beautifier',
    'src.nodes.pipeline_2_generation.writer'
]:
    if mod_name in sys.modules:
        importlib.reload(sys.modules[mod_name])

from src.core.graph_pipeline2 import create_pipeline2_graph
from src.utils.registry_helper import load_all_registries
from src.core.state import PPTState
from langchain_core.runnables import RunnableConfig


# Page configuration
st.set_page_config(
    page_title="EY PPT Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #2e2e38;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FFE600;
        color: #2e2e38;
        font-weight: 600;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #E6CF00;
        border: none;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 4px solid #0c5460;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/outputs', exist_ok=True)
    os.makedirs('data/templates', exist_ok=True)
    os.makedirs('data/registry', exist_ok=True)


def get_available_templates():
    """Get list of available templates with registry status."""
    templates_dir = Path('data/templates')
    registry_dir = Path('data/registry')
    
    if not templates_dir.exists():
        return []
    
    templates = []
    for file in templates_dir.glob('*.pptx'):
        template_name = file.stem
        registry_file = registry_dir / f"{template_name}.json"
        
        templates.append({
            'filename': file.name,
            'display_name': template_name.replace('_', ' ').replace('-', ' ').title(),
            'has_registry': registry_file.exists(),
            'path': str(file)
        })
    
    return templates


def get_presentation_history():
    """Get list of previously generated presentations."""
    outputs_dir = Path('data/outputs')
    
    if not outputs_dir.exists():
        return []
    
    presentations = []
    for file in outputs_dir.glob('*.pptx'):
        stat = file.stat()
        presentations.append({
            'filename': file.name,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'size_kb': stat.st_size / 1024,
            'path': str(file)
        })
    
    # Sort by creation time (newest first)
    presentations.sort(key=lambda x: x['created'], reverse=True)
    return presentations


def generate_presentation(documentation: str, template_name: str):
    """Generate a presentation from documentation text."""
    try:
        # Load all template registries
        combined_registry = load_all_registries()
        
        if not combined_registry:
            return False, "No templates found in registry. Please run Pipeline 1 first to index templates."
        
        # Get the registry for the selected template
        template_key = Path(template_name).stem
        
        if template_key not in combined_registry:
            return False, f"Registry for {template_name} not found. Please index this template first using Pipeline 1."
        
        target_registry = combined_registry[template_key]
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"presentation_{timestamp}.pptx"
        output_path = f"data/outputs/{output_filename}"
        
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
            thread_id=f"streamlit_gen_{timestamp}",
            current_step="start"
        )
        
        # Initialize and run the graph
        progress_placeholder = st.empty()
        progress_placeholder.info("🚀 Initializing pipeline...")
        
        app_graph = create_pipeline2_graph()
        config_obj = RunnableConfig(configurable={"thread_id": f"streamlit_gen_{timestamp}"})
        
        progress_placeholder.info("📝 Processing documentation...")
        final_state = app_graph.invoke(initial_state, config=config_obj)
        
        if final_state.get("final_file_path") and os.path.exists(final_state["final_file_path"]):
            progress_placeholder.empty()
            # Return both success flag and the actual file path from the state
            return True, final_state["final_file_path"]
        else:
            errors = final_state.get('validation_errors', [])
            error_msg = '; '.join(errors) if errors else 'Unknown error occurred'
            return False, f"Failed to generate presentation: {error_msg}"
    
    except Exception as e:
        traceback.print_exc()
        return False, f"Error: {str(e)}"


# Main Application
def main():
    ensure_directories()
    
    # Header
    st.markdown('<h1 class="main-header">📊 EY Presentation Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform your documentation into professional PowerPoint presentations</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://assets.ey.com/content/dam/ey-sites/ey-com/en_gl/generic/logos/ey-logo.png", width=150)
        st.title("⚙️ Configuration")
        
        # Template selection
        templates = get_available_templates()
        
        if not templates:
            st.error("⚠️ No templates found in data/templates/")
            st.info("Please add .pptx template files to the data/templates/ directory and run Pipeline 1 to index them.")
            return
        
        template_options = {t['display_name']: t['filename'] for t in templates}
        template_display_names = list(template_options.keys())
        
        # Add registry status indicators
        template_labels = []
        for t in templates:
            status = "✅" if t['has_registry'] else "❌"
            template_labels.append(f"{status} {t['display_name']}")
        
        selected_template_label = st.selectbox(
            "Select Template",
            template_labels,
            help="✅ = Indexed and ready | ❌ = Needs indexing (run Pipeline 1)"
        )
        
        # Extract the actual template name
        selected_template_display = selected_template_label.split(' ', 1)[1]
        selected_template = template_options[selected_template_display]
        
        st.divider()
        
        # Settings
        st.subheader("📋 Settings")
        char_count_display = st.checkbox("Show character count", value=True)
        
        st.divider()
        
        # Help section
        with st.expander("ℹ️ How to Use"):
            st.markdown("""
            **Steps:**
            1. Select a template from the dropdown
            2. Enter your documentation text
            3. Click "Generate Presentation"
            4. Download your presentation!
            
            **Tips:**
            - Minimum 50 characters required
            - Longer, detailed documentation produces better results
            - Include clear headings and structure
            - Templates marked with ❌ need to be indexed first
            """)
        
        with st.expander("🔧 Indexing Templates"):
            st.markdown("""
            If a template shows ❌, you need to index it first:
            
            ```bash
            python main.py
            ```
            
            This creates the template registry needed for generation.
            """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Input Documentation")
        
        # Documentation input
        documentation = st.text_area(
            "Enter your documentation text here:",
            height=400,
            placeholder="Paste your project documentation, requirements, or any text content you want to convert into a presentation...\n\nExample: Ernst & Young (EY) is one of the world's Big Four accounting firms...",
            help="Enter the text content that will be used to generate your presentation"
        )
        
        # Character count
        if char_count_display and documentation:
            char_count = len(documentation)
            word_count = len(documentation.split())
            
            count_col1, count_col2, count_col3 = st.columns(3)
            count_col1.metric("Characters", f"{char_count:,}")
            count_col2.metric("Words", f"{word_count:,}")
            count_col3.metric("Status", "✅ Ready" if char_count >= 50 else "⚠️ Too short")
        
        # Generate button
        st.divider()
        
        if st.button("🚀 Generate Presentation", type="primary"):
            if not documentation or len(documentation.strip()) < 50:
                st.error("⚠️ Please enter at least 50 characters of documentation text.")
            else:
                with st.spinner("Generating your presentation... This may take a moment."):
                    success, result = generate_presentation(documentation, selected_template)
                    
                    if success:
                        st.success(f"✅ Presentation generated successfully!")
                        
                        # result is now the full file path
                        output_path = result
                        if os.path.exists(output_path):
                            with open(output_path, 'rb') as file:
                                filename = os.path.basename(output_path)
                                st.download_button(
                                    label="📥 Download Presentation",
                                    data=file,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                                )
                            
                            st.balloons()
                        else:
                            st.error(f"❌ File was generated but not found at: {output_path}")
                    else:
                        st.error(f"❌ {result}")
    
    with col2:
        st.subheader("📚 Recent Presentations")
        
        history = get_presentation_history()
        
        if history:
            for pres in history[:10]:  # Show last 10
                with st.container():
                    st.markdown(f"**{pres['filename']}**")
                    st.caption(f"Created: {pres['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.caption(f"Size: {pres['size_kb']:.1f} KB")
                    
                    # Download button for each presentation
                    with open(pres['path'], 'rb') as file:
                        st.download_button(
                            label="📥 Download",
                            data=file,
                            file_name=pres['filename'],
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            key=f"download_{pres['filename']}"
                        )
                    
                    st.divider()
        else:
            st.info("No presentations generated yet. Create your first one!")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>EY Presentation Generator | Built with Streamlit & LangGraph</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
