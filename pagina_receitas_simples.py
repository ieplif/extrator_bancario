import streamlit as st
import pandas as pd
from categorizador_receitas_simples import CategorizadorReceitasSimples
from gerenciador_persistencia_unificado import GerenciadorPersistenciaUnificado
from estilo_unificado import aplicar_estilo_pagina, card_categoria

def pagina_receitas():
    """Página de Receitas - Sistema simples com duas colunas (Paciente e Fonte de Pagamento)."""
    aplicar_estilo_pagina(st)
    st.title("💰 Gestão de Receitas")
    st.markdown("**Sistema simples com duas colunas: Paciente e Fonte de Pagamento**")
    
    # Inicializar gerenciador
    gerenciador = GerenciadorPersistenciaUnificado()
    
    # Verificar se há transações processadas na sessão
    if 'transacoes_processadas' in st.session_state:
        st.success("✅ Dados carregados do Dashboard. Processe a categorização abaixo.")
        
        transacoes = st.session_state.transacoes_processadas
        arquivo_origem = st.session_state.get('arquivo_origem', 'sessao')
        
        # Categorizar receitas
        categorizador = CategorizadorReceitasSimples()
        receitas_categorizadas = categorizador.processar_creditos(transacoes)
        
        if not receitas_categorizadas.empty:
            # Seção de Categorização
            st.header("💰 Receitas Categorizadas")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Resumo da Categorização")
                
                # Estatísticas da categorização
                stats = categorizador.obter_estatisticas()
                
                # Cards de estatísticas
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Total de Receitas", stats['total_creditos'])
                
                with col_stat2:
                    st.metric("Cartão de Crédito", stats['cartao_credito'])
                
                with col_stat3:
                    st.metric("Preenchimento Manual", stats['preenchimento_manual'])
                
                # Resumo por fonte de pagamento
                por_fonte = categorizador.obter_receitas_por_fonte()
                
                if por_fonte:
                    st.subheader("📊 Por Fonte de Pagamento")
                    
                    for fonte, dados in por_fonte.items():
                        # Cor por fonte
                        if 'Cartão' in fonte:
                            cor = '#849585'  # Verde sage
                        else:
                            cor = '#849585'  # Verde sage
                        
                        st.markdown(f"""
                        <div style="
                            background-color: {cor}20;
                            border-left: 4px solid {cor};
                            border-radius: 8px;
                            padding: 15px;
                            margin: 10px 0;
                        ">
                            <h4 style="margin: 0; color: {cor};">{fonte}</h4>
                            <p style="margin: 5px 0; font-size: 1.1em;">
                                <strong>R$ {dados['total']:,.2f}</strong> 
                                ({int(dados['quantidade'])} transações)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Resumo por paciente (apenas preenchidos automaticamente)
                por_paciente = categorizador.obter_receitas_por_paciente()
                
                if por_paciente:
                    st.subheader("👥 Pacientes Identificados Automaticamente")
                    
                    for paciente, dados in por_paciente.items():
                        st.markdown(f"""
                        <div style="
                            background-color: #E9E5DC;
                            border-left: 4px solid #849585;
                            border-radius: 8px;
                            padding: 15px;
                            margin: 10px 0;
                        ">
                            <h4 style="margin: 0; color: #849585;">{paciente}</h4>
                            <p style="margin: 5px 0; font-size: 1.1em;">
                                <strong>R$ {dados['total']:,.2f}</strong> 
                                ({int(dados['quantidade'])} transações)
                            </p>
                            <p style="margin: 0; font-size: 0.9em; color: #666;">📅 {dados.get('todas_datas')}
                            </p>


                        </div>
                        """, unsafe_allow_html=True)
            
            with col2:
                st.subheader("Ações")
                
                # Informações sobre preenchimento manual
                receitas_manuais = categorizador.obter_receitas_preenchimento_manual()
                
                if not receitas_manuais.empty:
                    st.warning(f"""
                    ⚠️ **{len(receitas_manuais)} receitas** requerem preenchimento manual:
                    
                    - **Cartão de crédito:** Preencher campo Paciente
                    - **Lista especial:** Preencher Paciente e Fonte de Pagamento
                    
                    Você poderá editar após salvar os dados.
                    """)
                else:
                    st.success("✅ Todas as receitas foram categorizadas automaticamente!")
                
                # Seleção de mês/ano
                from datetime import datetime
                col_mes_rec, col_ano_rec = st.columns(2)
                
                with col_mes_rec:
                    mes_rec = st.selectbox(
                        "Mês",
                        options=list(range(1, 13)),
                        format_func=lambda x: f"{x:02d}",
                        index=datetime.now().month - 1,
                        key="mes_receitas_salvar"
                    )
                
                with col_ano_rec:
                    ano_rec = st.selectbox(
                        "Ano",
                        options=list(range(2020, 2030)),
                        index=list(range(2020, 2030)).index(datetime.now().year),
                        key="ano_receitas"
                    )
                
                mes_ano_rec = f"{mes_rec:02d}/{ano_rec}"
                st.info(f"📅 Receitas para: **{mes_ano_rec}**")
                
                # Opções de salvamento
                modo_salvamento = st.radio(
                    "Como salvar as receitas?",
                    ["Adicionar às existentes", "Sobrescrever dados salvos"],
                    help="Adicionar: mantém receitas anteriores. Sobrescrever: remove todas as anteriores."
                )
                
                if st.button("💾 Salvar Receitas Categorizadas", type="primary"):
                    modo = 'adicionar' if modo_salvamento == "Adicionar às existentes" else 'sobrescrever'
                    
                    resultado = gerenciador.salvar_receitas(
                        receitas_categorizadas, 
                        arquivo_origem, 
                        modo,
                        mes_ano=mes_ano_rec
                    )
                    
                    if resultado['sucesso']:
                        # Obter resumo atualizado
                        resumo_atualizado = gerenciador.obter_resumo_receitas()
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
                        ✅ **Receitas salvas com sucesso!**
                        
                        - **Novas receitas:** {resultado['novas_receitas']}
                        - **Total de receitas:** {resultado['total_receitas']}
                        - **Modo:** {resultado['modo']}
                        - **Requer preenchimento:** {resultado['requer_preenchimento_manual']}
                        
                        {periodo_texto}
                        """)
                        
                        # Limpar dados da sessão
                        if 'transacoes_processadas' in st.session_state:
                            del st.session_state.transacoes_processadas
                        if 'arquivo_origem' in st.session_state:
                            del st.session_state.arquivo_origem
                        
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao salvar: {resultado['erro']}")
                
                # Download das receitas categorizadas
                csv_categorizadas = receitas_categorizadas.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Baixar Categorizadas (CSV)",
                    data=csv_categorizadas,
                    file_name=f"receitas_categorizadas_{arquivo_origem.replace('.ofx', '')}.csv",
                    mime="text/csv"
                )
                
                # Botão para limpar dados da sessão
                if st.button("🗑️ Limpar Dados da Sessão"):
                    if 'transacoes_processadas' in st.session_state:
                        del st.session_state.transacoes_processadas
                    if 'arquivo_origem' in st.session_state:
                        del st.session_state.arquivo_origem
                    st.rerun()
            
            # Tabela detalhada das receitas categorizadas
            st.subheader("📋 Detalhes das Receitas Categorizadas")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tipos_preenchimento = ['Todos'] + list(receitas_categorizadas['Tipo_Preenchimento'].unique())
                tipo_filtro = st.selectbox("Filtrar por tipo:", tipos_preenchimento)
            
            with col2:
                fontes_disponiveis = ['Todas'] + [f for f in receitas_categorizadas['Fonte_Pagamento'].unique() if f != '']
                fonte_filtro = st.selectbox("Filtrar por fonte:", fontes_disponiveis)
            
            with col3:
                valor_min = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=10.0)
            
            # Aplicar filtros
            receitas_filtradas = receitas_categorizadas.copy()
            
            if tipo_filtro != 'Todos':
                receitas_filtradas = receitas_filtradas[receitas_filtradas['Tipo_Preenchimento'] == tipo_filtro]
            
            if fonte_filtro != 'Todas':
                receitas_filtradas = receitas_filtradas[receitas_filtradas['Fonte_Pagamento'] == fonte_filtro]
            
            if valor_min > 0:
                receitas_filtradas = receitas_filtradas[receitas_filtradas['Valor'] >= valor_min]
            
            # Formatar valores para exibição
            receitas_display = receitas_filtradas.copy()
            receitas_display['Valor'] = receitas_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(
                receitas_display[['Data', 'Paciente', 'Fonte_Pagamento', 'Valor', 'Razao_Social_Original', 'Tipo_Preenchimento']], 
                use_container_width=True, 
                hide_index=True
            )
        
        else:
            st.info("Nenhuma receita (crédito) encontrada nos dados processados.")
    
    # Seção de Receitas Salvas
    st.header("💾 Receitas Salvas")
    
    receitas_salvas = gerenciador.carregar_receitas()
    
    if not receitas_salvas.empty:
        resumo = gerenciador.obter_resumo_receitas()
        
        # Métricas das receitas salvas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Receitas", resumo['total_receitas'])
        
        with col2:
            st.metric("Valor Total", f"R$ {resumo['valor_total']:,.2f}")
        
        with col3:
            st.metric("Preenchimento Manual", resumo['preenchimento']['manual'])
        
        with col4:
            periodo = resumo.get('periodo', {})
            if periodo:
                st.metric("Período", f"{periodo.get('inicio', 'N/A')} a {periodo.get('fim', 'N/A')}")
        
        # Seção de Preenchimento Manual
        receitas_manuais_salvas = gerenciador.obter_receitas_preenchimento_manual()
        
        if not receitas_manuais_salvas.empty:
            st.header("✏️ Preenchimento Manual")
            
            st.info(f"""
            📝 **{len(receitas_manuais_salvas)} receitas** aguardando preenchimento manual.
            
            Preencha os campos Paciente e/ou Fonte de Pagamento conforme necessário.
            """)
            
            # Interface de preenchimento manual
            for index, receita in receitas_manuais_salvas.iterrows():
                # Verificar se é cartão de crédito para mostrar interface de divisão
                is_cartao = receita['Tipo_Preenchimento'] == 'cartao_credito'
                
                with st.expander(f"✏️ {receita['Razao_Social_Original']} - R$ {receita['Valor']:,.2f} ({receita['Data']})"):
                    # Informações da transação original
                    st.markdown("### 📋 Informações da Transação Original")
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Data do Pagamento", receita['Data'])
                    with col_info2:
                        st.metric("Valor Total", f"R$ {receita['Valor']:,.2f}")
                    with col_info3:
                        st.metric("Fonte", receita['Fonte_Pagamento'] if receita['Fonte_Pagamento'] else 'N/A')
                    
                    st.markdown(f"**Razão Social:** {receita['Razao_Social_Original']}")
                    st.markdown(f"**Tipo:** {receita['Tipo_Preenchimento']}")
                    
                    st.markdown("---")
                    
                    if is_cartao:
                        # Interface de divisão para cartão de crédito
                        st.markdown("### 👥 Dividir entre Pacientes")
                        
                        # Inicializar lista de pacientes no session_state
                        if f'divisoes_{index}' not in st.session_state:
                            st.session_state[f'divisoes_{index}'] = [
                                {'paciente': '', 'valor': 0.0, 'data': receita['Data']}
                            ]
                        
                        divisoes = st.session_state[f'divisoes_{index}']
                        
                        # Renderizar campos para cada paciente
                        for i, div in enumerate(divisoes):
                            st.markdown(f"#### Paciente {i+1}")
                            
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                div['paciente'] = st.text_input(
                                    "Nome do Paciente",
                                    value=div['paciente'],
                                    key=f"div_nome_{index}_{i}",
                                    placeholder="Ex: João Silva"
                                )
                            
                            with col2:
                                div['valor'] = st.number_input(
                                    "Valor (R$)",
                                    min_value=0.0,
                                    value=float(div['valor']),
                                    step=0.01,
                                    format="%.2f",
                                    key=f"div_valor_{index}_{i}"
                                )
                            
                            with col3:
                                div['data'] = st.text_input(
                                    "Data da Consulta",
                                    value=div['data'],
                                    key=f"div_data_{index}_{i}",
                                    placeholder="DD/MM/AAAA"
                                )
                            
                            with col4:
                                if len(divisoes) > 1:
                                    if st.button("❌", key=f"remover_{index}_{i}", help="Remover paciente"):
                                        divisoes.pop(i)
                                        st.rerun()
                        
                        # Botão para adicionar mais pacientes
                        col_add, col_space = st.columns([1, 3])
                        with col_add:
                            if st.button("➕ Adicionar Paciente", key=f"add_{index}"):
                                divisoes.append({'paciente': '', 'valor': 0.0, 'data': receita['Data']})
                                st.rerun()
                        
                        # Resumo da divisão
                        st.markdown("---")
                        st.markdown("### 📊 Resumo da Divisão")
                        
                        soma_valores = sum(d['valor'] for d in divisoes)
                        diferenca = abs(soma_valores - receita['Valor'])
                        
                        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                        
                        with col_res1:
                            st.metric("Pacientes", len(divisoes))
                        
                        with col_res2:
                            st.metric("Soma", f"R$ {soma_valores:,.2f}")
                        
                        with col_res3:
                            st.metric("Original", f"R$ {receita['Valor']:,.2f}")
                        
                        with col_res4:
                            if diferenca < 0.01:
                                st.metric("Diferença", "R$ 0,00", delta="✅ OK")
                            elif diferenca < 1.00:
                                st.metric("Diferença", f"R$ {diferenca:.2f}", delta="⚠️ Pequena")
                            else:
                                st.metric("Diferença", f"R$ {diferenca:.2f}", delta="❌ Grande")
                        
                        # Validação visual
                        if diferenca >= 0.01:
                            if diferenca < 1.00:
                                st.warning(f"⚠️ A diferença é de R$ {diferenca:.2f}. Deseja continuar mesmo assim?")
                            else:
                                st.error(f"❌ A diferença é de R$ {diferenca:.2f}. Verifique os valores antes de salvar.")
                        else:
                            st.success("✅ Os valores conferem!")
                        
                        # Botões de ação
                        col_salvar, col_cancelar = st.columns(2)
                        
                        with col_salvar:
                            if st.button("💾 Salvar Divisão", key=f"salvar_div_{index}", type="primary"):
                                # Validar antes de salvar
                                erros = []
                                for i, div in enumerate(divisoes, 1):
                                    if not div['paciente'].strip():
                                        erros.append(f"Paciente {i}: nome vazio")
                                    if div['valor'] <= 0:
                                        erros.append(f"Paciente {i}: valor inválido")
                                    if not div['data'].strip():
                                        erros.append(f"Paciente {i}: data vazia")
                                
                                if erros:
                                    st.error("❌ Erros encontrados:\n" + "\n".join(f"- {e}" for e in erros))
                                else:
                                    resultado = gerenciador.dividir_receita_cartao(
                                        data_original=receita['Data'],
                                        razao_social=receita['Razao_Social_Original'],
                                        valor_original=receita['Valor'],
                                        divisoes=divisoes
                                    )
                                    
                                    if resultado['sucesso']:
                                        st.success(f"""
                                        ✅ **Receita dividida com sucesso!**
                                        
                                        - **Pacientes:** {resultado['receitas_criadas']}
                                        - **Valor total:** R$ {resultado['valor_total']:,.2f}
                                        - **Diferença:** R$ {resultado['diferenca']:.2f}
                                        """)
                                        
                                        # Limpar session_state
                                        if f'divisoes_{index}' in st.session_state:
                                            del st.session_state[f'divisoes_{index}']
                                        
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro: {resultado['erro']}")
                        
                        with col_cancelar:
                            if st.button("🔄 Cancelar", key=f"cancelar_div_{index}"):
                                if f'divisoes_{index}' in st.session_state:
                                    del st.session_state[f'divisoes_{index}']
                                st.rerun()
                    
                    else:
                        # Interface simples para outros tipos (manual)
                        st.markdown("### ✏️ Preencher Campos")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Campos atuais
                            paciente_atual = receita['Paciente'] if receita['Paciente'] else ""
                            
                            # Input para preenchimento
                            novo_paciente = st.text_input(
                                "Nome do Paciente:", 
                                value=paciente_atual,
                                key=f"paciente_{index}"
                            )
                        
                        with col2:
                            fonte_atual = receita['Fonte_Pagamento'] if receita['Fonte_Pagamento'] else ""
                            
                            novo_fonte = st.selectbox(
                                "Fonte de Pagamento:",
                                ["", "Particular", "Cartão de Crédito", "Convênio", "PIX", "Transferência"],
                                index=0 if not fonte_atual else ["", "Particular", "Cartão de Crédito", "Convênio", "PIX", "Transferência"].index(fonte_atual) if fonte_atual in ["", "Particular", "Cartão de Crédito", "Convênio", "PIX", "Transferência"] else 0,
                                key=f"fonte_{index}"
                            )
                        
                        if st.button("💾 Atualizar", key=f"atualizar_{index}", type="primary"):
                            resultado = gerenciador.atualizar_receita_por_dados(
                                receita['Data'],
                                receita['Razao_Social_Original'],
                                receita['Valor'],
                                paciente=novo_paciente if novo_paciente.strip() else None,
                                fonte_pagamento=novo_fonte if novo_fonte.strip() else None
                            )
                            
                            if resultado['sucesso']:
                                st.success("✅ Receita atualizada com sucesso!")
                                st.rerun()
                            else:
                                st.error(f"❌ Erro: {resultado['erro']}")
        
        # Resumo por Fonte de Pagamento
        if resumo['por_fonte_pagamento']:
            st.subheader("📊 Resumo por Fonte de Pagamento")
            
            col1, col2 = st.columns(2)
            
            with col1:
                for fonte, dados in resumo['por_fonte_pagamento'].items():
                    # Converter valores numpy para float
                    total = float(dados['total'])
                    quantidade = int(dados['quantidade'])
                    media = float(dados['media'])
                    
                    # Cor por fonte
                    if 'Cartão' in fonte:
                        cor = '#849585'
                    else:
                        cor = '#849585'
                    
                    st.markdown(f"""
                    <div style="
                        background-color: {cor}20;
                        border-left: 4px solid {cor};
                        border-radius: 8px;
                        padding: 15px;
                        margin: 10px 0;
                    ">
                        <h4 style="margin: 0; color: {cor};">{fonte}</h4>
                        <p style="margin: 5px 0; font-size: 1.1em;">
                            <strong>R$ {total:,.2f}</strong> 
                            ({quantidade} transações)
                        </p>
                        <small>Média: R$ {media:,.2f}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                # Filtros para receitas salvas
                st.subheader("🔍 Filtrar Receitas Salvas")
                
                # Preparar dados de data
                receitas_salvas['Data_dt'] = pd.to_datetime(receitas_salvas['Data'], format='%d/%m/%Y')
                receitas_salvas['Mes_Ano'] = receitas_salvas['Data_dt'].dt.strftime('%m/%Y')
                
                # Filtro por fonte de pagamento
                fontes_unicas = ['Todas'] + [f for f in receitas_salvas['Fonte_Pagamento'].unique() if f != '']
                fonte_filtro_salvas = st.selectbox("Fonte de Pagamento:", fontes_unicas, key="fonte_receitas")
                
                # Filtro por mês
                meses_unicos = ['Todos'] + sorted(list(receitas_salvas['Mes_Ano'].unique()), reverse=True)
                mes_filtro = st.selectbox("Mês:", meses_unicos, key="mes_receitas_filtro")
                
                # Filtro por período personalizado
                col_data1, col_data2 = st.columns(2)
                with col_data1:
                    data_inicio = st.date_input("Data início:", value=None, key="data_inicio_receitas")
                with col_data2:
                    data_fim = st.date_input("Data fim:", value=None, key="data_fim_receitas")
                
                # Filtro por valor
                valor_min_salvas = st.number_input("Valor mínimo:", min_value=0.0, value=0.0, key="valor_min_receitas")
                
                # Aplicar filtros
                receitas_filtradas_salvas = receitas_salvas.copy()
                
                if fonte_filtro_salvas != 'Todas':
                    receitas_filtradas_salvas = receitas_filtradas_salvas[receitas_filtradas_salvas['Fonte_Pagamento'] == fonte_filtro_salvas]
                
                if mes_filtro != 'Todos':
                    receitas_filtradas_salvas = receitas_filtradas_salvas[receitas_filtradas_salvas['Mes_Ano'] == mes_filtro]
                
                if data_inicio is not None:
                    receitas_filtradas_salvas = receitas_filtradas_salvas[receitas_filtradas_salvas['Data_dt'] >= pd.to_datetime(data_inicio)]
                
                if data_fim is not None:
                    receitas_filtradas_salvas = receitas_filtradas_salvas[receitas_filtradas_salvas['Data_dt'] <= pd.to_datetime(data_fim)]
                
                if valor_min_salvas > 0:
                    receitas_filtradas_salvas = receitas_filtradas_salvas[receitas_filtradas_salvas['Valor'] >= valor_min_salvas]
                
                # Download das receitas salvas
                csv_receitas_salvas = receitas_filtradas_salvas.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Baixar Receitas Filtradas (CSV)",
                    data=csv_receitas_salvas,
                    file_name=f"receitas_salvas_{fonte_filtro_salvas.lower()}.csv",
                    mime="text/csv"
                )
        
        # Resumo por Paciente
        if resumo['por_paciente']:
            st.subheader("👥 Resumo por Paciente")
            
            # Mostrar apenas os 10 pacientes com maior valor
            pacientes_ordenados = sorted(
                resumo['por_paciente'].items(), 
                key=lambda x: float(x[1]['total']), 
                reverse=True
            )[:10]
            
            for paciente, dados in pacientes_ordenados:
                total = float(dados['total'])
                quantidade = int(dados['quantidade'])
                media = float(dados['media'])
                
                st.markdown(f"""
                <div style="
                    background-color: #E9E5DC;
                    border-left: 4px solid #849585;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                ">
                    <h4 style="margin: 0; color: #849585;">{paciente}</h4>
                    <p style="margin: 5px 0; font-size: 1.1em;">
                        <strong>R$ {total:,.2f}</strong> 
                        ({quantidade} transações)
                    </p>
                    <p style="margin: 0; font-size: 0.9em; color: #666;">📅 {dados.get('todas_datas')}
                    </p>
                """, unsafe_allow_html=True)
            
            if len(resumo['por_paciente']) > 10:
                st.info(f"Mostrando os 10 pacientes com maior valor. Total: {len(resumo['por_paciente'])} pacientes.")
        
        # Análise temporal por mês
        if len(receitas_filtradas_salvas) > 0:
            st.subheader("📅 Análise Temporal por Mês")
            
            # Preparar dados mensais
            analise_mensal_total = receitas_filtradas_salvas.groupby('Mes_Ano')['Valor'].agg(['sum', 'count']).reset_index()
            analise_mensal_total.columns = ['Mes_Ano', 'Total', 'Quantidade']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**💰 Total por Mês:**")
                for _, row in analise_mensal_total.iterrows():
                    st.markdown(f"""
                    <div style="
                        background-color: #E9E5DC;
                        border-left: 4px solid #849585;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 10px 0;
                    ">
                        <h4 style="margin: 0; color: #849585;">📅 {row['Mes_Ano']}</h4>
                        <p style="margin: 5px 0; font-size: 1.1em;">
                            <strong>R$ {row['Total']:,.2f}</strong> 
                            ({int(row['Quantidade'])} transações)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.write("**📊 Gráfico Temporal:**")
                
                if len(analise_mensal_total) > 1:
                    # Ordenar por data
                    analise_mensal_total['Data_Sort'] = pd.to_datetime(analise_mensal_total['Mes_Ano'], format='%m/%Y')
                    analise_mensal_total = analise_mensal_total.sort_values('Data_Sort')
                    
                    # Gráfico de linha
                    st.line_chart(analise_mensal_total.set_index('Mes_Ano')['Total'])
                else:
                    st.info("Adicione mais dados para visualizar tendências temporais.")
        
        # Mostrar tabela das receitas salvas
        st.subheader("📋 Receitas Filtradas")
        
        # Mostrar informações do filtro aplicado
        info_filtro = []
        if 'fonte_filtro_salvas' in locals() and fonte_filtro_salvas != 'Todas':
            info_filtro.append(f"Fonte: {fonte_filtro_salvas}")
        if 'mes_filtro' in locals() and mes_filtro != 'Todos':
            info_filtro.append(f"Mês: {mes_filtro}")
        if 'data_inicio' in locals() and data_inicio is not None:
            info_filtro.append(f"A partir de: {data_inicio.strftime('%d/%m/%Y')}")
        if 'data_fim' in locals() and data_fim is not None:
            info_filtro.append(f"Até: {data_fim.strftime('%d/%m/%Y')}")
        if 'valor_min_salvas' in locals() and valor_min_salvas > 0:
            info_filtro.append(f"Valor mín: R$ {valor_min_salvas:,.2f}")
        
        if info_filtro:
            st.info(f"**Filtros aplicados:** {' | '.join(info_filtro)}")
        
        # Mostrar métricas das receitas filtradas
        if len(receitas_filtradas_salvas) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Receitas Filtradas", len(receitas_filtradas_salvas))
            
            with col2:
                total_filtrado = receitas_filtradas_salvas['Valor'].sum()
                st.metric("Total Filtrado", f"R$ {total_filtrado:,.2f}")
            
            with col3:
                media_filtrada = receitas_filtradas_salvas['Valor'].mean()
                st.metric("Média", f"R$ {media_filtrada:,.2f}")
        
        # Formatar valores para exibição
        receitas_display_salvas = receitas_filtradas_salvas.copy()
        receitas_display_salvas['Valor'] = receitas_display_salvas['Valor'].apply(lambda x: f"R$ {x:,.2f}")
        
        st.dataframe(
            receitas_display_salvas[['Data', 'Paciente', 'Fonte_Pagamento', 'Valor', 'Razao_Social_Original', 'Tipo_Preenchimento']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Opções de gestão
        st.subheader("🛠️ Gestão de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📦 Fazer Backup", key="backup_receitas"):
                resultado_backup = gerenciador.fazer_backup()
                if resultado_backup['sucesso']:
                    st.success(f"✅ Backup criado: {resultado_backup['timestamp']}")
                else:
                    st.error(f"❌ Erro no backup: {resultado_backup['erro']}")
        
        with col2:
            if st.button("🗑️ Limpar Todos os Dados", key="limpar_receitas"):
                if st.checkbox("Confirmar limpeza (irreversível)", key="confirmar_limpeza_receitas"):
                    resultado = gerenciador.limpar_dados(confirmar=True)
                    if resultado['sucesso']:
                        st.success("✅ Dados limpos com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {resultado['erro']}")
    
    else:
        st.info("""
        📝 **Nenhuma receita salva ainda.**
        
        Para começar:
        1. Vá para o **Dashboard**
        2. Faça upload de um arquivo OFX
        3. Clique em "Ir para Categorização de Receitas"
        4. Salve as receitas categorizadas
        """)
