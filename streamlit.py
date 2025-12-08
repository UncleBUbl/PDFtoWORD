import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# 1. Page Config (Must be the first command)
st.set_page_config(
    page_title="DocuGenius AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Custom CSS for "SaaS" Look
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
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
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        max-width: 800px;
        margin: auto;
    }

    /* Custom Title */
    .title-text {
        text-align: center;
        color: #1a1a1a;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle-text {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
    }

    /* Style the File Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #e0e0e0;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        transition: border-color 0.3s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #4CAF50;
    }

    /* Style the Button */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        width: 100%;
        transition: background-color 0.3s, transform 0.1s;
    }
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Success Message Box */
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin-top: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 3. Secure API Key Setup
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    api_key = "" # Leave empty, we will ask user or handle gracefully

# 4. Main App Logic
def main():
    # -- Header Section --
    st.markdown('<div class="title-text">DocuGenius AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">Convert locked PDFs into editable Word documents instantly.</div>', unsafe_allow_html=True)

    # -- Layout: Center Column --
    col1, col2, col3 = st.columns([1, 6, 1])

    with col2:
        # Check for API Key
        if not api_key:
            user_key = st.text_input("🔑 Enter Gemini API Key to start:", type="password")
            if user_key:
                genai.configure(api_key=user_key)
        else:
            genai.configure(api_key=api_key)

        # File Upload
        uploaded_file = st.file_uploader("Drop your PDF here", type=['pdf'])

        # Action Button
        if uploaded_file:
            if st.button("✨ Convert to Word Document"):
                if not api_key and not user_key:
                    st.error("Please provide an API Key first.")
                else:
                    process_file(uploaded_file)

def process_file(uploaded_file):
    with st.spinner("🤖 AI is reading and formatting your document..."):
        try:
            # Initialize Model (Using the latest stable model)
            model = genai.GenerativeModel('gemini-1.5-flash') 

            # Prepare Data
            pdf_data = uploaded_file.getvalue()
            
            prompt = """
            You are a professional document converter. 
            Read this PDF and convert it into clean, structured text.
            1. Keep all Headers (#), Bullet points (*), and Tables intact.
            2. Do not summarize; extract the full content.
            3. Do not add introductory text (like "Here is the file").
            """

            # Call Gemini
            response = model.generate_content([
                {'mime_type': 'application/pdf', 'data': pdf_data},
                prompt
            ])
            
            extracted_text = response.text

            # Convert Markdown to Word
            doc = Document()
            doc.add_heading('Converted Document', 0)

            for line in extracted_text.split('\n'):
                if line.startswith('# '):
                    doc.add_heading(line[2:], level=1)
                elif line.startswith('## '):
                    doc.add_heading(line[2:], level=2)
                elif line.startswith('### '):
                    doc.add_heading(line[2:], level=3)
                elif line.startswith('* ') or line.startswith('- '):
                    doc.add_paragraph(line[2:], style='List Bullet')
                elif line.strip():
                    doc.add_paragraph(line)

            # Save to Memory Buffer
            bio = BytesIO()
            doc.save(bio)
            
            # Success & Download
            st.markdown('<div class="success-box">✅ Conversion Complete!</div>', unsafe_allow_html=True)
            st.write("") # Spacer
            
            st.download_button(
                label="⬇️ Download Word Document (.docx)",
                data=bio.getvalue(),
                file_name=f"{uploaded_file.name.split('.')[0]}_editable.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

            # Optional Preview
            with st.expander("👁️ View Extracted Content"):
                st.markdown(extracted_text)

        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
            st.info("Tip: If you get a 404 error, the model name might have changed. Try 'gemini-1.5-pro' or check Google AI Studio.")

if __name__ == "__main__":
    main()
