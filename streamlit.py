import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# 1. Page Config
st.set_page_config(
    page_title="DocuGenius AI (Gemini 3)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; font-family: 'Helvetica Neue', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Card Container */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-width: 900px;
        margin: auto;
    }

    /* Titles */
    .title-text {
        text-align: center;
        background: -webkit-linear-gradient(45deg, #4285F4, #9B72CB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .subtitle-text { text-align: center; color: #5f6368; font-size: 1.2rem; margin-bottom: 2rem; }

    /* Text Area for Editing */
    textarea {
        font-size: 1rem !important;
        font-family: 'Courier New', monospace !important;
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = ""
if 'file_name' not in st.session_state:
    st.session_state.file_name = "document"

# 4. Helper Function: Convert Markdown text to Docx object
def generate_docx(text_content):
    doc = Document()
    doc.add_heading(st.session_state.file_name, 0)

    for line in text_content.split('\n'):
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
            doc.add_paragraph(line[2:], style='List Bullet')
        else:
            doc.add_paragraph(line)
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# 5. Main App Logic
def main():
    st.markdown('<div class="title-text">DocuGenius AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">Convert & Edit PDFs with <b>Gemini 3 Pro</b></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 8, 1])

    with col2:
        # -- API Key Input --
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
        except:
            api_key = st.text_input("🔑 Enter Gemini API Key:", type="password")

        if api_key:
            genai.configure(api_key=api_key)

        # -- File Upload Section --
        # Only show upload if we haven't generated content yet OR if user wants to start over
        if not st.session_state.generated_content:
            uploaded_file = st.file_uploader("📂 Drag & Drop PDF", type=['pdf'])

            if uploaded_file and st.button("✨ Convert with Gemini 3 Pro", type="primary"):
                if not api_key:
                    st.error("Please provide an API Key first.")
                else:
                    with st.spinner("🚀 Analyzing text structure..."):
                        try:
                            # Gemini 3 Pro Call
                            model = genai.GenerativeModel('gemini-3-pro-preview')
                            prompt = """
                            Extract all text from this PDF.
                            - Format as clean Markdown (# for headers, * for bullets).
                            - Preserve tables and logical flow.
                            - NO conversational filler.
                            """
                            response = model.generate_content([
                                {'mime_type': 'application/pdf', 'data': uploaded_file.getvalue()},
                                prompt
                            ])
                            
                            # Save to Session State
                            st.session_state.generated_content = response.text
                            st.session_state.file_name = uploaded_file.name.split('.')[0]
                            st.rerun() # Refresh to show editor
                        except Exception as e:
                            st.error(f"Error: {e}")

        # -- Editor Section (Shows after conversion) --
        else:
            st.success("✅ Conversion successful! You can edit the text below before downloading.")
            
            # 1. The Editor
            # The 'value' is read from state, and changes update the key 'generated_content' automatically
            edited_text = st.text_area(
                "📝 Edit Document Content (Markdown format supported):", 
                value=st.session_state.generated_content,
                height=400
            )
            
            # Update state explicitly just in case
            st.session_state.generated_content = edited_text

            col_a, col_b = st.columns(2)
            
            with col_a:
                # 2. Download Button
                docx_file = generate_docx(st.session_state.generated_content)
                st.download_button(
                    label="⬇️ Download Word Doc",
                    data=docx_file,
                    file_name=f"{st.session_state.file_name}_edited.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )

            with col_b:
                # 3. Reset Button
                if st.button("🔄 Start Over / New File", use_container_width=True):
                    st.session_state.generated_content = ""
                    st.rerun()

if __name__ == "__main__":
    main()
