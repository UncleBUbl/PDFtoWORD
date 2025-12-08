import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# 1. Configuration
st.set_page_config(page_title="PDF to Word Converter", layout="wide")
st.title("📄 AI PDF to Editable Word Doc")

# API Key Input
api_key = st.text_input("Enter your Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=aAIzaSyCz3lqRAfl6A1URitgiFWxnh0bdHLiQQXY)

    # 2. File Upload
    uploaded_file = st.file_uploader("Upload your PDF", type=['pdf'])

    if uploaded_file and st.button("Convert to Word"):
        with st.spinner("AI is reading and converting..."):
            try:
                # Load Model
                model = genai.GenerativeModel('gemini-1.5-flash')

                # Prepare the PDF for the API
                pdf_data = uploaded_file.getvalue()
                
                # Prompt the AI
                prompt = """
                You are a document conversion expert. 
                Extract the content from this PDF file. 
                Keep headers, bullet points, and paragraphs clear. 
                Do not include any introductory text like "Here is the content", just give me the raw text content.
                """
                
                # Generate Content
                response = model.generate_content([
                    {'mime_type': 'application/pdf', 'data': pdf_data},
                    prompt
                ])
                
                extracted_text = response.text

                # 3. Create Word Document
                doc = Document()
                doc.add_heading('Converted Document', 0)
                
                # Simple logic to add text to Word doc (splits by newlines)
                for paragraph in extracted_text.split('\n'):
                    if paragraph.strip():
                        doc.add_paragraph(paragraph)

                # Save to a buffer (memory)
                bio = BytesIO()
                doc.save(bio)
                
                # 4. Download Button
                st.download_button(
                    label="⬇️ Download Word Doc",
                    data=bio.getvalue(),
                    file_name="converted_doc.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                # Show preview
                st.subheader("Preview:")
                st.markdown(extracted_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
