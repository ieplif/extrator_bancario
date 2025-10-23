import streamlit as st
import pandas as pd
from categorizador_despesas import CategorizadorDespesas
from gerenciador_persistencia_unificado import GerenciadorPersistenciaUnificado

def pagina_despesas():
    """Página de Despesas - Categorização automática e gestão persistente."""
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
            # Estatísticas da categorização
            total_debitos = len([t for t in transacoes if t['Valor'] < 0])
            retiradas = len(despesas_categorizadas[despesas_categorizadas['Descricao'] == 'Retirada'])
            valor_total = despesas_categorizadas['Valor'].sum()
            
            st.header("📊 Categorização Automática")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Débitos", total_debitos)
            
            with col2:
                st.metric("Retiradas", retiradas)
            
            with col3:
                st.metric("Categorizadas", len(despesas_categorizadas))
            
            with col4:
                st.metric("Valor Total", f"R$ {valor_total:,.2f}")
            
            # Resumo por categoria
            st.subheader("📋 Resumo por Categoria")
            
            resumo_categoria = despesas_categorizadas.groupby('Descricao').agg({
                'Valor': ['sum', 'count']
            }).round(2)
            
            for categoria in resumo_categoria.index:
                total = resumo_categoria.loc[categoria, ('Valor', 'sum')]
                quantidade = resumo_categoria.loc[categoria, ('Valor', 'count')]
            
                
                st.markdown(f"""
                <div style="background-color: #E9E5DC; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #BF6F4E;">
                    <h4 style="margin: 0; color: #BF6F4E;">{categoria}</h4>
                    <p style="margin: 5px 0;"><strong>R$ {total:,.2f}</strong> ({quantidade} transações)</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Tabela de despesas
            st.subheader("📋 Despesas Categorizadas")
            
            # Formatar valores para exibição
            df_display = despesas_categorizadas.copy()
            df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Opções de salvamento
            st.header("💾 Salvar Despesas")
            
            # Seleção de mês/ano
            from datetime import datetime
            col_mes, col_ano = st.columns(2)
            
            with col_mes:
                mes = st.selectbox(
                    "Mês",
                    options=list(range(1, 13)),
                    format_func=lambda x: f"{x:02d}",
                    index=datetime.now().month - 1,
                    key="mes_despesas"
                )
            
            with col_ano:
                ano = st.selectbox(
                    "Ano",
                    options=list(range(2020, 2030)),
                    index=list(range(2020, 2030)).index(datetime.now().year),
                    key="ano_despesas"
                )
            
            mes_ano = f"{mes:02d}/{ano}"
            st.info(f"📅 As despesas serão salvas para o mês: **{mes_ano}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("➕ Adicionar às Existentes", type="primary"):
                    resultado = gerenciador.salvar_despesas(despesas_categorizadas, arquivo_origem, modo='adicionar', mes_ano=mes_ano)
                    
                    if resultado['sucesso']:
                        st.success(f"✅ {resultado['novas_despesas']} despesas adicionadas! Total: {resultado['total_despesas']}")
                        # Limpar sessão e recarregar
                        if 'transacoes_processadas' in st.session_state:
                            del st.session_state.transacoes_processadas
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {resultado['erro']}")
            
            with col2:
                if st.button("🔄 Sobrescrever Dados Salvos"):
                    resultado = gerenciador.salvar_despesas(despesas_categorizadas, arquivo_origem, modo='sobrescrever', mes_ano=mes_ano)
                    
                    if resultado['sucesso']:
                        st.success(f"✅ Dados sobrescritos! Total: {resultado['total_despesas']} despesas")
                        # Limpar sessão e recarregar
                        if 'transacoes_processadas' in st.session_state:
                            del st.session_state.transacoes_processadas
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {resultado['erro']}")
            
            # Download
            csv_data = despesas_categorizadas.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv_data,
                file_name=f"despesas_{arquivo_origem.replace('.ofx', '')}.csv",
                mime="text/csv"
            )
        
        else:
            st.warning("⚠️ Nenhuma despesa encontrada nas transações processadas.")
    
    # Seção de despesas salvas (sempre visível)
    st.header("🏷️ Despesas Salvas")
    
    # Carregar despesas salvas
    despesas_salvas = gerenciador.carregar_despesas()
    
    if not despesas_salvas.empty:
        # Resumo geral
        resumo = gerenciador.obter_resumo_despesas()
        
        # Cards de resumo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Despesas", resumo['total_despesas'])
        
        with col2:
            st.metric("Valor Total", f"R$ {resumo['valor_total']:,.2f}")
        
        with col3:
            if resumo['periodo']:
                inicio = resumo['periodo']['inicio']
                fim = resumo['periodo']['fim']
                periodo_texto = inicio if inicio == fim else f"{inicio} a {fim}"
                st.metric("Período", periodo_texto)
        
        # Resumo por categoria (cards)
        st.subheader("📊 Resumo por Categoria (Dados Salvos)")
        
        for categoria, dados in resumo['por_categoria'].items():
            total = float(dados['total'])
            quantidade = int(dados['quantidade'])
            
            st.markdown(f"""
            <div style="background-color: #E9E5DC; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #BF6F4E;">
                <h4 style="margin: 0; color: #BF6F4E;">{categoria}</h4>
                <p style="margin: 5px 0; font-size: 1.1em;"><strong>R$ {total:,.2f}</strong> ({quantidade} transações)</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Filtros
        st.subheader("🔍 Filtrar Despesas Salvas")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            categorias_unicas = ['Todas'] + sorted(despesas_salvas['Descricao'].unique().tolist())
            categoria_filtro = st.selectbox("Categoria", categorias_unicas)
        
        with col2:
            # Converter datas para análise
            despesas_salvas['Data_dt'] = pd.to_datetime(despesas_salvas['Data'], format='%d/%m/%Y')
            meses_unicos = ['Todos'] + sorted(despesas_salvas['Data_dt'].dt.strftime('%m/%Y').unique().tolist(), reverse=True)
            mes_filtro = st.selectbox("Mês", meses_unicos)
        
        with col3:
            data_inicio = st.date_input("Data início", value=None)
        
        with col4:
            data_fim = st.date_input("Data fim", value=None)
        
        with col5:
            valor_min = st.number_input("Valor mínimo (R$)", min_value=0.0, value=0.0, step=10.0)
        
        # Aplicar filtros
        df_filtrado = despesas_salvas.copy()
        
        if categoria_filtro != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['Descricao'] == categoria_filtro]
        
        if mes_filtro != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Data_dt'].dt.strftime('%m/%Y') == mes_filtro]
        
        if data_inicio:
            df_filtrado = df_filtrado[df_filtrado['Data_dt'] >= pd.to_datetime(data_inicio)]
        
        if data_fim:
            df_filtrado = df_filtrado[df_filtrado['Data_dt'] <= pd.to_datetime(data_fim)]
        
        if valor_min > 0:
            df_filtrado = df_filtrado[df_filtrado['Valor'] >= valor_min]
        
        # Mostrar resultados filtrados
        if not df_filtrado.empty:
            st.info(f"📊 **{len(df_filtrado)} despesas** encontradas (Total: R$ {df_filtrado['Valor'].sum():,.2f})")
            
            # Formatar para exibição
            df_display = df_filtrado.drop(['Data_dt'], axis=1, errors='ignore').copy()
            df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Nenhuma despesa encontrada com os filtros aplicados.")
        
        # Opções de gerenciamento
        st.subheader("🛠️ Gerenciar Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Limpar Todas as Despesas"):
                resultado = gerenciador.limpar_dados(confirmar=True, tipo='despesas')
                if resultado['sucesso']:
                    st.success("✅ Despesas limpas com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ Erro: {resultado['erro']}")
        
        with col2:
            if st.button("💾 Fazer Backup"):
                resultado = gerenciador.fazer_backup()
                if resultado['sucesso']:
                    st.success(f"✅ Backup criado: {resultado['timestamp']}")
                else:
                    st.error(f"❌ Erro: {resultado['erro']}")
        
        # Botão Fechar Mês
        st.markdown("---")
        st.subheader("📈 Fechamento Mensal")
        
        if st.button("📈 Ir para Fechamento de Mês", type="primary", use_container_width=True):
            st.session_state.pagina_atual = "resultado"
            st.rerun()
    
    else:
        st.info("📝 Nenhuma despesa salva ainda. Processe um arquivo OFX no Dashboard primeiro.")
