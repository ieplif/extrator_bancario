import streamlit as st
import pandas as pd
from datetime import datetime
from gerenciador_resultado import GerenciadorResultado
from gerenciador_persistencia_unificado import GerenciadorPersistenciaUnificado

def pagina_resultado():
    """Página de resultados mensais e fechamentos."""
    
    st.title("📊 Resultados Mensais")
    st.markdown("Fechamentos mensais e análise de resultados")
    
    # Inicializar gerenciadores
    gerenciador_resultado = GerenciadorResultado()
    gerenciador_dados = GerenciadorPersistenciaUnificado()
    
    # Carregar dados existentes
    resultados_salvos = gerenciador_resultado.carregar_resultados()
    
    # Sidebar com informações
    with st.sidebar:
        st.header("📋 Resultados Salvos")
        
        if not resultados_salvos.empty:
            total_fechamentos = len(resultados_salvos)
            ultimo_fechamento = resultados_salvos.iloc[0]['Mes_Ano']
            
            st.metric("Total de Fechamentos", total_fechamentos)
            st.metric("Último Fechamento", ultimo_fechamento)
            
            # Lista de fechamentos
            st.subheader("📅 Fechamentos Disponíveis")
            for _, resultado in resultados_salvos.iterrows():
                mes_ano = resultado['Mes_Ano']
                resultado_liquido = resultado['Resultado_Liquido']
                cor = "🟢" if resultado_liquido >= 0 else "🔴"
                st.write(f"{cor} {mes_ano}: R$ {resultado_liquido:,.2f}")
        else:
            st.info("Nenhum fechamento realizado ainda")
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["🔄 Novo Fechamento", "📊 Resultados Salvos", "📈 Análise Anual"])
    
    with tab1:
        st.header("🔄 Realizar Novo Fechamento")
        
        # Verificar se há dados para fechamento
        despesas_salvas = gerenciador_dados.carregar_despesas()
        receitas_salvas = gerenciador_dados.carregar_receitas()
        
        if despesas_salvas.empty and receitas_salvas.empty:
            st.warning("⚠️ Nenhum dado de receitas ou despesas encontrado. Processe extratos primeiro nas páginas de Receitas e Despesas.")
            return
        
        # Seleção do mês para fechamento
        col1, col2 = st.columns(2)
        
        with col1:
            mes = st.selectbox(
                "Mês",
                options=list(range(1, 13)),
                format_func=lambda x: f"{x:02d}",
                index=datetime.now().month - 1
            )
        
        with col2:
            ano = st.selectbox(
                "Ano",
                options=list(range(2020, 2030)),
                index=list(range(2020, 2030)).index(datetime.now().year)
            )
        
        mes_ano = f"{mes:02d}/{ano}"
        
        # Verificar se já existe fechamento
        fechamento_existente = gerenciador_resultado.obter_resultado_mes(mes_ano)
        
        if fechamento_existente:
            st.warning(f"⚠️ Já existe fechamento para {mes_ano}")
            st.json(fechamento_existente)
            sobrescrever = st.checkbox("Sobrescrever fechamento existente")
        else:
            sobrescrever = False
        
        # Filtrar dados do mês selecionado
        if not despesas_salvas.empty:
            despesas_salvas['Data_Obj'] = pd.to_datetime(despesas_salvas['Data'], format='%d/%m/%Y')
            despesas_mes = despesas_salvas[
                (despesas_salvas['Data_Obj'].dt.month == mes) & 
                (despesas_salvas['Data_Obj'].dt.year == ano)
            ]
        else:
            despesas_mes = pd.DataFrame()
        
        if not receitas_salvas.empty:
            receitas_salvas['Data_Obj'] = pd.to_datetime(receitas_salvas['Data'], format='%d/%m/%Y')
            receitas_mes = receitas_salvas[
                (receitas_salvas['Data_Obj'].dt.month == mes) & 
                (receitas_salvas['Data_Obj'].dt.year == ano)
            ]
        else:
            receitas_mes = pd.DataFrame()
        
        # Mostrar preview do fechamento
        if not despesas_mes.empty or not receitas_mes.empty:
            st.subheader(f"📋 Preview do Fechamento - {mes_ano}")
            
            # Calcular resultado
            resultado_calculado = gerenciador_resultado.calcular_resultado_mes(
                mes_ano, receitas_mes, despesas_mes
            )
            
            if 'erro' not in resultado_calculado:
                # Exibir resultado formatado
                st.markdown("### 💰 Receita Bruta")
                st.metric("", f"R$ {resultado_calculado['receita_bruta']:,.2f}")
                
                st.markdown("### 📋 Despesas Operacionais")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🏠 Aluguel", f"R$ {resultado_calculado['despesas_operacionais']['Aluguel']:,.2f}")
                    st.metric("⚡ Luz", f"R$ {resultado_calculado['despesas_operacionais']['Luz']:,.2f}")
                
                with col2:
                    st.metric("🏥 Fisioterapeutas", f"R$ {resultado_calculado['despesas_operacionais']['Fisioterapeutas']:,.2f}")
                    st.metric("🧹 Limpeza", f"R$ {resultado_calculado['despesas_operacionais']['Limpeza']:,.2f}")
                
                with col3:
                    st.metric("📦 Diversos", f"R$ {resultado_calculado['despesas_operacionais']['Diversos']:,.2f}")
                
                st.markdown("---")
                st.metric("📋 Total Operacionais", f"R$ {resultado_calculado['total_operacionais']:,.2f}")
                
                st.markdown("### 💼 Resultado Bruto")
                resultado_bruto_cor = "normal" if resultado_calculado['resultado_bruto'] >= 0 else "inverse"
                st.metric("", f"R$ {resultado_calculado['resultado_bruto']:,.2f}", delta_color=resultado_bruto_cor)
                
                st.markdown("### 💸 Retirada")
                st.metric("", f"R$ {resultado_calculado['retirada']:,.2f}")
                
                st.markdown("### 🎯 Resultado Líquido")
                resultado_liquido_cor = "normal" if resultado_calculado['resultado_liquido'] >= 0 else "inverse"
                st.metric("", f"R$ {resultado_calculado['resultado_liquido']:,.2f}", delta_color=resultado_liquido_cor)
                
                # Campo para observações
                observacoes = st.text_area("📝 Observações (opcional)", placeholder="Adicione observações sobre este fechamento...")
                
                # Botão para salvar
                col1, col2 = st.columns(2)
                
                with col1:
                    disabled_button = bool(fechamento_existente) and not sobrescrever
                    if st.button("💾 Salvar Fechamento", type="primary", disabled=disabled_button):
                        if sobrescrever:
                            resultado_salvar = gerenciador_resultado.sobrescrever_fechamento(resultado_calculado, observacoes)
                        else:
                            resultado_salvar = gerenciador_resultado.salvar_fechamento(resultado_calculado, observacoes)
                        
                        if resultado_salvar['sucesso']:
                            st.success(f"✅ Fechamento de {mes_ano} salvo com sucesso!")
                            if sobrescrever:
                                st.info("ℹ️ Fechamento anterior foi sobrescrito")
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao salvar: {resultado_salvar['erro']}")
                
                with col2:
                    if fechamento_existente:
                        if st.button("🗑️ Excluir Fechamento Existente", type="secondary"):
                            resultado_exclusao = gerenciador_resultado.excluir_fechamento(mes_ano)
                            if resultado_exclusao['sucesso']:
                                st.success(f"✅ Fechamento de {mes_ano} excluído!")
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao excluir: {resultado_exclusao['erro']}")
            
            else:
                st.error(f"❌ Erro no cálculo: {resultado_calculado['erro']}")
        
        else:
            st.info(f"ℹ️ Nenhum dado encontrado para {mes_ano}")
    
    with tab2:
        st.header("📊 Resultados Salvos")
        
        if not resultados_salvos.empty:
            # Filtros
            col1, col2 = st.columns(2)
            
            with col1:
                anos_disponiveis = sorted(list(set(resultados_salvos['Mes_Ano'].str.split('/').str[1])), reverse=True)
                ano_filtro = st.selectbox("Filtrar por Ano", ["Todos"] + anos_disponiveis)
            
            with col2:
                ordenacao = st.selectbox("Ordenar por", ["Mais Recente", "Mais Antigo", "Maior Resultado", "Menor Resultado"])
            
            # Aplicar filtros
            df_filtrado = resultados_salvos.copy()
            
            if ano_filtro != "Todos":
                df_filtrado = df_filtrado[df_filtrado['Mes_Ano'].str.endswith(f"/{ano_filtro}")]
            
            # Aplicar ordenação
            if ordenacao == "Mais Recente":
                df_filtrado['Data_Ord'] = pd.to_datetime(df_filtrado['Mes_Ano'], format='%m/%Y')
                df_filtrado = df_filtrado.sort_values('Data_Ord', ascending=False)
            elif ordenacao == "Mais Antigo":
                df_filtrado['Data_Ord'] = pd.to_datetime(df_filtrado['Mes_Ano'], format='%m/%Y')
                df_filtrado = df_filtrado.sort_values('Data_Ord', ascending=True)
            elif ordenacao == "Maior Resultado":
                df_filtrado = df_filtrado.sort_values('Resultado_Liquido', ascending=False)
            elif ordenacao == "Menor Resultado":
                df_filtrado = df_filtrado.sort_values('Resultado_Liquido', ascending=True)
            
            # Exibir resultados
            for _, resultado in df_filtrado.iterrows():
                mes_ano = resultado['Mes_Ano']
                
                with st.expander(f"📅 {mes_ano} - R$ {resultado['Resultado_Liquido']:,.2f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**💰 Receitas e Resultados**")
                        st.write(f"Receita Bruta: R$ {resultado['Receita_Bruta']:,.2f}")
                        st.write(f"Resultado Bruto: R$ {resultado['Resultado_Bruto']:,.2f}")
                        st.write(f"Resultado Líquido: R$ {resultado['Resultado_Liquido']:,.2f}")
                        
                        if resultado['Observacoes']:
                            st.markdown("**📝 Observações**")
                            st.write(resultado['Observacoes'])
                    
                    with col2:
                        st.markdown("**📋 Despesas Operacionais**")
                        st.write(f"🏠 Aluguel: R$ {resultado['Aluguel']:,.2f}")
                        st.write(f"⚡ Luz: R$ {resultado['Luz']:,.2f}")
                        st.write(f"🏥 Fisioterapeutas: R$ {resultado['Fisioterapeutas']:,.2f}")
                        st.write(f"🧹 Limpeza: R$ {resultado['Limpeza']:,.2f}")
                        st.write(f"📦 Diversos: R$ {resultado['Diversos']:,.2f}")
                        st.write(f"💸 Retirada: R$ {resultado['Retirada']:,.2f}")
                        
                        st.markdown("**📅 Fechamento**")
                        st.write(f"Data: {resultado['Data_Fechamento']}")
            
            # Resumo geral
            st.markdown("---")
            st.subheader("📊 Resumo Geral")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_receita = df_filtrado['Receita_Bruta'].sum()
                st.metric("💰 Receita Total", f"R$ {total_receita:,.2f}")
            
            with col2:
                total_operacionais = df_filtrado['Total_Operacionais'].sum()
                st.metric("📋 Despesas Operacionais", f"R$ {total_operacionais:,.2f}")
            
            with col3:
                total_retirada = df_filtrado['Retirada'].sum()
                st.metric("💸 Total Retiradas", f"R$ {total_retirada:,.2f}")
            
            with col4:
                resultado_total = df_filtrado['Resultado_Liquido'].sum()
                st.metric("🎯 Resultado Total", f"R$ {resultado_total:,.2f}")
        
        else:
            st.info("ℹ️ Nenhum resultado salvo ainda. Realize fechamentos na aba 'Novo Fechamento'.")
    
    with tab3:
        st.header("📈 Análise Anual")
        
        if not resultados_salvos.empty:
            # Seleção do ano
            anos_disponiveis = sorted(list(set(resultados_salvos['Mes_Ano'].str.split('/').str[1])), reverse=True)
            ano_analise = st.selectbox("Selecione o Ano para Análise", anos_disponiveis)
            
            # Obter resumo anual
            resumo_anual = gerenciador_resultado.obter_resumo_anual(ano_analise)
            
            st.subheader(f"📊 Resumo de {ano_analise}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📅 Meses Fechados", f"{resumo_anual['meses_fechados']}/12")
            
            with col2:
                st.metric("💰 Receita Anual", f"R$ {resumo_anual['receita_bruta_total']:,.2f}")
            
            with col3:
                st.metric("📋 Despesas Anuais", f"R$ {resumo_anual['despesas_operacionais_total']:,.2f}")
            
            with col4:
                st.metric("🎯 Resultado Anual", f"R$ {resumo_anual['resultado_liquido_total']:,.2f}")
            
            # Gráfico mensal (se houver dados)
            if resumo_anual['meses_fechados'] > 0:
                dados_ano = resultados_salvos[resultados_salvos['Mes_Ano'].str.endswith(f"/{ano_analise}")].copy()
                dados_ano['Mes_Num'] = dados_ano['Mes_Ano'].str.split('/').str[0].astype(int)
                dados_ano = dados_ano.sort_values('Mes_Num')
                
                st.subheader("📈 Evolução Mensal")
                
                # Gráfico de linha
                st.line_chart(
                    dados_ano.set_index('Mes_Ano')[['Receita_Bruta', 'Total_Operacionais', 'Resultado_Liquido']],
                    use_container_width=True
                )
                
                # Tabela detalhada
                st.subheader("📋 Detalhamento Mensal")
                
                colunas_exibir = ['Mes_Ano', 'Receita_Bruta', 'Total_Operacionais', 'Retirada', 'Resultado_Liquido']
                st.dataframe(
                    dados_ano[colunas_exibir].round(2),
                    use_container_width=True,
                    hide_index=True
                )
        
        else:
            st.info("ℹ️ Nenhum dado disponível para análise anual.")

# Teste da página
if __name__ == "__main__":
    pagina_resultado()
