import streamlit as st
import fitz # PyMuPDF

st.set_page_config(layout="wide")
st.title("Extrator de Dados de Extrato Bancário")
st.write("Faça o upload do seu extrato bancário em PDF para iniciar a extração.")

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type=["pdf"])

if uploaded_file is not None:
    st.success("Arquivo PDF carregado com sucesso!")
    st.write("Nome do arquivo:", uploaded_file.name)
    st.write("Tamanho do arquivo:", uploaded_file.size, "bytes")

    # Extraindo texto do PDF
    extracted_text = extract_text_from_pdf(uploaded_file)
    st.subheader("Texto Extraído do PDF")
    st.text_area("", extracted_text, height=300)