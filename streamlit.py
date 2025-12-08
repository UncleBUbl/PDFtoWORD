import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import base64

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DocuGenius Pro", page_icon="📑")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    
    /* Make the editor font monospace so tables align visually in the browser */
    .stTextArea textarea { 
        font-family: 'Courier New', monospace; 
        font-size: 14px; 
        line-height: 1.5;
    }
    
    .main-header { 
        font-size: 2rem; 
        font-weight: 700; 
        color: #1a73e8; 
        text-align: center; 
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER: Display PDF ---
def display_pdf(pdf_bytes):
    """
    Displays the PDF using an <embed> tag which is more robust than iframe.
    """
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- HELPER: Advanced Markdown to Docx ---
def create_table_from_markdown(doc, table_lines):
    """
    Parses a list of Markdown table lines and adds a real table to the Docx.
    """
    try:
        # Filter out the separator line (e.g., |---|---|)
        rows = [row for row in table_lines if '---' not in row]
        
        if not rows:
            return

        # Determine dimensions
        # Split by '|' and remove empty first/last elements created by split
        header_cells = [c.strip() for c in rows[0].split('|') if c.strip() != '']
        num_cols = len(header_cells)
        
        # Create Table in Word
        table = doc.add_table(rows=len(rows), cols=num_cols)
        table.style = 'Table Grid' # Gives it borders
        
        for i, row_text in enumerate(rows):
            # Parse cells
            cells_text = [c.strip() for c in row_text.split('|') if c.strip() != '']
            
            # Safe fill (prevent index errors if row is malformed)
            for j, text in enumerate(cells_text):
                if j < num_cols:
                    table.cell(i, j).text = text
    except Exception:
        # Fallback: if table parsing fails, just write lines
        for line in table_lines:
            doc.add_paragraph(line)

def generate_docx(text_content):
    doc = Document()
    
    # Iterate through lines to detect tables vs text
    lines = text_content.split('\n')
    table_buffer = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line looks like a table row
        if stripped.startswith('|') and stripped.endswith('|'):
            table_buffer.append(stripped)
        else:
            # If we were building a table, convert it now
            if table_buffer:
                create_table_from_markdown(doc, table_buffer)
                table_buffer = [] # Reset buffer
            
            # Process normal text
            if line.startswith('# '): doc.add_heading(line[2:], level=1)
            elif line.startswith('## '): doc.add_heading(line[2:], level=2)
            elif line.startswith('### '): doc.add_heading(line[2:], level=3)
            elif line.startswith('* ') or line.startswith('- '):
                doc.add_paragraph(line[2:], style='List Bullet')
            elif stripped:
                doc.add_paragraph(line)
    
    # Catch any table at the very end of the file
    if table_buffer:
        create_table_from_markdown(doc, table_buffer)

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- MAIN APP ---
def main():
    # 1. Sidebar
    with st.sidebar:
        st.title("⚙️ Settings")
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("API Key Active")
        except:
            api_key = st.text_input("Gemini API Key", type="password")

        st.info("Tip: If tables look messy in the text box, don't worry! They will look perfect in the downloaded Word Doc.")

    # 2. Header
    st.markdown('<div class="main-header">DocuGenius Pro 🚀</div>', unsafe_allow_html=True)

    # 3. Session State Management
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = ""
    if 'pdf_bytes' not in st.session_state:
        st.session_state.pdf_bytes = None

    # 4. Upload View
    if not st.session_state.generated_content:
        uploaded_file = st.file_uploader("Upload PDF (Tables supported)", type=['pdf'])
        
        if uploaded_file and st.button("🚀 Convert Now", type="primary"):
            if not api_key:
                st.error("Please enter an API Key.")
            else:
                genai.configure(api_key=api_key)
                
                # Save bytes immediately to session state so we don't lose them
                st.session_state.pdf_bytes = uploaded_file.getvalue()
                
                with st.spinner("🤖 Analyzing layout and extracting tables..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro') # 1.5 Pro is excellent for tables
                        
                        prompt = """
                        Extract all text from this PDF into clean Markdown.
                        CRITICAL INSTRUCTIONS FOR TABLES:
                        1. Detect all tables and represent them using standard Markdown table syntax.
                        2. Example format:
                        | Header 1 | Header 2 |
                        |---|---|
                        | Row 1 Col 1 | Row 1 Col 2 |
                        3. Ensure every row starts and ends with a pipe character (|).
                        4. Preserve all headers (#) and lists (*).
                        """

                        response = model.generate_content([
                            {'mime_type': 'application/pdf', 'data': st.session_state.pdf_bytes},
                            prompt
                        ])
                        
                        st.session_state.generated_content = response.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # 5. Editor / Split View
    else:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📄 Original File")
            if st.session_state.pdf_bytes:
                display_pdf(st.session_state.pdf_bytes)
            else:
                st.warning("PDF preview unavailable (Session Cleared)")

        with col2:
            st.subheader("📝 Editable Content")
            
            # The Text Area
            edited_text = st.text_area(
                "Edit Markdown (Tables appear as text here but convert to grids in Word):", 
                value=st.session_state.generated_content, 
                height=800
            )
            st.session_state.generated_content = edited_text
            
            st.divider()
            
            # Download Logic
            docx_data = generate_docx(st.session_state.generated_content)
            
            st.download_button(
                label="⬇️ Download as Word Doc", 
                data=docx_data, 
                file_name="converted_tables.docx", 
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
            
            if st.button("🔄 Start New File", use_container_width=True):
                st.session_state.generated_content = ""
                st.session_state.pdf_bytes = None
                st.rerun()

if __name__ == "__main__":
    main()
