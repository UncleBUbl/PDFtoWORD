import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO
import base64

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DocuGenius Pro (Gemini 3)", page_icon="⚡")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    
    /* Monospace font for editor so tables align visually */
    .stTextArea textarea { 
        font-family: 'Courier New', monospace; 
        font-size: 14px; 
        line-height: 1.5;
    }
    
    .main-header { 
        font-size: 2.5rem; 
        font-weight: 800; 
        color: #1a73e8; 
        text-align: center; 
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER: Display PDF ---
def display_pdf(pdf_bytes):
    """Displays PDF using <embed> to prevent losing it on refresh."""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- HELPER: Advanced Markdown Tables to Docx ---
def create_table_from_markdown(doc, table_lines):
    """Parses Markdown table lines and builds a real Word table."""
    try:
        # Filter out separator lines (like |---|---|)
        rows = [row for row in table_lines if '---' not in row]
        if not rows: return

        # Calculate columns based on header
        header_cells = [c.strip() for c in rows[0].split('|') if c.strip() != '']
        num_cols = len(header_cells)
        
        # Create Table
        table = doc.add_table(rows=len(rows), cols=num_cols)
        table.style = 'Table Grid'
        
        for i, row_text in enumerate(rows):
            cells_text = [c.strip() for c in row_text.split('|') if c.strip() != '']
            for j, text in enumerate(cells_text):
                if j < num_cols:
                    table.cell(i, j).text = text
    except:
        # Fallback if parsing fails
        for line in table_lines:
            doc.add_paragraph(line)

def generate_docx(text_content):
    doc = Document()
    lines = text_content.split('\n')
    table_buffer = []
    
    for line in lines:
        stripped = line.strip()
        
        # Detect Table Rows
        if stripped.startswith('|') and stripped.endswith('|'):
            table_buffer.append(stripped)
        else:
            # Write buffered table if we just finished one
            if table_buffer:
                create_table_from_markdown(doc, table_buffer)
                table_buffer = [] 
            
            # Normal Text Processing
            if line.startswith('# '): doc.add_heading(line[2:], level=1)
            elif line.startswith('## '): doc.add_heading(line[2:], level=2)
            elif line.startswith('### '): doc.add_heading(line[2:], level=3)
            elif line.startswith('* ') or line.startswith('- '):
                doc.add_paragraph(line[2:], style='List Bullet')
            elif stripped:
                doc.add_paragraph(line)
    
    # Check for table at end of file
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
            
        st.info("Using Model: **Gemini 3 Pro Preview**")

    # 2. Header
    st.markdown('<div class="main-header">DocuGenius Pro (Gemini 3) 🚀</div>', unsafe_allow_html=True)

    # 3. Session State
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = ""
    if 'pdf_bytes' not in st.session_state:
        st.session_state.pdf_bytes = None

    # 4. Upload View
    if not st.session_state.generated_content:
        uploaded_file = st.file_uploader("Upload PDF (Tables supported)", type=['pdf'])
        
        if uploaded_file and st.button("🚀 Convert with Gemini 3", type="primary"):
            if not api_key:
                st.error("Please enter an API Key.")
            else:
                genai.configure(api_key=api_key)
                st.session_state.pdf_bytes = uploaded_file.getvalue()
                
                with st.spinner("Gemini 3 Pro is processing tables & text..."):
                    try:
                        # --- STRICTLY USING GEMINI 3 PRO PREVIEW ---
                        model = genai.GenerativeModel('gemini-3-pro-preview')
                        
                        prompt = """
                        You are a document conversion engine. Extract all content from this PDF.
                        
                        STRICT RULES:
                        1. Output clean Markdown.
                        2. TABLES: specific attention to tables. You MUST format them as Markdown tables.
                           Example:
                           | Header 1 | Header 2 |
                           |---|---|
                           | Data 1   | Data 2   |
                        3. Do not miss any rows.
                        4. Do not include conversational text like "Here is the output".
                        """

                        response = model.generate_content([
                            {'mime_type': 'application/pdf', 'data': st.session_state.pdf_bytes},
                            prompt
                        ])
                        
                        st.session_state.generated_content = response.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        if "404" in str(e):
                             st.warning("Gemini 3 Pro Preview not found. Check if your API key has access to 'gemini-3-pro-preview'.")

    # 5. Editor / Split View
    else:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📄 Original PDF")
            if st.session_state.pdf_bytes:
                display_pdf(st.session_state.pdf_bytes)

        with col2:
            st.subheader("📝 Editable Text (Markdown)")
            
            edited_text = st.text_area(
                "Edit content here:", 
                value=st.session_state.generated_content, 
                height=800
            )
            st.session_state.generated_content = edited_text
            
            st.divider()
            
            docx_data = generate_docx(st.session_state.generated_content)
            
            st.download_button(
                label="⬇️ Download Word Doc", 
                data=docx_data, 
                file_name="converted_gemini3.docx", 
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
