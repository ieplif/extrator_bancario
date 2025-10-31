"""
Utilitários para carregamento de CSS no Streamlit
"""

import streamlit as st
import os

def carregar_css():
    """
    Carrega o arquivo CSS centralizado e injeta no Streamlit.
    Aplica dark mode se ativado.
    
    Returns:
        None
    """
    # Caminho do arquivo CSS
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    
    # Ler conteúdo do CSS
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Verificar se dark mode está ativo
        if st.session_state.get('dark_mode', False):
            # Adicionar CSS dark mode diretamente
            css_dark = """
            /* Dark Mode Ativo */
            .stApp {
                background-color: #2C3531 !important;
            }
            [data-testid="stSidebar"] {
                background-color: #3E4A47 !important;
            }
            .stApp h1, .stApp h2, .stApp h3 {
                color: #E8EBE8 !important;
            }
            .card-despesa, .card-receita {
                background-color: #3E4A47 !important;
                border-left-color: #9BAA9D !important;
            }
            .card-despesa h4, .card-receita h4 {
                color: #9BAA9D !important;
            }
            .card-despesa p, .card-receita p,
            .card-despesa strong, .card-receita strong {
                color: #E8EBE8 !important;
            }
            div[data-testid="stMetricValue"] {
                color: #9BAA9D !important;
            }
            div[data-testid="stMetricLabel"] {
                color: #B8C5BA !important;
            }
            """
            css_content += css_dark
        
        # Injetar CSS no Streamlit
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.warning("⚠️ Arquivo styles.css não encontrado. Usando estilos padrão.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar CSS: {str(e)}")

def aplicar_dark_mode():
    """
    Função descontinuada - dark mode agora é aplicado em carregar_css().
    Mantida para compatibilidade.
    """
    pass

