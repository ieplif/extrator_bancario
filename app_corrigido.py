import streamlit as st
import pandas as pd
import tempfile
import os
from extrator_ofx_corrigido import ExtratorOFX

def main():
    st.set_page_config(page_title="Extrator Bancario", page_icon="💰", layout="wide")
    
    st.title("💰 Extrator de Dados Bancarios OFX")
    st.markdown("**Faca upload de um arquivo OFX para extrair e visualizar dados bancarios**")
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Informacoes")
        st.markdown("""
        **Dados extraidos:**
        - Data da transacao
        - Descricao completa
        - Razao Social
        - CNPJ/CPF
        - Valor e tipo
        
        **Formatos aceitos:**
        - Arquivos .ofx
        """)
    
    uploaded_file = st.file_uploader("Escolha um arquivo OFX", type=['ofx'])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ofx') as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        try:
            with st.spinner('Processando arquivo OFX...'):
                extrator = ExtratorOFX()
                transacoes = extrator.processar_arquivo(tmp_path)
            
            if transacoes:
                # Resumo
                st.header("📊 Resumo do Extrato")
                
                col1, col2, col3, col4 = st.columns(4)
                
                creditos = [t for t in transacoes if t['Valor'] > 0]
                debitos = [t for t in transacoes if t['Valor'] < 0]
                total_creditos = sum(t['Valor'] for t in creditos)
                total_debitos = sum(t['Valor'] for t in debitos)
                
                with col1:
                    st.metric("Total Transacoes", len(transacoes))
                
                with col2:
                    st.metric("Creditos", len(creditos), f"R$ {total_creditos:,.2f}")
                
                with col3:
                    st.metric("Debitos", len(debitos), f"R$ {total_debitos:,.2f}")
                
                with col4:
                    saldo = total_creditos + total_debitos
                    st.metric("Saldo Liquido", f"R$ {saldo:,.2f}")
                
                # Tabela de transações
                st.header("📋 Transacoes Extraidas")
                
                df = pd.DataFrame(transacoes)
                
                # Filtros
                col1, col2 = st.columns(2)
                
                with col1:
                    tipo_filtro = st.selectbox("Filtrar por tipo:", ["Todos", "Credito", "Debito"])
                
                with col2:
                    valor_min = st.number_input("Valor minimo (R$):", min_value=0.0, value=0.0, step=10.0)
                
                # Aplicar filtros
                df_filtrado = df.copy()
                
                if tipo_filtro != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_filtro]
                
                if valor_min > 0:
                    df_filtrado = df_filtrado[abs(df_filtrado['Valor']) >= valor_min]
                
                # Formatar valores para exibição
                df_display = df_filtrado.copy()
                df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Download
                st.header("💾 Download")
                
                csv_data = df.to_csv(index=False, encoding='utf-8')
                
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv_data,
                    file_name=f"extrato_{uploaded_file.name.replace('.ofx', '')}.csv",
                    mime="text/csv"
                )
                
                # Gráficos
                st.header("📈 Visualizacoes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Creditos vs Debitos")
                    chart_data = pd.DataFrame({
                        'Tipo': ['Creditos', 'Debitos'],
                        'Quantidade': [len(creditos), len(debitos)]
                    })
                    st.bar_chart(chart_data.set_index('Tipo'))
                
                with col2:
                    st.subheader("Transacoes por Data")
                    df['Data_obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
                    transacoes_por_data = df.groupby('Data_obj').size()
                    st.line_chart(transacoes_por_data)
                
            else:
                st.error("Nenhuma transacao encontrada no arquivo OFX.")
                st.info("Verifique se o arquivo esta no formato OFX correto.")
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
            st.info("Tente novamente com um arquivo OFX valido.")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    else:
        st.info("""
        👆 **Como usar:**
        
        1. Faca upload de um arquivo OFX do seu banco
        2. Aguarde o processamento automatico  
        3. Visualize os dados extraidos
        4. Baixe o arquivo CSV organizado
        
        **Dica:** Exporte o extrato em formato OFX pelo internet banking do seu banco.
        """)

if __name__ == "__main__":
    main()
