import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import base64

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DocuGenius Pro", page_icon="📑")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1e3a8a; text-align: center; }
    /* Make the text area taller and monospace for easier editing */
    .stTextArea textarea { height: 600px; font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: Display PDF in Browser ---
def display_pdf(uploaded_file):
    # Read file as bytes:
    bytes_data = uploaded_file.getvalue()
    # Convert to base64
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    # Embed PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- HELPER: Generate Word Doc ---
def generate_docx(text_content):
    doc = Document()
    for line in text_content.split('\n'):
        if line.startswith('# '): doc.add_heading(line[2:], level=1)
        elif line.startswith('## '): doc.add_heading(line[2:], level=2)
        elif line.startswith('### '): doc.add_heading(line[2:], level=3)
        elif line.startswith('* '): doc.add_paragraph(line[2:], style='List Bullet')
        else: doc.add_paragraph(line)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- MAIN APP ---
def main():
    # 1. Sidebar - Settings
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # API Key
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("API Key Found ✅")
        except:
            api_key = st.text_input("Gemini API Key", type="password")

        st.divider()
        
        # AI Customization
        st.subheader("Conversion Style")
        conversion_mode = st.radio("Mode:", ["Exact Transcription", "Summarize", "Translate to English", "Fix Grammar"])
        
        st.info("💡 'Exact Transcription' tries to keep the layout same. Others will change the text.")

    # 2. Main Area
    st.markdown('<div class="main-header">DocuGenius Pro 🚀</div>', unsafe_allow_html=True)

    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = ""

    # Upload Area
    if not st.session_state.generated_content:
        uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
        
        if uploaded_file and st.button("Start Processing", type="primary"):
            if not api_key:
                st.error("Please enter an API Key in the Sidebar.")
            else:
                genai.configure(api_key=api_key)
                with st.spinner("🤖 Reading Document..."):
                    try:
                        model = genai.GenerativeModel('gemini-3-pro-preview')
                        
                        # Dynamic Prompt based on Sidebar selection
                        base_prompt = "Extract text from this PDF."
                        if conversion_mode == "Exact Transcription":
                            instruction = "Keep layout identical. Use Markdown headers (#) and bullets (*). Output raw text only."
                        elif conversion_mode == "Summarize":
                            instruction = "Summarize the key points of this document in Markdown bullet points."
                        elif conversion_mode == "Translate to English":
                            instruction = "Translate all text to English. Maintain original formatting."
                        elif conversion_mode == "Fix Grammar":
                            instruction = "Correct all grammar and spelling mistakes. Keep original meaning and formatting."
                        
                        full_prompt = f"{base_prompt} {instruction}"

                        response = model.generate_content([
                            {'mime_type': 'application/pdf', 'data': uploaded_file.getvalue()},
                            full_prompt
                        ])
                        
                        st.session_state.generated_content = response.text
                        st.session_state.uploaded_file = uploaded_file # Save file for preview
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # 3. Editor View (Split Screen)
    else:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📄 Original PDF")
            # Show the PDF used
            if 'uploaded_file' in st.session_state:
                display_pdf(st.session_state.uploaded_file)

        with col2:
            st.subheader("📝 Editable Text")
            edited_text = st.text_area("Make changes here:", value=st.session_state.generated_content, height=550)
            st.session_state.generated_content = edited_text
            
            # Download Logic
            docx = generate_docx(st.session_state.generated_content)
            st.download_button(
                "⬇️ Download Word Doc", 
                data=docx, 
                file_name="converted.docx", 
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
            
            if st.button("🔄 Start New File"):
                st.session_state.generated_content = ""
                st.rerun()

if __name__ == "__main__":
    main()
