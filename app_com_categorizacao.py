import streamlit as st
import pandas as pd
import tempfile
import os
from extrator_ofx import ExtratorOFX
from categorizador_despesas import CategorizadorDespesas
from gerenciador_persistencia import GerenciadorPersistencia

def main():
    st.set_page_config(page_title="Extrator Bancario", page_icon="💰", layout="wide")
    
    st.title("💰 Extrator de Dados Bancarios OFX")
    st.markdown("**Faca upload de um arquivo OFX para extrair, categorizar e salvar dados bancarios**")
    
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
    
    /* Estilo para categorias */
    .categoria-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar com informações e dados persistentes
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
        
        # Seção de dados persistentes
        st.header("📊 Dados Salvos")
        
        # Inicializar gerenciador
        gerenciador = GerenciadorPersistencia()
        despesas_salvas = gerenciador.carregar_despesas()
        
        if not despesas_salvas.empty:
            resumo = gerenciador.obter_resumo_despesas()
            
            st.metric("Total de Despesas", resumo['total_despesas'])
            st.metric("Valor Total", f"R$ {resumo['valor_total']:,.2f}")
            
            # Mostrar categorias
            st.subheader("Por Categoria:")
            for categoria, dados in resumo['por_categoria'].items():
                st.write(f"**{categoria}:** R$ {dados['total']:,.2f} ({dados['quantidade']} itens)")
            
            # Botão para ver detalhes
            if st.button("📋 Ver Todas as Despesas"):
                st.session_state.mostrar_despesas_salvas = True
        else:
            st.info("Nenhuma despesa salva ainda.")
            
        # Botão para limpar dados
        if st.button("🗑️ Limpar Dados", help="Remove todas as despesas salvas"):
            if st.checkbox("Confirmar limpeza (irreversível)"):
                resultado = gerenciador.limpar_dados(confirmar=True)
                if resultado['sucesso']:
                    st.success("Dados limpos com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro: {resultado['erro']}")
    
    # Mostrar despesas salvas se solicitado
    if st.session_state.get('mostrar_despesas_salvas', False):
        st.header("📋 Todas as Despesas Salvas")
        
        if not despesas_salvas.empty:
            # Filtros para despesas salvas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                categorias_unicas = ['Todas'] + list(despesas_salvas['Descricao'].unique())
                categoria_filtro = st.selectbox("Filtrar por categoria:", categorias_unicas)
            
            with col2:
                valor_min_salvas = st.number_input("Valor mínimo:", min_value=0.0, value=0.0, key="valor_min_salvas")
            
            with col3:
                if st.button("❌ Fechar"):
                    st.session_state.mostrar_despesas_salvas = False
                    st.rerun()
            
            # Aplicar filtros
            despesas_filtradas = despesas_salvas.copy()
            
            if categoria_filtro != 'Todas':
                despesas_filtradas = despesas_filtradas[despesas_filtradas['Descricao'] == categoria_filtro]
            
            if valor_min_salvas > 0:
                despesas_filtradas = despesas_filtradas[despesas_filtradas['Valor'] >= valor_min_salvas]
            
            # Mostrar tabela
            st.dataframe(
                despesas_filtradas[['Data', 'Descricao', 'Valor', 'Razao_Social_Original', 'Arquivo_Origem']], 
                use_container_width=True, 
                hide_index=True
            )
            
            # Download das despesas salvas
            csv_despesas_salvas = despesas_filtradas.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="📥 Baixar Despesas Filtradas (CSV)",
                data=csv_despesas_salvas,
                file_name=f"despesas_salvas_{categoria_filtro.lower()}.csv",
                mime="text/csv"
            )
        
        st.divider()
    
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
                
                # Categorizar despesas
                categorizador = CategorizadorDespesas()
                despesas_categorizadas = categorizador.processar_debitos(transacoes)
                stats_categorizacao = categorizador.obter_estatisticas_regras(transacoes)
            
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
                
                # Seção de Categorização de Despesas
                st.header("🏷️ Despesas Categorizadas")
                
                if not despesas_categorizadas.empty:
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
                        
                        nome_arquivo = uploaded_file.name if uploaded_file else "manual"
                        
                        if st.button("💾 Salvar Despesas Categorizadas", type="primary"):
                            modo = 'adicionar' if modo_salvamento == "Adicionar às existentes" else 'sobrescrever'
                            
                            resultado = gerenciador.salvar_despesas(
                                despesas_categorizadas, 
                                nome_arquivo, 
                                modo
                            )
                            
                            if resultado['sucesso']:
                                st.success(f"""
                                ✅ **Despesas salvas com sucesso!**
                                
                                - **Novas despesas:** {resultado['novas_despesas']}
                                - **Total de despesas:** {resultado['total_despesas']}
                                - **Modo:** {resultado['modo']}
                                """)
                                
                                # Atualizar sidebar
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao salvar: {resultado['erro']}")
                        
                        # Download das despesas categorizadas
                        csv_categorizadas = despesas_categorizadas.to_csv(index=False, encoding='utf-8')
                        st.download_button(
                            label="📥 Baixar Categorizadas (CSV)",
                            data=csv_categorizadas,
                            file_name=f"despesas_categorizadas_{nome_arquivo.replace('.ofx', '')}.csv",
                            mime="text/csv"
                        )
                    
                    # Tabela detalhada das despesas categorizadas
                    st.subheader("Detalhes das Despesas Categorizadas")
                    
                    # Filtros
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        categorias_disponiveis = ['Todas'] + list(despesas_categorizadas['Descricao'].unique())
                        categoria_filtro_cat = st.selectbox("Filtrar por categoria:", categorias_disponiveis, key="cat_filter")
                    
                    with col2:
                        valor_min_cat = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=10.0, key="valor_min_cat")
                    
                    # Aplicar filtros
                    despesas_filtradas_cat = despesas_categorizadas.copy()
                    
                    if categoria_filtro_cat != 'Todas':
                        despesas_filtradas_cat = despesas_filtradas_cat[despesas_filtradas_cat['Descricao'] == categoria_filtro_cat]
                    
                    if valor_min_cat > 0:
                        despesas_filtradas_cat = despesas_filtradas_cat[despesas_filtradas_cat['Valor'] >= valor_min_cat]
                    
                    # Formatar valores para exibição
                    despesas_display = despesas_filtradas_cat.copy()
                    despesas_display['Valor'] = despesas_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")
                    
                    st.dataframe(
                        despesas_display[['Data', 'Descricao', 'Valor', 'Razao_Social_Original']], 
                        use_container_width=True, 
                        hide_index=True
                    )
                
                else:
                    st.info("Nenhuma despesa (débito) encontrada neste extrato.")
                
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
                    st.subheader("Despesas por Categoria")
                    
                    if not despesas_categorizadas.empty:
                        # Gráfico de categorias
                        cat_resumo = despesas_categorizadas.groupby('Descricao')['Valor'].sum().sort_values(ascending=False)
                        
                        # Criar gráfico de barras para categorias
                        max_cat_valor = cat_resumo.max()
                        
                        st.markdown("<div style='margin: 20px 0;'>", unsafe_allow_html=True)
                        
                        for categoria, valor in cat_resumo.items():
                            altura_cat = (valor / max_cat_valor) * 200
                            
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
                                    R$ {valor:,.0f}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.info("Nenhuma despesa para categorizar.")
                
                # Tabela de transações válidas (todas)
                st.header("📋 Todas as Transacoes Validas")
                
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
        3. Visualize os dados extraidos e categorizados
        4. Salve as despesas categorizadas na tabela persistente
        5. Baixe os arquivos CSV organizados
        
        **Novo:** Sistema de categorização automática de despesas com tabela persistente!
        """)

if __name__ == "__main__":
    main()
