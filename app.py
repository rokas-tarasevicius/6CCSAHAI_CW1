import streamlit as st

st.set_page_config(page_title="PDF Upload", page_icon="📄")

st.title("PDF Upload")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    st.write(f"File size: {uploaded_file.size} bytes")
    
    # Display file info
    with st.expander("File Details"):
        st.write(f"**Filename:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size:,} bytes")
        st.write(f"**Type:** {uploaded_file.type}")

