import streamlit as st
import pandas as pd
import tempfile
import os
from extrator_ofx import ExtratorOFX

def main():
    st.set_page_config(page_title="Extrator Bancario", page_icon="💰", layout="wide")
    
    st.title("💰 Extrator de Dados Bancarios OFX")
    st.markdown("**Faca upload de um arquivo OFX para extrair e visualizar dados bancarios**")
    
    # CSS personalizado para métricas
    st.markdown("""
    <style>
    /* Estilo para débitos - vermelho */
    .metric-debito {
        background-color: #ffe6e6;
        border-left: 4px solid #ff4b4b;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    
    .metric-debito .metric-label {
        color: #ff4b4b;
        font-weight: bold;
    }
    
    .metric-debito .metric-value {
        color: #ff4b4b;
        font-size: 1.2em;
        font-weight: bold;
    }
    
    /* Estilo para créditos - verde */
    .metric-credito {
        background-color: #e6ffe6;
        border-left: 4px solid #00cc44;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    
    .metric-credito .metric-label {
        color: #00cc44;
        font-weight: bold;
    }
    
    .metric-credito .metric-value {
        color: #00cc44;
        font-size: 1.2em;
        font-weight: bold;
    }
    
    /* Estilo para saldo negativo */
    .saldo-negativo {
        background-color: #fff2f2;
        border: 2px solid #ff4b4b;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    
    /* Estilo para saldo positivo */
    .saldo-positivo {
        background-color: #f2fff2;
        border: 2px solid #00cc44;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
                stats = extrator.obter_estatisticas_filtros()
            
            if transacoes:
                # Informações sobre filtros aplicados
                if stats['transacoes_filtradas'] > 0:
                    st.info(f"ℹ️ **{stats['transacoes_filtradas']} lançamentos informativos** foram filtrados e não aparecem nos cálculos (ex: 'Saldo Total Disponível Dia')")
                
                # Calcular valores
                creditos = [t for t in transacoes if t['Valor'] > 0]
                debitos = [t for t in transacoes if t['Valor'] < 0]
                total_creditos = sum(t['Valor'] for t in creditos)
                total_debitos = sum(t['Valor'] for t in debitos)
                saldo = total_creditos + total_debitos
                
                # Resumo com layout personalizado
                st.header("📊 Resumo do Extrato (Sem Lançamentos Informativos)")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Transacoes Validas", len(transacoes))
                
                with col2:
                    # Créditos com estilo personalizado
                    st.markdown(f"""
                    <div class="metric-credito">
                        <div class="metric-label">💰 Créditos</div>
                        <div class="metric-value">{len(creditos)} transações</div>
                        <div class="metric-value">↗️ R$ {total_creditos:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    # Débitos com estilo personalizado
                    valor_absoluto_debitos = abs(total_debitos)
                    st.markdown(f"""
                    <div class="metric-debito">
                        <div class="metric-label">💸 Débitos</div>
                        <div class="metric-value">{len(debitos)} transações</div>
                        <div class="metric-value">↘️ R$ {valor_absoluto_debitos:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    # Saldo com estilo condicional
                    if saldo >= 0:
                        st.markdown(f"""
                        <div class="saldo-positivo">
                            <h3 style="color: #00cc44; margin: 0;">💚 Saldo Positivo</h3>
                            <h2 style="color: #00cc44; margin: 5px 0;">R$ {saldo:,.2f}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="saldo-negativo">
                            <h3 style="color: #ff4b4b; margin: 0;">⚠️ Saldo Negativo</h3>
                            <h2 style="color: #ff4b4b; margin: 5px 0;">R$ {saldo:,.2f}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                
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
                
                # Gráficos corrigidos com cores personalizadas
                st.header("📈 Visualizacoes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Comparacao de Valores (Absolutos)")
                    
                    # Dados para gráfico corrigido
                    valor_absoluto_debitos = abs(total_debitos)
                    
                    # Criar gráfico HTML personalizado com cores
                    max_valor = max(total_creditos, valor_absoluto_debitos)
                    altura_credito = (total_creditos / max_valor) * 300
                    altura_debito = (valor_absoluto_debitos / max_valor) * 300
                    
                    st.markdown(f"""
                    <div style="display: flex; align-items: end; justify-content: space-around; height: 350px; margin: 20px 0;">
                        <div style="text-align: center;">
                            <div style="
                                width: 80px; 
                                height: {altura_credito}px; 
                                background-color: #00cc44; 
                                margin: 0 auto 10px auto;
                                border-radius: 5px 5px 0 0;
                                display: flex;
                                align-items: end;
                                justify-content: center;
                                color: white;
                                font-weight: bold;
                                padding-bottom: 10px;
                            ">
                                R$ {total_creditos:,.0f}
                            </div>
                            <div style="font-weight: bold; color: #00cc44;">💰 Créditos</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="
                                width: 80px; 
                                height: {altura_debito}px; 
                                background-color: #ff4b4b; 
                                margin: 0 auto 10px auto;
                                border-radius: 5px 5px 0 0;
                                display: flex;
                                align-items: end;
                                justify-content: center;
                                color: white;
                                font-weight: bold;
                                padding-bottom: 10px;
                            ">
                                R$ {valor_absoluto_debitos:,.0f}
                            </div>
                            <div style="font-weight: bold; color: #ff4b4b;">💸 Débitos</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Mostrar valores exatos
                    st.markdown(f"""
                    **Valores exatos:**
                    - 💰 Créditos: R$ {total_creditos:,.2f}
                    - 💸 Débitos: R$ {valor_absoluto_debitos:,.2f}
                    - **Diferença:** R$ {valor_absoluto_debitos - total_creditos:,.2f} a mais em débitos
                    """)
                
                with col2:
                    st.subheader("Quantidade de Transacoes")
                    
                    # Criar gráfico HTML personalizado para quantidades
                    max_qtd = max(len(creditos), len(debitos))
                    altura_qtd_credito = (len(creditos) / max_qtd) * 300
                    altura_qtd_debito = (len(debitos) / max_qtd) * 300
                    
                    st.markdown(f"""
                    <div style="display: flex; align-items: end; justify-content: space-around; height: 350px; margin: 20px 0;">
                        <div style="text-align: center;">
                            <div style="
                                width: 80px; 
                                height: {altura_qtd_credito}px; 
                                background-color: #00cc44; 
                                margin: 0 auto 10px auto;
                                border-radius: 5px 5px 0 0;
                                display: flex;
                                align-items: end;
                                justify-content: center;
                                color: white;
                                font-weight: bold;
                                padding-bottom: 10px;
                            ">
                                {len(creditos)}
                            </div>
                            <div style="font-weight: bold; color: #00cc44;">💰 Créditos</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="
                                width: 80px; 
                                height: {altura_qtd_debito}px; 
                                background-color: #ff4b4b; 
                                margin: 0 auto 10px auto;
                                border-radius: 5px 5px 0 0;
                                display: flex;
                                align-items: end;
                                justify-content: center;
                                color: white;
                                font-weight: bold;
                                padding-bottom: 10px;
                            ">
                                {len(debitos)}
                            </div>
                            <div style="font-weight: bold; color: #ff4b4b;">💸 Débitos</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Mostrar quantidades exatas
                    st.markdown(f"""
                    **Quantidades:**
                    - 💰 Créditos: {len(creditos)} transações
                    - 💸 Débitos: {len(debitos)} transações
                    - **Total:** {len(transacoes)} transações válidas
                    """)
                
                # Gráfico de linha das transações por data
                st.subheader("Transacoes por Data")
                df = pd.DataFrame(transacoes)
                df['Data_obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
                transacoes_por_data = df.groupby('Data_obj').size()
                st.line_chart(transacoes_por_data)
                
                # Tabela de transações válidas
                st.header("📋 Transacoes Validas")
                
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
        3. Visualize os dados extraidos
        4. Baixe os arquivos CSV organizados
        
        **Dica:** Exporte o extrato em formato OFX pelo internet banking do seu banco.
        """)

if __name__ == "__main__":
    main()
