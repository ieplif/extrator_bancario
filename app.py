import streamlit as st
import pandas as pd
import tempfile
import os
from extrator_ofx import ExtratorOFX
from categorizador_despesas import CategorizadorDespesas
from gerenciador_persistencia_unificado import GerenciadorPersistenciaUnificado
from categorizador_receitas_simples import CategorizadorReceitasSimples
from estilo_unificado import aplicar_estilo_pagina, card_categoria, metrica_customizada

LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo_humaniza.png")

def configurar_pagina():
    """Configurações gerais da página."""
    st.set_page_config(
        page_title="Humaniza - Gestão Financeira", 
        page_icon="🦋", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Aplicar estilo unificado
    aplicar_estilo_pagina(st)
    

def sidebar_navegacao():
    """Cria a navegação na sidebar."""

    # Logo da clínica na sidebar
    st.sidebar.image(LOGO_PATH, use_container_width=True)
    st.sidebar.markdown("---")

    # st.sidebar.title("🧭 Navegação")
    
    # Opções de navegação
    opcoes = {
        "📊 Dashboard": "dashboard",
        "🏷️ Despesas": "despesas",
        "💰 Receitas": "receitas",
        "📊 Resultado": "resultado"
    }
    
    # Seleção da página atual
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = "dashboard"
    
    # Criar botões de navegação
    for nome, chave in opcoes.items():
        if st.sidebar.button(nome, key=f"nav_{chave}", use_container_width=True):
            st.session_state.pagina_atual = chave
            st.rerun()
    
    st.sidebar.divider()
    
    return st.session_state.pagina_atual


def sidebar_informacoes():
    """Informações gerais na sidebar."""
    st.sidebar.header("ℹ️ Informações")
    st.sidebar.markdown("""
    **Dados extraídos:**
    - Data da transação
    - Descrição completa
    - Razão Social
    - CNPJ/CPF
    - Valor e tipo
    
    **Formatos aceitos:**
    - Arquivos .ofx
    """)

def criar_graficos_valores(total_creditos, total_debitos):
    """Cria gráficos de valores com cores personalizadas."""
    valor_absoluto_debitos = abs(total_debitos)
    
    # Criar gráfico HTML personalizado com cores
    max_valor = max(total_creditos, valor_absoluto_debitos)
    altura_credito = (total_creditos / max_valor) * 300 if max_valor > 0 else 0
    altura_debito = (valor_absoluto_debitos / max_valor) * 300 if max_valor > 0 else 0
    
    return f"""
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
    """

def pagina_dashboard():
    """Página principal - Dashboard com análise da extração."""

    st.title("📊 Dashboard - Análise de Extrato")
    st.markdown("**Faça upload de um arquivo OFX para análise completa dos dados bancários**")
    
    # Upload de arquivo
    uploaded_file = st.file_uploader("Escolha um arquivo OFX", type=['ofx'])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ofx') as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        try:
            with st.spinner('Processando arquivo OFX...'):
                # Extrair dados
                extrator = ExtratorOFX()
                transacoes = extrator.processar_arquivo(tmp_path)
                stats = extrator.obter_estatisticas_filtros()
            
            if transacoes:
                # Informações sobre filtros aplicados
                if stats['transacoes_filtradas'] > 0:
                    st.info(f"ℹ️ **{stats['transacoes_filtradas']} lançamentos informativos** foram filtrados e não aparecem nos cálculos")
                
                # Calcular valores
                creditos = [t for t in transacoes if t['Valor'] > 0]
                debitos = [t for t in transacoes if t['Valor'] < 0]
                total_creditos = sum(t['Valor'] for t in creditos)
                total_debitos = sum(t['Valor'] for t in debitos)
                saldo = total_creditos + total_debitos
                
                # Resumo com layout personalizado
                st.header("📊 Resumo do Extrato")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Transações Válidas", len(transacoes))
                
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
                
                # Gráficos
                st.header("📈 Visualizações")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Comparação de Valores (Absolutos)")
                    
                    # Gráfico HTML personalizado
                    grafico_html = criar_graficos_valores(total_creditos, total_debitos)
                    st.markdown(grafico_html, unsafe_allow_html=True)
                    
                    # Mostrar valores exatos
                    valor_absoluto_debitos = abs(total_debitos)
                    diferenca = total_creditos - valor_absoluto_debitos

                    if diferenca > 0:
                        st.markdown(f"""
                        **Valores exatos:**
                        - 💰 Créditos: R$ {total_creditos:,.2f}
                        - 💸 Débitos: R$ {valor_absoluto_debitos:,.2f}
                        - **Diferença:** R$ {diferenca:,.2f} a mais em créditos
                        """)
                    elif diferenca < 0:
                        st.markdown(f"""
                        **Valores exatos:**
                        - 💰 Créditos: R$ {total_creditos:,.2f}
                        - 💸 Débitos: R$ {valor_absoluto_debitos:,.2f}
                        - **Diferença:** R$ {abs(diferenca):,.2f} a mais em débitos
                        """)
                    else:
                        st.markdown(f"""
                        **Valores exatos:**
                        - 💰 Créditos: R$ {total_creditos:,.2f}
                        - 💸 Débitos: R$ {valor_absoluto_debitos:,.2f}
                        - **Diferença:** Créditos e débitos equilibrados
                        """)
                
                with col2:
                    st.subheader("Transações por Data")
                    df = pd.DataFrame(transacoes)
                    df['Data_obj'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
                    transacoes_por_data = df.groupby('Data_obj').size()
                    st.line_chart(transacoes_por_data)
                
                # Análise adicional
                st.header("📊 Análise Detalhada")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Maiores Créditos")
                    if creditos:
                        maiores_creditos = df[df['Valor'] > 0].nlargest(5, 'Valor')[['Data', 'Razao Social', 'Valor']]
                        maiores_creditos['Valor'] = maiores_creditos['Valor'].apply(lambda x: f"R$ {x:,.2f}")
                        st.dataframe(maiores_creditos, hide_index=True)
                    else:
                        st.info("Nenhum crédito encontrado.")
                
                with col2:
                    st.subheader("Maiores Débitos")
                    if debitos:
                        maiores_debitos = df[df['Valor'] < 0].nsmallest(5, 'Valor')[['Data', 'Razao Social', 'Valor']]
                        maiores_debitos['Valor'] = maiores_debitos['Valor'].apply(lambda x: f"R$ {x:,.2f}")
                        st.dataframe(maiores_debitos, hide_index=True)
                    else:
                        st.info("Nenhum débito encontrado.")
                
                # Tabela de transações válidas
                st.header("📋 Todas as Transações Válidas")
                
                # Filtros
                col1, col2 = st.columns(2)
                
                with col1:
                    tipo_filtro = st.selectbox("Filtrar por tipo:", ["Todos", "Credito", "Debito"])
                
                with col2:
                    valor_min = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=10.0)
                
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
                        label="📥 Baixar Transações Válidas (CSV)",
                        data=csv_data,
                        file_name=f"extrato_valido_{uploaded_file.name.replace('.ofx', '')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Botões para categorização
                    col2a, col2b = st.columns(2)
                    
                    with col2a:
                        if st.button("🏷️ Ir para Despesas", type="primary"):
                            # Salvar dados na sessão para usar na página de despesas
                            st.session_state.transacoes_processadas = transacoes
                            st.session_state.arquivo_origem = uploaded_file.name
                            st.session_state.pagina_atual = "despesas"
                            st.rerun()
                    
                    with col2b:
                        if st.button("💰 Ir para Receitas", type="primary"):
                            # Salvar dados na sessão para usar na página de receitas
                            st.session_state.transacoes_processadas = transacoes
                            st.session_state.arquivo_origem = uploaded_file.name
                            st.session_state.pagina_atual = "receitas"
                            st.rerun()
                
                # Mostrar lançamentos filtrados em expander
                if stats['transacoes_filtradas'] > 0:
                    with st.expander(f"🔍 Ver {stats['transacoes_filtradas']} lançamentos filtrados"):
                        st.markdown("**Estes lançamentos foram removidos dos cálculos por serem informativos:**")
                        
                        filtrados_df = pd.DataFrame([
                            {
                                'Descrição': item['memo'],
                                'Valor': f"R$ {item['valor']:,.2f}",
                                'Motivo': item['motivo']
                            }
                            for item in stats['detalhes_filtradas']
                        ])
                        
                        st.dataframe(filtrados_df, use_container_width=True, hide_index=True)
                
            else:
                st.error("Nenhuma transação válida encontrada no arquivo OFX.")
                st.info("Verifique se o arquivo está no formato OFX correto.")
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
            st.info("Tente novamente com um arquivo OFX válido.")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    else:
        st.info("""
        👆 **Como usar o Dashboard:**
        
        1. Faça upload de um arquivo OFX do seu banco
        2. Aguarde o processamento automático  
        3. Visualize a análise completa dos dados
        4. Use os filtros para explorar as transações
        5. Baixe os arquivos CSV ou vá para Despesas para categorização
        
        **Dica:** Exporte o extrato em formato OFX pelo internet banking do seu banco.
        """)



def main():
    """Função principal da aplicação."""
    configurar_pagina()
    
    # Navegação na sidebar
    pagina_atual = sidebar_navegacao()
    
    # Informações na sidebar
    sidebar_informacoes()
    
    # Renderizar página atual
    if pagina_atual == "dashboard":
        pagina_dashboard()
    elif pagina_atual == "despesas":
        from pagina_despesas import pagina_despesas
        pagina_despesas()
    elif pagina_atual == "receitas":
        from pagina_receitas_simples import pagina_receitas
        pagina_receitas()
    elif pagina_atual == "resultado":
        from pagina_resultado import pagina_resultado
        pagina_resultado()

if __name__ == "__main__":
    main()
