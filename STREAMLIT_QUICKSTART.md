# 🚀 Streamlit Frontend - Quick Start

## What is This?

A beautiful, user-friendly web interface for your EY PPT Generation system. Generate professional PowerPoint presentations from documentation text with just a few clicks!

---

## ⚡ Quick Start (30 seconds)

### 1. Install Dependencies (First Time Only)

```powershell
pip install -r requirements.txt
```

### 2. Ensure Templates are Indexed

```powershell
# Index your PowerPoint templates (only needed once per template)
python main.py
```

### 3. Launch the Frontend

```powershell
streamlit run streamlit_app.py
```

### 4. Open in Browser

The app automatically opens at: **http://localhost:8501**

---

## 📊 Using the Application

### Step 1: Select a Template
- Look at the sidebar (left side)
- Choose a template from the dropdown
- ✅ = Ready to use
- ❌ = Needs indexing (run `python main.py`)

### Step 2: Enter Documentation
- Paste your text in the main input area
- Minimum 50 characters
- Longer text = Better presentations

### Step 3: Generate
- Click **"🚀 Generate Presentation"**
- Wait for the process to complete (usually 30-60 seconds)
- Success message will appear!

### Step 4: Download
- Click **"📥 Download Presentation"**
- Your .pptx file is ready!

---

## 🎯 Features

### ✨ Main Panel
- **Large Text Editor**: Paste documentation (supports long texts)
- **Character Counter**: Real-time feedback on text length
- **Generate Button**: One-click presentation creation
- **Download Button**: Instant download after generation

### 📚 History Panel (Right Side)
- View last 10 generated presentations
- See creation date and file size
- Download any previous presentation

### ⚙️ Sidebar (Left Side)
- **Template Selection**: Choose your PowerPoint template
- **Settings**: Toggle character count display
- **Help Section**: Quick how-to guide
- **Indexing Guide**: Template setup instructions

---

## 🎨 Screenshots (What You'll See)

### Main Interface
```
┌─────────────────────────────────────────────────────────────┐
│  📊 EY Presentation Generator                               │
│  Transform your documentation into professional PowerPoints │
├─────────────────────────────────────────────────────────────┤
│  Sidebar          │  Input Area        │  History           │
│  ┌──────┐        │  ┌──────────────┐  │  ┌──────────────┐  │
│  │ ✅ Temp│        │  │Documentation │  │  │presentation_ │  │
│  │ ❌ Temp│        │  │   ...        │  │  │  20260216... │  │
│  │      │        │  │              │  │  │  [Download▼] │  │
│  └──────┘        │  └──────────────┘  │  └──────────────┘  │
│                  │  [Generate🚀]      │                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Pro Tips

### For Best Results:
1. **Clear Structure**: Use headings and paragraphs
2. **Detailed Content**: More detail = Better slides
3. **Organized Text**: Bullet points and lists work well
4. **Length**: 500-2000 words ideal

### Good Documentation Example:
```
Product Overview:
Our AI solution transforms business processes...

Key Features:
- Automated data processing
- Real-time analytics
- Cloud-based infrastructure

Benefits:
Companies using our solution see 40% efficiency gains...
```

### What Happens Behind the Scenes:
1. ✅ Your text is analyzed by AI
2. ✅ Slide structure is planned
3. ✅ Content is formatted for PowerPoint
4. ✅ Slides are generated with proper layouts
5. ✅ Professional styling is applied

---

## 🔧 Troubleshooting

### "No templates found"
- **Fix**: Add .pptx files to `data/templates/` folder
- **Then Run**: `python main.py`

### Template shows ❌
- **Fix**: Run `python main.py` to index templates
- Creates registry files in `data/registry/`

### "API key not found" error
- **Fix**: Check your `.env` file contains:
  ```env
  OPENAI_API_KEY=your_key_here
  # OR any other supported provider
  ```

### Application won't start
- **Fix 1**: Reinstall dependencies
  ```powershell
  pip install -r requirements.txt --upgrade
  ```
- **Fix 2**: Check Python version (3.11+ recommended)
  ```powershell
  python --version
  ```

### Port 8501 already in use
- **Fix**: Use a different port
  ```powershell
  streamlit run streamlit_app.py --server.port 8502
  ```

### Generation takes too long
- **Normal**: 30-90 seconds depending on text length
- **Tip**: Check progress messages in terminal

---

## 🎯 Advanced Options

### Run on Custom Port
```powershell
streamlit run streamlit_app.py --server.port 8080
```

### Run on All Interfaces (Network Access)
```powershell
streamlit run streamlit_app.py --server.address 0.0.0.0
```

### Production Mode (No File Watching)
```powershell
streamlit run streamlit_app.py --server.runOnSave false
```

### Custom Theme
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FFE600"  # EY Yellow
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F0F0"
textColor = "#2e2e38"
font = "sans serif"
```

---

## 📁 File Locations

- **Generated Presentations**: `data/outputs/presentation_YYYYMMDD_HHMMSS.pptx`
- **Templates**: `data/templates/*.pptx`
- **Registry (Metadata)**: `data/registry/*.json`
- **Configuration**: `.env`

---

## 🔐 Security Notes

- ✅ API keys stored securely in `.env` (not in code)
- ✅ Files saved locally only
- ✅ No external data transmission (except to AI API)
- ⚠️ Don't commit `.env` to version control

---

## 🚀 What's Next?

After creating your first presentation:

1. **Customize Templates**: Create your own .pptx templates
2. **Adjust Settings**: Modify slidegeneration parameters
3. **Share Access**: Deploy to Streamlit Cloud for team access
4. **Integrate APIs**: Connect to document management systems

---

## 📊 System Requirements

- **Python**: 3.11 or higher (3.14 is supported)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for dependencies + generated files
- **Internet**: Required for AI API calls
- **Browser**: Chrome, Firefox, Edge, Safari (modern versions)

---

## 🆘 Need Help?

1. **Check Terminal**: Error messages show in PowerShell
2. **Read FRONTEND_GUIDE.md**: Comprehensive documentation
3. **Verify Setup**: Ensure templates are indexed
4. **Test API**: Run `python test_auth.py` to verify API keys

---

## 🎉 Success Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file configured with API key
- [ ] Templates added to `data/templates/`
- [ ] Templates indexed (`python main.py`)
- [ ] Streamlit running (`streamlit run streamlit_app.py`)
- [ ] Browser open at http://localhost:8501
- [ ] First presentation generated successfully!

---

**🎊 Congratulations! You're ready to generate professional presentations with ease!**

---

## Quick Commands Reference

```powershell
# Install
pip install -r requirements.txt

# Index templates
python main.py

# Start frontend
streamlit run streamlit_app.py

# Custom port
streamlit run streamlit_app.py --server.port 8080

# Check Python version
python --version

# Upgrade all packages
pip install -r requirements.txt --upgrade
```

---

**Built with ❤️ using Streamlit** | [Full Docs](FRONTEND_GUIDE.md)
