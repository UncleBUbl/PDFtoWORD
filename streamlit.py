import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# 1. Page Config (Must be the first command)
st.set_page_config(
    page_title="DocuGenius AI (Gemini 3)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Custom CSS for "SaaS" Look
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f0f2f6;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Center Container (Card Look) */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: white;
        padding: 3rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-width: 800px;
        margin: auto;
    }

    /* Custom Title */
    .title-text {
        text-align: center;
        background: -webkit-linear-gradient(45deg, #4285F4, #9B72CB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle-text {
        text-align: center;
        color: #5f6368;
        font-size: 1.2rem;
        margin-bottom: 2.5rem;
    }

    /* Style the File Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #a0a0a0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
        background-color: #fafafa;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #4285F4;
        background-color: #f0f7ff;
    }

    /* Style the Button */
    .stButton > button {
        background: linear-gradient(90deg, #4285F4 0%, #2b6cb0 100%);
        color: white;
        border: none;
        padding: 0.85rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 10px;
        width: 100%;
        box-shadow: 0 4px 6px rgba(66, 133, 244, 0.3);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(66, 133, 244, 0.4);
    }
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Success Message Box */
    .success-box {
        padding: 1.5rem;
        background-color: #e6fffa;
        color: #2c7a7b;
        border-radius: 10px;
        border: 1px solid #b2f5ea;
        margin-top: 1.5rem;
        text-align: center;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# 3. Secure API Key Setup
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    api_key = "" 

# 4. Main App Logic
def main():
    # -- Header Section --
    st.markdown('<div class="title-text">DocuGenius AI</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle-text">Powered by <b>Gemini 3 Pro Preview</b></div>', unsafe_allow_html=True)

    # -- Layout: Center Column --
    col1, col2, col3 = st.columns([1, 8, 1])

    with col2:
        # Check for API Key if not in secrets
        if not api_key:
            user_key = st.text_input("🔑 Enter Gemini API Key:", type="password")
            if user_key:
                genai.configure(api_key=user_key)
        else:
            genai.configure(api_key=api_key)

        # File Upload
        uploaded_file = st.file_uploader("📂 Drag & Drop your PDF here", type=['pdf'])

        # Action Button
        if uploaded_file:
            if st.button("✨ Convert with Gemini 3 Pro"):
                if not api_key and not user_key:
                    st.error("Please provide an API Key first.")
                else:
                    process_file(uploaded_file)

def process_file(uploaded_file):
    with st.spinner("🚀 Gemini 3 Pro is processing... (Reading text, tables & layout)"):
        try:
            # --- MODEL SELECTION: GEMINI 3 PRO PREVIEW ---
            # Using the specific model ID you requested
            model = genai.GenerativeModel('gemini-3-pro-preview') 

            # Prepare Data
            pdf_data = uploaded_file.getvalue()
            
            prompt = """
            You are an advanced document conversion AI.
            Task: Convert this PDF into a structured, editable format.
            
            Requirements:
            1. Extract ALL text, preserving headers (use #), lists (*), and bolding (**).
            2. Detect tables and format them as Markdown tables.
            3. Do NOT add any conversational filler (no "Here is your document").
            4. Output RAW Markdown only.
            """

            # Call Gemini
            response = model.generate_content([
                {'mime_type': 'application/pdf', 'data': pdf_data},
                prompt
            ])
            
            extracted_text = response.text

            # Convert Markdown to Word
            doc = Document()
            
            # Add a title based on filename
            safe_filename = uploaded_file.name.split('.')[0]
            doc.add_heading(safe_filename, 0)

            for line in extracted_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('# '):
                    doc.add_heading(line[2:], level=1)
                elif line.startswith('## '):
                    doc.add_heading(line[2:], level=2)
                elif line.startswith('### '):
                    doc.add_heading(line[2:], level=3)
                elif line.startswith('* ') or line.startswith('- '):
                    p = doc.add_paragraph(line[2:], style='List Bullet')
                else:
                    doc.add_paragraph(line)

            # Save to Memory Buffer
            bio = BytesIO()
            doc.save(bio)
            
            # Success & Download
            st.markdown('<div class="success-box">✅ Conversion Complete! Your document is ready.</div>', unsafe_allow_html=True)
            st.write("") # Spacer
            
            st.download_button(
                label="⬇️ Download Word Document (.docx)",
                data=bio.getvalue(),
                file_name=f"{safe_filename}_gemini3.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

            # Optional Preview
            with st.expander("👁️ View Extracted Content Preview"):
                st.markdown(extracted_text)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            if "404" in str(e):
                st.warning(f"Double check the model name. attempted to use: 'gemini-3-pro-preview'")

if __name__ == "__main__":
    main()
