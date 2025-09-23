import streamlit as st
import pandas as pd
import tempfile
import os
from extrator_ofx_filtrado import ExtratorOFX

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
        
        **Filtros aplicados:**
        - Remove "Saldo Total Disponivel"
        - Remove "Saldo Anterior"
        - Remove outros lancamentos informativos
        
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
                stats = extrator.obter_estatisticas_filtros()
            
            if transacoes:
                # Informações sobre filtros aplicados
                if stats['transacoes_filtradas'] > 0:
                    st.info(f"ℹ️ **{stats['transacoes_filtradas']} lançamentos informativos** foram filtrados e não aparecem nos cálculos (ex: 'Saldo Total Disponível Dia')")
                
                # Resumo
                st.header("📊 Resumo do Extrato (Sem Lançamentos Informativos)")
                
                col1, col2, col3, col4 = st.columns(4)
                
                creditos = [t for t in transacoes if t['Valor'] > 0]
                debitos = [t for t in transacoes if t['Valor'] < 0]
                total_creditos = sum(t['Valor'] for t in creditos)
                total_debitos = sum(t['Valor'] for t in debitos)
                
                with col1:
                    st.metric("Transacoes Validas", len(transacoes))
                
                with col2:
                    st.metric("Creditos", len(creditos), f"R$ {total_creditos:,.2f}")
                
                with col3:
                    st.metric("Debitos", len(debitos), f"R$ {total_debitos:,.2f}")
                
                with col4:
                    saldo = total_creditos + total_debitos
                    delta_color = "normal" if saldo >= 0 else "inverse"
                    st.metric("Saldo Liquido", f"R$ {saldo:,.2f}")
                
                # Mostrar lançamentos filtrados em expander
                if stats['transacoes_filtradas'] > 0:
                    with st.expander(f"🔍 Ver {stats['transacoes_filtradas']} lançamentos filtrados"):
                        st.markdown("**Estes lançamentos foram removidos dos cálculos por serem informativos:**")
                        
                        filtrados_df = pd.DataFrame([
                            {
                                'Descricao': item['memo'],
                                'Valor': f"R$ {item['valor']:,.2f}",
                                'Motivo': item['motivo']
                            }
                            for item in stats['detalhes_filtradas']
                        ])
                        
                        st.dataframe(filtrados_df, use_container_width=True, hide_index=True)
                
                # Tabela de transações válidas
                st.header("📋 Transacoes Validas")
                
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
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # CSV das transações válidas
                    csv_data = df.to_csv(index=False, encoding='utf-8')
                    st.download_button(
                        label="📥 Baixar Transacoes Validas (CSV)",
                        data=csv_data,
                        file_name=f"extrato_valido_{uploaded_file.name.replace('.ofx', '')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # CSV dos lançamentos filtrados
                    if stats['transacoes_filtradas'] > 0:
                        filtrados_csv = filtrados_df.to_csv(index=False, encoding='utf-8')
                        st.download_button(
                            label="📥 Baixar Lancamentos Filtrados (CSV)",
                            data=filtrados_csv,
                            file_name=f"lancamentos_filtrados_{uploaded_file.name.replace('.ofx', '')}.csv",
                            mime="text/csv"
                        )
                
                # Gráficos
                st.header("📈 Visualizacoes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Creditos vs Debitos")
                    chart_data = pd.DataFrame({
                        'Tipo': ['Creditos', 'Debitos'],
                        'Quantidade': [len(creditos), len(debitos)],
                        'Valor Total': [total_creditos, abs(total_debitos)]
                    })
                    st.bar_chart(chart_data.set_index('Tipo')['Quantidade'])
                
                with col2:
                    st.subheader("Transacoes por Data")
                    df['Data_obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
                    transacoes_por_data = df.groupby('Data_obj').size()
                    st.line_chart(transacoes_por_data)
                
                # Análise adicional
                st.header("📊 Analise Detalhada")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Maiores Creditos")
                    maiores_creditos = df[df['Valor'] > 0].nlargest(5, 'Valor')[['Data', 'Razao Social', 'Valor']]
                    maiores_creditos['Valor'] = maiores_creditos['Valor'].apply(lambda x: f"R$ {x:,.2f}")
                    st.dataframe(maiores_creditos, hide_index=True)
                
                with col2:
                    st.subheader("Maiores Debitos")
                    maiores_debitos = df[df['Valor'] < 0].nsmallest(5, 'Valor')[['Data', 'Razao Social', 'Valor']]
                    maiores_debitos['Valor'] = maiores_debitos['Valor'].apply(lambda x: f"R$ {x:,.2f}")
                    st.dataframe(maiores_debitos, hide_index=True)
                
            else:
                st.error("Nenhuma transacao valida encontrada no arquivo OFX.")
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
        3. Visualize os dados extraidos (sem lancamentos informativos)
        4. Baixe os arquivos CSV organizados
        
        **Novo:** O sistema agora filtra automaticamente lancamentos informativos como "Saldo Total Disponivel Dia" que nao representam movimentacoes reais.
        """)

if __name__ == "__main__":
    main()
