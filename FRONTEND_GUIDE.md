# 🎨 Frontend Guide: Streamlit Web Application

## Overview

The **EY Presentation Generator** frontend provides an intuitive web interface for transforming documentation into professional PowerPoint presentations. Built with Streamlit, it offers a modern, responsive UI that makes PPT generation accessible to all users.

---

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Navigate to the project directory
cd "PPT generation\ppt-generation"

# Install required packages
pip install -r requirements.txt
```

### 2. Setup Environment

Ensure your `.env` file contains the necessary API keys:

```env
OPENAI_API_KEY=your_api_key_here
# or
ANTHROPIC_API_KEY=your_api_key_here
# or
GOOGLE_API_KEY=your_api_key_here
```

### 3. Index Templates (First Time Only)

Before using the frontend, you need to index your PowerPoint templates:

```powershell
python main.py
```

This creates the registry files needed for presentation generation.

### 4. Launch the Frontend

```powershell
streamlit run streamlit_app.py
```

The application will open automatically in your default web browser at `http://localhost:8501`

---

## 📋 Features

### ✨ Main Features

1. **Template Selection**
   - Choose from available PowerPoint templates
   - Visual indicators show which templates are ready to use (✅) or need indexing (❌)

2. **Documentation Input**
   - Large text area for pasting documentation
   - Real-time character and word count
   - Minimum 50 characters required

3. **One-Click Generation**
   - Generate presentations with a single click
   - Real-time progress indicators
   - Automatic validation

4. **Instant Downloads**
   - Download generated presentations immediately
   - Access presentation history
   - Quick re-download from history

5. **Presentation History**
   - View recently generated presentations
   - See creation timestamps and file sizes
   - Download any previous presentation

### 🎯 User Interface Sections

#### Left Panel: Generation Interface
- **Documentation Input**: Large text area for your content
- **Character Counter**: Shows character count, word count, and status
- **Generate Button**: Initiates the presentation generation

#### Right Panel: History
- **Recent Presentations**: Lists up to 10 most recent presentations
- **Quick Download**: Download buttons for each presentation
- **File Details**: Filename, creation date, and file size

#### Sidebar: Configuration
- **Template Selector**: Choose your PowerPoint template
- **Settings**: Toggle character count display
- **Help Sections**: Instructions and troubleshooting

---

## 📖 How to Use

### Step-by-Step Guide

1. **Launch the Application**
   ```powershell
   streamlit run streamlit_app.py
   ```

2. **Select a Template**
   - Open the sidebar (left side)
   - Choose a template from the dropdown
   - Ensure the template has a ✅ (indexed)
   - If it shows ❌, run `python main.py` first

3. **Enter Your Documentation**
   - Paste or type your documentation in the text area
   - Minimum 50 characters required
   - The more detailed, the better the results

4. **Generate Presentation**
   - Click the "🚀 Generate Presentation" button
   - Wait for the progress indicator to complete
   - Success message will appear when done

5. **Download Your Presentation**
   - Click the "📥 Download Presentation" button
   - The .pptx file will be saved to your downloads folder
   - You can also access it from the "Recent Presentations" panel

---

## 🔧 Configuration

### Directory Structure

The application expects the following directory structure:

```
ppt-generation/
├── streamlit_app.py          # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
└── data/
    ├── templates/             # PowerPoint template files (.pptx)
    ├── registry/              # Template metadata (auto-generated)
    ├── outputs/               # Generated presentations
    └── uploads/               # Uploaded files (if any)
```

### Environment Variables

Create a `.env` file with your AI provider credentials:

```env
# OpenAI (recommended)
OPENAI_API_KEY=sk-...

# OR Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# OR Google Gemini
GOOGLE_API_KEY=...

# Azure (if using Azure OpenAI)
AZURE_OPENAI_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
```

---

## 💡 Tips for Best Results

### Documentation Best Practices

1. **Be Detailed**: Include comprehensive information
   - The AI works better with more context
   - Aim for at least 500-1000 characters

2. **Structure Your Content**: Use clear headings and sections
   - Main topics and subtopics
   - Bullet points or numbered lists
   - Clear paragraph breaks

3. **Include Key Information**:
   - Project overview
   - Key features or capabilities
   - Benefits and value propositions
   - Technical details (if applicable)
   - Timeline or roadmap (if applicable)

### Example Good Documentation

```
Ernst & Young (EY) Auditing Services

Overview:
Ernst & Young (EY) is one of the world's "Big Four" accounting firms...

Key Services:
- Financial statement audits
- Internal control evaluations
- Compliance audits
- Risk assessment services

Technology Integration:
EY leverages advanced platforms like EY Helix for data analytics...

Global Presence:
Operating in 150+ countries with coordinated methodologies...
```

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: "No templates found"
**Solution**: 
1. Add .pptx files to `data/templates/` directory
2. Run `python main.py` to index them

#### Issue: Template shows ❌ (not indexed)
**Solution**:
```powershell
python main.py
```
This will create the registry for all templates.

#### Issue: "Documentation text is too short"
**Solution**: Ensure your text has at least 50 characters. For best results, use 500+ characters.

#### Issue: Generation fails with API error
**Solution**:
1. Check your `.env` file has valid API keys
2. Verify your API key has sufficient credits
3. Check your internet connection

#### Issue: Application won't start
**Solution**:
```powershell
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Try running again
streamlit run streamlit_app.py
```

#### Issue: Port 8501 already in use
**Solution**:
```powershell
# Use a different port
streamlit run streamlit_app.py --server.port 8502
```

---

## 🎨 Customization

### Changing EY Branding

The application includes EY-specific branding. To customize:

1. **Logo**: Update the image URL in `streamlit_app.py`:
   ```python
   st.image("your_logo_url_here", width=150)
   ```

2. **Colors**: Modify the CSS in the `st.markdown()` section:
   ```python
   .stButton>button {
       background-color: #YOUR_COLOR;  # Change button color
   }
   ```

3. **Page Title**: Change in `st.set_page_config()`:
   ```python
   st.set_page_config(
       page_title="Your Company Name",
       page_icon="📊",
   )
   ```

---

## 🚀 Advanced Usage

### Running in Production

For production deployment, consider:

1. **Streamlit Cloud**: Deploy directly to Streamlit Cloud
   ```bash
   # Push to GitHub and connect to Streamlit Cloud
   ```

2. **Docker**: Containerize the application
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["streamlit", "run", "streamlit_app.py"]
   ```

3. **Custom Domain**: Use Streamlit's custom domain feature

### Performance Optimization

- **Caching**: The app uses Streamlit's caching for template loading
- **Session State**: Maintains user inputs across reruns
- **Lazy Loading**: Templates are loaded only when needed

---

## 📊 Application Flow

```
User Opens App
    ↓
Selects Template (from sidebar)
    ↓
Enters Documentation (in text area)
    ↓
Clicks Generate Button
    ↓
Backend Processes:
  1. Validates input (50+ chars)
  2. Loads template registry
  3. Runs Pipeline 2 graph
  4. Generates slides
  5. Creates .pptx file
    ↓
Shows Success Message + Download Button
    ↓
User Downloads Presentation
```

---

## 🔐 Security Notes

- **API Keys**: Never commit `.env` file to version control
- **File Upload**: Currently disabled; can be enabled if needed
- **Output Storage**: Generated files are stored locally in `data/outputs/`
- **Access Control**: Add authentication if deploying publicly

---

## 📞 Support

### Getting Help

1. **Documentation**: Read this guide and `QUICK_START.md`
2. **Code Comments**: Check inline comments in `streamlit_app.py`
3. **Error Messages**: Pay attention to error messages in the UI
4. **Logs**: Check terminal output for detailed error traces

### Reporting Issues

When reporting issues, include:
- Error message (full text)
- Steps to reproduce
- Screenshot (if applicable)
- Your Python version: `python --version`
- Your Streamlit version: `streamlit --version`

---

## 🎯 Next Steps

After successfully using the frontend:

1. **Customize Templates**: Add your own PowerPoint templates
2. **Integrate Images**: Enhance the Image Director node
3. **Add Authentication**: Implement user login for multi-user environments
4. **Deploy to Cloud**: Share with your team via Streamlit Cloud
5. **API Integration**: Connect to corporate document repositories

---

## 📝 Changelog

### Version 1.0 (February 2026)
- ✨ Initial release with Streamlit frontend
- 📊 Template selection and validation
- 📝 Documentation input with character counter
- 🎨 EY-branded modern UI
- 📥 Download functionality
- 📚 Presentation history panel
- 🔧 Configuration sidebar
- ℹ️ Integrated help sections

---

**Built with ❤️ using Streamlit, LangGraph, and Python-PPTX**
