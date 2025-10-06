import streamlit as st
import pandas as pd
import tempfile
import os
from extrator_ofx import ExtratorOFX
from categorizador_despesas import CategorizadorDespesas
from gerenciador_persistencia_unificado import GerenciadorPersistenciaUnificado
from categorizador_receitas_simples import CategorizadorReceitasSimples

def configurar_pagina():
    """Configurações gerais da página."""
    st.set_page_config(
        page_title="Extrator Bancario", 
        page_icon="💰", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado
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
    
    /* Estilo para categorias */
    .categoria-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Estilo para navegação */
    .nav-link {
        display: block;
        padding: 10px 15px;
        margin: 5px 0;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        text-decoration: none;
        color: #333;
        font-weight: bold;
    }
    
    .nav-link:hover {
        background-color: #e9ecef;
    }
    
    .nav-link.active {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

def sidebar_navegacao():
    """Cria a navegação na sidebar."""
    st.sidebar.title("🧭 Navegação")
    
    # Opções de navegação
    opcoes = {
        "📊 Dashboard": "dashboard",
        "🏷️ Despesas": "despesas",
        "💰 Receitas": "receitas"
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
                    st.markdown(f"""
                    **Valores exatos:**
                    - 💰 Créditos: R$ {total_creditos:,.2f}
                    - 💸 Débitos: R$ {valor_absoluto_debitos:,.2f}
                    - **Diferença:** R$ {valor_absoluto_debitos - total_creditos:,.2f} a mais em débitos
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

def pagina_despesas():
    """Página de Despesas - Categorização e gestão."""
    st.title("🏷️ Gestão de Despesas")
    st.markdown("**Categorização automática e gestão de despesas persistentes**")
    
    # Inicializar gerenciador
    gerenciador = GerenciadorPersistenciaUnificado()
    
    # Verificar se há transações processadas na sessão
    if 'transacoes_processadas' in st.session_state:
        st.success("✅ Dados carregados do Dashboard. Processe a categorização abaixo.")
        
        transacoes = st.session_state.transacoes_processadas
        arquivo_origem = st.session_state.get('arquivo_origem', 'sessao')
        
        # Categorizar despesas
        categorizador = CategorizadorDespesas()
        despesas_categorizadas = categorizador.processar_debitos(transacoes)
        
        if not despesas_categorizadas.empty:
            # Seção de Categorização
            st.header("🏷️ Despesas Categorizadas")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Resumo por Categoria")
                
                # Resumo das categorias
                resumo_cat = despesas_categorizadas.groupby('Descricao')['Valor'].agg(['sum', 'count']).round(2)
                resumo_cat.columns = ['Total (R$)', 'Quantidade']
                resumo_cat = resumo_cat.sort_values('Total (R$)', ascending=False)
                
                # Mostrar como cards
                for categoria, dados in resumo_cat.iterrows():
                    st.markdown(f"""
                    <div class="categoria-card">
                        <h4 style="margin: 0; color: #333;">{categoria}</h4>
                        <p style="margin: 5px 0; font-size: 1.1em;">
                            <strong>R$ {dados['Total (R$)']:,.2f}</strong> 
                            ({int(dados['Quantidade'])} transações)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.subheader("Ações")
                
                # Opções de salvamento
                modo_salvamento = st.radio(
                    "Como salvar as despesas?",
                    ["Adicionar às existentes", "Sobrescrever dados salvos"],
                    help="Adicionar: mantém despesas anteriores. Sobrescrever: remove todas as anteriores."
                )
                
                if st.button("💾 Salvar Despesas Categorizadas", type="primary"):
                    modo = 'adicionar' if modo_salvamento == "Adicionar às existentes" else 'sobrescrever'
                    
                    resultado = gerenciador.salvar_despesas(
                        despesas_categorizadas, 
                        arquivo_origem, 
                        modo
                    )
                    
                    if resultado['sucesso']:
                        # Obter resumo atualizado para mostrar período
                        resumo_atualizado = gerenciador.obter_resumo_despesas()
                        periodo_atualizado = resumo_atualizado.get('periodo', {})
                        
                        periodo_texto = ""
                        if periodo_atualizado:
                            inicio = periodo_atualizado.get('inicio', 'N/A')
                            fim = periodo_atualizado.get('fim', 'N/A')
                            if inicio == fim:
                                periodo_texto = f"📅 **Período atualizado:** {inicio}"
                            else:
                                periodo_texto = f"📅 **Período atualizado:** {inicio} a {fim}"
                        
                        st.success(f"""
                        ✅ **Despesas salvas com sucesso!**
                        
                        - **Novas despesas:** {resultado['novas_despesas']}
                        - **Total de despesas:** {resultado['total_despesas']}
                        - **Modo:** {resultado['modo']}
                        
                        {periodo_texto}
                        """)
                        
                        # Limpar dados da sessão
                        if 'transacoes_processadas' in st.session_state:
                            del st.session_state.transacoes_processadas
                        if 'arquivo_origem' in st.session_state:
                            del st.session_state.arquivo_origem
                        
                        # Forçar atualização da página para mostrar dados atualizados
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao salvar: {resultado['erro']}")
                
                # Download das despesas categorizadas
                csv_categorizadas = despesas_categorizadas.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Baixar Categorizadas (CSV)",
                    data=csv_categorizadas,
                    file_name=f"despesas_categorizadas_{arquivo_origem.replace('.ofx', '')}.csv",
                    mime="text/csv"
                )
                
                # Botão para limpar dados da sessão
                if st.button("🗑️ Limpar Dados da Sessão"):
                    if 'transacoes_processadas' in st.session_state:
                        del st.session_state.transacoes_processadas
                    if 'arquivo_origem' in st.session_state:
                        del st.session_state.arquivo_origem
                    st.rerun()
            
            # Gráfico de categorias
            st.subheader("📊 Gráfico por Categoria")
            
            # Criar gráfico de barras para categorias
            max_cat_valor = resumo_cat['Total (R$)'].max()
            
            st.markdown("<div style='margin: 20px 0;'>", unsafe_allow_html=True)
            
            for categoria, dados in resumo_cat.iterrows():
                altura_cat = (dados['Total (R$)'] / max_cat_valor) * 200
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin: 10px 0;">
                    <div style="width: 120px; text-align: right; padding-right: 10px; font-weight: bold; font-size: 0.9em;">
                        {categoria}:
                    </div>
                    <div style="
                        width: {altura_cat}px; 
                        height: 25px; 
                        background-color: #ff4b4b; 
                        border-radius: 3px;
                        display: flex;
                        align-items: center;
                        justify-content: end;
                        color: white;
                        font-weight: bold;
                        font-size: 0.8em;
                        padding-right: 5px;
                        min-width: 80px;
                    ">
                        R$ {dados['Total (R$)']:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Tabela detalhada das despesas categorizadas
            st.subheader("📋 Detalhes das Despesas Categorizadas")
            
            # Filtros
            col1, col2 = st.columns(2)
            
            with col1:
                categorias_disponiveis = ['Todas'] + list(despesas_categorizadas['Descricao'].unique())
                categoria_filtro = st.selectbox("Filtrar por categoria:", categorias_disponiveis)
            
            with col2:
                valor_min = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=10.0)
            
            # Aplicar filtros
            despesas_filtradas = despesas_categorizadas.copy()
            
            if categoria_filtro != 'Todas':
                despesas_filtradas = despesas_filtradas[despesas_filtradas['Descricao'] == categoria_filtro]
            
            if valor_min > 0:
                despesas_filtradas = despesas_filtradas[despesas_filtradas['Valor'] >= valor_min]
            
            # Formatar valores para exibição
            despesas_display = despesas_filtradas.copy()
            despesas_display['Valor'] = despesas_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(
                despesas_display[['Data', 'Descricao', 'Valor', 'Razao_Social_Original']], 
                use_container_width=True, 
                hide_index=True
            )
        
        else:
            st.info("Nenhuma despesa (débito) encontrada nos dados processados.")
    
    # Seção de Despesas Salvas
    st.header("💾 Despesas Salvas")
    
    despesas_salvas = gerenciador.carregar_despesas()
    
    if not despesas_salvas.empty:
        resumo = gerenciador.obter_resumo_despesas()
        
        # Métricas das despesas salvas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Despesas", resumo['total_despesas'])
        
        with col2:
            st.metric("Valor Total", f"R$ {resumo['valor_total']:,.2f}")
        
        with col3:
            periodo = resumo.get('periodo', {})
            if periodo:
                st.metric("Período", f"{periodo.get('inicio', 'N/A')} a {periodo.get('fim', 'N/A')}")
        
        # Resumo por categoria
        st.subheader("📊 Resumo por Categoria (Dados Salvos)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            for categoria, dados in resumo['por_categoria'].items():
                # Converter valores numpy para float para formatação
                total = float(dados['total'])
                quantidade = int(dados['quantidade'])
                media = float(dados['media'])
                
                st.markdown(f"""
                <div class="categoria-card">
                    <h4 style="margin: 0; color: #333;">{categoria}</h4>
                    <p style="margin: 5px 0; font-size: 1.1em;">
                        <strong>R$ {total:,.2f}</strong> 
                        ({quantidade} transações)
                    </p>
                    <small>Média: R$ {media:,.2f}</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Filtros para despesas salvas
            st.subheader("🔍 Filtrar Despesas Salvas")
            
            # Preparar dados de data
            despesas_salvas['Data_dt'] = pd.to_datetime(despesas_salvas['Data'], format='%d/%m/%Y')
            despesas_salvas['Mes_Ano'] = despesas_salvas['Data_dt'].dt.strftime('%m/%Y')
            despesas_salvas['Mes_Nome'] = despesas_salvas['Data_dt'].dt.strftime('%B/%Y')
            
            # Filtro por categoria
            categorias_unicas = ['Todas'] + list(despesas_salvas['Descricao'].unique())
            categoria_filtro_salvas = st.selectbox("Categoria:", categorias_unicas)
            
            # Filtro por mês
            meses_unicos = ['Todos'] + sorted(list(despesas_salvas['Mes_Ano'].unique()), reverse=True)
            mes_filtro = st.selectbox("Mês:", meses_unicos, key="mes_filtro")
            
            # Filtro por período personalizado
            col_data1, col_data2 = st.columns(2)
            with col_data1:
                data_inicio = st.date_input("Data início:", value=None, key="data_inicio_salvas")
            with col_data2:
                data_fim = st.date_input("Data fim:", value=None, key="data_fim_salvas")
            
            # Filtro por valor
            valor_min_salvas = st.number_input("Valor mínimo:", min_value=0.0, value=0.0, key="valor_min_salvas")
            
            # Aplicar filtros
            despesas_filtradas_salvas = despesas_salvas.copy()
            
            # Filtro por categoria
            if categoria_filtro_salvas != 'Todas':
                despesas_filtradas_salvas = despesas_filtradas_salvas[despesas_filtradas_salvas['Descricao'] == categoria_filtro_salvas]
            
            # Filtro por mês
            if mes_filtro != 'Todos':
                despesas_filtradas_salvas = despesas_filtradas_salvas[despesas_filtradas_salvas['Mes_Ano'] == mes_filtro]
            
            # Filtro por período personalizado
            if data_inicio is not None:
                despesas_filtradas_salvas = despesas_filtradas_salvas[despesas_filtradas_salvas['Data_dt'] >= pd.to_datetime(data_inicio)]
            
            if data_fim is not None:
                despesas_filtradas_salvas = despesas_filtradas_salvas[despesas_filtradas_salvas['Data_dt'] <= pd.to_datetime(data_fim)]
            
            # Filtro por valor
            if valor_min_salvas > 0:
                despesas_filtradas_salvas = despesas_filtradas_salvas[despesas_filtradas_salvas['Valor'] >= valor_min_salvas]
            
            # Download das despesas salvas
            csv_despesas_salvas = despesas_filtradas_salvas.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="📥 Baixar Despesas Filtradas (CSV)",
                data=csv_despesas_salvas,
                file_name=f"despesas_salvas_{categoria_filtro_salvas.lower()}.csv",
                mime="text/csv"
            )
        
        # Análise temporal por mês
        if len(despesas_filtradas_salvas) > 0:
            st.subheader("📅 Análise Temporal por Mês")
            
            # Preparar dados mensais
            analise_mensal = despesas_filtradas_salvas.groupby(['Mes_Ano', 'Descricao'])['Valor'].sum().reset_index()
            analise_mensal_total = despesas_filtradas_salvas.groupby('Mes_Ano')['Valor'].agg(['sum', 'count']).reset_index()
            analise_mensal_total.columns = ['Mes_Ano', 'Total', 'Quantidade']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**💰 Total por Mês:**")
                for _, row in analise_mensal_total.iterrows():
                    st.markdown(f"""
                    <div class="categoria-card">
                        <h4 style="margin: 0; color: #333;">📅 {row['Mes_Ano']}</h4>
                        <p style="margin: 5px 0; font-size: 1.1em;">
                            <strong>R$ {row['Total']:,.2f}</strong> 
                            ({int(row['Quantidade'])} transações)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.write("**📊 Gráfico Temporal:**")
                
                # Criar gráfico de linha temporal
                if len(analise_mensal_total) > 1:
                    # Ordenar por data
                    analise_mensal_total['Data_Sort'] = pd.to_datetime(analise_mensal_total['Mes_Ano'], format='%m/%Y')
                    analise_mensal_total = analise_mensal_total.sort_values('Data_Sort')
                    
                    # Gráfico de linha
                    st.line_chart(analise_mensal_total.set_index('Mes_Ano')['Total'])
                else:
                    st.info("Adicione mais dados para visualizar tendências temporais.")
            
            # Análise detalhada por categoria e mês
            if mes_filtro != 'Todos':
                st.subheader(f"📊 Detalhamento do Mês {mes_filtro}")
                
                despesas_mes = despesas_filtradas_salvas[despesas_filtradas_salvas['Mes_Ano'] == mes_filtro]
                resumo_mes = despesas_mes.groupby('Descricao')['Valor'].agg(['sum', 'count', 'mean']).round(2)
                resumo_mes.columns = ['Total', 'Quantidade', 'Média']
                resumo_mes = resumo_mes.sort_values('Total', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📋 Resumo por Categoria:**")
                    st.dataframe(resumo_mes, use_container_width=True)
                
                with col2:
                    st.write("**📈 Gráfico do Mês:**")
                    
                    # Gráfico de barras horizontais para o mês
                    max_valor_mes = resumo_mes['Total'].max()
                    
                    for categoria, dados in resumo_mes.iterrows():
                        largura = (dados['Total'] / max_valor_mes) * 300
                        
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; margin: 8px 0;">
                            <div style="width: 100px; text-align: right; padding-right: 8px; font-size: 0.8em; font-weight: bold;">
                                {categoria}:
                            </div>
                            <div style="
                                width: {largura}px; 
                                height: 20px; 
                                background-color: #ff4b4b; 
                                border-radius: 3px;
                                display: flex;
                                align-items: center;
                                justify-content: end;
                                color: white;
                                font-weight: bold;
                                font-size: 0.7em;
                                padding-right: 5px;
                                min-width: 60px;
                            ">
                                R$ {dados['Total']:,.0f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Mostrar tabela das despesas salvas
        st.subheader("📋 Despesas Filtradas")
        
        # Mostrar informações do filtro aplicado
        info_filtro = []
        if categoria_filtro_salvas != 'Todas':
            info_filtro.append(f"Categoria: {categoria_filtro_salvas}")
        if mes_filtro != 'Todos':
            info_filtro.append(f"Mês: {mes_filtro}")
        if data_inicio is not None:
            info_filtro.append(f"A partir de: {data_inicio.strftime('%d/%m/%Y')}")
        if data_fim is not None:
            info_filtro.append(f"Até: {data_fim.strftime('%d/%m/%Y')}")
        if valor_min_salvas > 0:
            info_filtro.append(f"Valor mín: R$ {valor_min_salvas:,.2f}")
        
        if info_filtro:
            st.info(f"**Filtros aplicados:** {' | '.join(info_filtro)}")
        
        # Mostrar métricas das despesas filtradas
        if len(despesas_filtradas_salvas) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Despesas Filtradas", len(despesas_filtradas_salvas))
            
            with col2:
                total_filtrado = despesas_filtradas_salvas['Valor'].sum()
                st.metric("Total Filtrado", f"R$ {total_filtrado:,.2f}")
            
            with col3:
                media_filtrada = despesas_filtradas_salvas['Valor'].mean()
                st.metric("Média", f"R$ {media_filtrada:,.2f}")
        
        st.dataframe(
            despesas_filtradas_salvas[['Data', 'Descricao', 'Valor', 'Razao_Social_Original', 'Arquivo_Origem']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Opções de gestão
        st.subheader("🛠️ Gestão de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📦 Fazer Backup"):
                resultado_backup = gerenciador.fazer_backup()
                if resultado_backup['sucesso']:
                    st.success(f"✅ Backup criado: {resultado_backup['timestamp']}")
                else:
                    st.error(f"❌ Erro no backup: {resultado_backup['erro']}")
        
        with col2:
            if st.button("🗑️ Limpar Todos os Dados"):
                if st.checkbox("Confirmar limpeza (irreversível)", key="confirmar_limpeza"):
                    resultado = gerenciador.limpar_dados(confirmar=True)
                    if resultado['sucesso']:
                        st.success("✅ Dados limpos com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {resultado['erro']}")
    
    else:
        st.info("""
        📝 **Nenhuma despesa salva ainda.**
        
        Para começar:
        1. Vá para o **Dashboard**
        2. Faça upload de um arquivo OFX
        3. Clique em "Ir para Categorização de Despesas"
        4. Salve as despesas categorizadas
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

if __name__ == "__main__":
    main()
