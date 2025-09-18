import streamlit as st

st.set_page_config(layout="wide")
st.title("Extrator de Dados de Extrato Bancário")
st.write("Faça o upload do seu extrato bancário em PDF para iniciar a extração.")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type=["pdf"])

if uploaded_file is not None:
    st.success("Arquivo PDF carregado com sucesso!")
    # Futuramente, aqui será a lógica de extração
    st.write("Nome do arquivo:", uploaded_file.name)
    st.write("Tamanho do arquivo:", uploaded_file.size, "bytes")