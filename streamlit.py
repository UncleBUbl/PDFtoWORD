import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# 1. Configuration
st.set_page_config(page_title="PDF to Word (Gemini 3 Pro)", layout="wide")
st.title("📄 PDF to Word Converter (Powered by Gemini 3)")

# Securely get API Key from Streamlit Secrets
# Make sure you have added GOOGLE_API_KEY in your Streamlit Cloud secrets!
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    # Fallback for local testing if secrets.toml isn't set up
    api_key = st.text_input("Enter your Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)

    # 2. File Upload
    uploaded_file = st.file_uploader("Upload your PDF", type=['pdf'])

    if uploaded_file and st.button("Convert to Word"):
        with st.spinner("Gemini 3 Pro is analyzing and converting..."):
            try:
                # --- UPDATE: Using Gemini 3 Pro Preview ---
                # Note: If 'gemini-3-pro-preview' gives a 404, try 'gemini-exp-1121' 
                # or check the available models list.
                model = genai.GenerativeModel('gemini-3-pro-preview')

                # Prepare PDF data
                pdf_data = uploaded_file.getvalue()
                
                # Prompt
                prompt = """
                Extract all text from this PDF document.
                - specific formatting: Use standard Markdown (# for headers, * for bullets).
                - preservation: Keep the original flow and structure.
                - output: strictly the content, no intro/outro filler.
                """
                
                # Generate
                response = model.generate_content([
                    {'mime_type': 'application/pdf', 'data': pdf_data},
                    prompt
                ])
                
                extracted_text = response.text

                # 3. Create Word Document
                doc = Document()
                doc.add_heading('Converted Document', 0)
                
                for line in extracted_text.split('\n'):
                    # Simple markdown-to-word logic
                    if line.startswith('# '):
                        doc.add_heading(line[2:], level=1)
                    elif line.startswith('## '):
                        doc.add_heading(line[2:], level=2)
                    elif line.startswith('### '):
                        doc.add_heading(line[2:], level=3)
                    elif line.strip():
                        doc.add_paragraph(line)

                # Save to buffer
                bio = BytesIO()
                doc.save(bio)
                
                # 4. Download
                st.download_button(
                    label="⬇️ Download Word Doc",
                    data=bio.getvalue(),
                    file_name="converted_gemini3.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                # Preview
                with st.expander("View Extracted Text"):
                    st.markdown(extracted_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
                
                # Troubleshooting Helper: List available models if 404 persists
                if "404" in str(e):
                    st.warning("⚠️ Troubleshooting: Attempting to list available models...")
                    try:
                        st.write("Available models for your key:")
                        for m in genai.list_models():
                            if 'generateContent' in m.supported_generation_methods:
                                st.code(m.name)
                    except:
                        st.write("Could not list models. Check your API Key.")
