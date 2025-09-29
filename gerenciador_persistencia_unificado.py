import pandas as pd
import os
from datetime import datetime
import json

class GerenciadorPersistenciaUnificado:
    """
    Gerencia a persistência de dados de despesas, receitas e configurações
    do sistema de extração bancária de forma unificada.
    """
    
    def __init__(self, diretorio_dados='dados_persistentes'):
        self.diretorio_dados = diretorio_dados
        
        # Arquivos de dados
        self.arquivo_despesas = os.path.join(diretorio_dados, 'despesas.csv')
        self.arquivo_receitas = os.path.join(diretorio_dados, 'receitas_simples.csv')
        
        # Arquivos de controle
        self.arquivo_historico = os.path.join(diretorio_dados, 'historico_processamentos.json')
        self.arquivo_config = os.path.join(diretorio_dados, 'configuracoes.json')
        
        # Criar diretório se não existir
        os.makedirs(diretorio_dados, exist_ok=True)
        
        # Inicializar arquivos se não existirem
        self._inicializar_arquivos()
    
    def _inicializar_arquivos(self):
        """Inicializa arquivos de dados se não existirem."""
        
        # Inicializar arquivo de despesas
        if not os.path.exists(self.arquivo_despesas):
            df_despesas_vazio = pd.DataFrame(columns=[
                'Data', 'Descricao', 'Valor', 'Razao_Social_Original', 
                'Data_Processamento', 'Arquivo_Origem'
            ])
            df_despesas_vazio.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
        
        # Inicializar arquivo de receitas
        if not os.path.exists(self.arquivo_receitas):
            df_receitas_vazio = pd.DataFrame(columns=[
                'Data', 'Razao_Social_Original', 'Razao_Social_Limpa', 'Valor',
                'Paciente', 'Fonte_Pagamento', 'Tipo_Preenchimento',
                'Requer_Preenchimento_Manual', 'Motivo_Categorizacao',
                'Data_Processamento', 'Arquivo_Origem'
            ])
            df_receitas_vazio.to_csv(self.arquivo_receitas, index=False, encoding='utf-8')
        
        # Inicializar histórico de processamentos
        if not os.path.exists(self.arquivo_historico):
            historico_vazio = {
                'processamentos': [],
                'total_arquivos_processados': 0,
                'total_despesas_salvas': 0,
                'total_receitas_salvas': 0
            }
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(historico_vazio, f, indent=2, ensure_ascii=False)
        
        # Inicializar configurações
        if not os.path.exists(self.arquivo_config):
            config_padrao = {
                'versao': '2.0',
                'ultima_atualizacao': datetime.now().isoformat(),
                'configuracoes_categorizacao': {
                    'permitir_duplicatas': False,
                    'backup_automatico': True,
                    'max_historico': 100
                },
                'configuracoes_despesas': {
                    'categorias_ativas': True,
                    'filtros_automaticos': True
                },
                'configuracoes_receitas': {
                    'preenchimento_manual': True,
                    'identificacao_automatica': True
                }
            }
            with open(self.arquivo_config, 'w', encoding='utf-8') as f:
                json.dump(config_padrao, f, indent=2, ensure_ascii=False)
    
    # ==================== MÉTODOS PARA DESPESAS ====================
    
    def salvar_despesas(self, novas_despesas, arquivo_origem='manual', modo='adicionar'):
        """
        Salva despesas na tabela persistente.
        
        Args:
            novas_despesas (pd.DataFrame): Novas despesas
            arquivo_origem (str): Nome do arquivo OFX de origem
            modo (str): 'adicionar' ou 'sobrescrever'
            
        Returns:
            dict: Resultado da operação
        """
        try:
            # Adicionar informações de origem
            novas_despesas = novas_despesas.copy()
            novas_despesas['Arquivo_Origem'] = arquivo_origem
            
            if modo == 'sobrescrever':
                # Sobrescrever arquivo
                novas_despesas.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
                total_final = len(novas_despesas)
                novas_adicionadas = len(novas_despesas)
            else:
                # Adicionar às existentes
                despesas_existentes = self.carregar_despesas()
                
                # Verificar duplicatas (opcional)
                config = self.carregar_configuracoes()
                if not config.get('configuracoes_categorizacao', {}).get('permitir_duplicatas', False):
                    # Remover possíveis duplicatas baseadas em Data, Valor e Razão Social
                    chaves_duplicata = ['Data', 'Valor', 'Razao_Social_Original']
                    
                    if not despesas_existentes.empty:
                        # Marcar duplicatas
                        merged = pd.merge(
                            novas_despesas, 
                            despesas_existentes[chaves_duplicata], 
                            on=chaves_duplicata, 
                            how='left', 
                            indicator=True
                        )
                        novas_despesas = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
                
                # Combinar dados
                if despesas_existentes.empty:
                    todas_despesas = novas_despesas
                else:
                    todas_despesas = pd.concat([despesas_existentes, novas_despesas], ignore_index=True)
                
                # Salvar
                todas_despesas.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
                total_final = len(todas_despesas)
                novas_adicionadas = len(novas_despesas)
            
            # Registrar no histórico
            self._registrar_processamento_despesas(arquivo_origem, novas_adicionadas, total_final)
            
            return {
                'sucesso': True,
                'novas_despesas': novas_adicionadas,
                'total_despesas': total_final,
                'modo': modo,
                'arquivo_origem': arquivo_origem
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'novas_despesas': 0,
                'total_despesas': 0
            }
    
    def carregar_despesas(self):
        """
        Carrega todas as despesas salvas.
        
        Returns:
            pd.DataFrame: DataFrame com todas as despesas
        """
        try:
            if os.path.exists(self.arquivo_despesas):
                return pd.read_csv(self.arquivo_despesas, encoding='utf-8')
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Erro ao carregar despesas: {e}")
            return pd.DataFrame()
    
    def obter_resumo_despesas(self):
        """
        Gera resumo completo das despesas salvas.
        
        Returns:
            dict: Resumo das despesas
        """
        despesas = self.carregar_despesas()
        
        if despesas.empty:
            return {
                'total_despesas': 0,
                'valor_total': 0,
                'por_categoria': {},
                'por_mes': {},
                'periodo': None
            }
        
        # Converter Data para datetime
        despesas['Data_dt'] = pd.to_datetime(despesas['Data'], format='%d/%m/%Y')
        
        # Resumo geral
        resumo = {
            'total_despesas': len(despesas),
            'valor_total': despesas['Valor'].sum(),
            'periodo': {
                'inicio': despesas['Data_dt'].min().strftime('%d/%m/%Y'),
                'fim': despesas['Data_dt'].max().strftime('%d/%m/%Y')
            }
        }
        
        # Por categoria
        por_categoria = despesas.groupby('Descricao').agg({
            'Valor': ['sum', 'count', 'mean'],
            'Data_dt': ['min', 'max']
        }).round(2)
        
        resumo['por_categoria'] = {}
        for categoria in por_categoria.index:
            resumo['por_categoria'][categoria] = {
                'total': por_categoria.loc[categoria, ('Valor', 'sum')],
                'quantidade': por_categoria.loc[categoria, ('Valor', 'count')],
                'media': por_categoria.loc[categoria, ('Valor', 'mean')],
                'primeira_data': por_categoria.loc[categoria, ('Data_dt', 'min')].strftime('%d/%m/%Y'),
                'ultima_data': por_categoria.loc[categoria, ('Data_dt', 'max')].strftime('%d/%m/%Y')
            }
        
        # Por mês
        despesas['Mes_Ano'] = despesas['Data_dt'].dt.strftime('%m/%Y')
        por_mes = despesas.groupby('Mes_Ano')['Valor'].agg(['sum', 'count']).round(2)
        
        resumo['por_mes'] = {}
        for mes in por_mes.index:
            resumo['por_mes'][mes] = {
                'total': por_mes.loc[mes, 'sum'],
                'quantidade': por_mes.loc[mes, 'count']
            }
        
        return resumo
    
    # ==================== MÉTODOS PARA RECEITAS ====================
    
    def salvar_receitas(self, novas_receitas, arquivo_origem='manual', modo='adicionar'):
        """
        Salva receitas na tabela persistente.
        
        Args:
            novas_receitas (pd.DataFrame): Novas receitas
            arquivo_origem (str): Nome do arquivo OFX de origem
            modo (str): 'adicionar' ou 'sobrescrever'
            
        Returns:
            dict: Resultado da operação
        """
        try:
            # Adicionar informações de origem
            novas_receitas = novas_receitas.copy()
            novas_receitas['Arquivo_Origem'] = arquivo_origem
            
            if modo == 'sobrescrever':
                # Sobrescrever arquivo
                novas_receitas.to_csv(self.arquivo_receitas, index=False, encoding='utf-8')
                total_final = len(novas_receitas)
                novas_adicionadas = len(novas_receitas)
            else:
                # Adicionar às existentes
                receitas_existentes = self.carregar_receitas()
                
                # Verificar duplicatas
                config = self.carregar_configuracoes()
                if not config.get('configuracoes_categorizacao', {}).get('permitir_duplicatas', False):
                    chaves_duplicata = ['Data', 'Valor', 'Razao_Social_Original']
                    
                    if not receitas_existentes.empty:
                        merged = pd.merge(
                            novas_receitas, 
                            receitas_existentes[chaves_duplicata], 
                            on=chaves_duplicata, 
                            how='left', 
                            indicator=True
                        )
                        novas_receitas = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
                
                # Combinar dados
                if receitas_existentes.empty:
                    todas_receitas = novas_receitas
                else:
                    todas_receitas = pd.concat([receitas_existentes, novas_receitas], ignore_index=True)
                
                # Salvar
                todas_receitas.to_csv(self.arquivo_receitas, index=False, encoding='utf-8')
                total_final = len(todas_receitas)
                novas_adicionadas = len(novas_receitas)
            
            # Registrar no histórico
            self._registrar_processamento_receitas(arquivo_origem, novas_adicionadas, total_final)
            
            return {
                'sucesso': True,
                'novas_receitas': novas_adicionadas,
                'total_receitas': total_final,
                'modo': modo,
                'arquivo_origem': arquivo_origem,
                'requer_preenchimento_manual': len(novas_receitas[novas_receitas['Requer_Preenchimento_Manual'] == True])
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'novas_receitas': 0,
                'total_receitas': 0
            }
    
    def carregar_receitas(self):
        """
        Carrega todas as receitas salvas.
        
        Returns:
            pd.DataFrame: DataFrame com todas as receitas
        """
        try:
            if os.path.exists(self.arquivo_receitas):
                return pd.read_csv(self.arquivo_receitas, encoding='utf-8')
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Erro ao carregar receitas: {e}")
            return pd.DataFrame()
    
    def obter_resumo_receitas(self):
        """
        Gera resumo completo das receitas salvas.
        
        Returns:
            dict: Resumo das receitas
        """
        receitas = self.carregar_receitas()
        
        if receitas.empty:
            return {
                'total_receitas': 0,
                'valor_total': 0,
                'por_fonte_pagamento': {},
                'por_paciente': {},
                'por_mes': {},
                'periodo': None,
                'preenchimento': {
                    'manual': 0,
                    'automatico': 0,
                    'cartao_credito': 0
                }
            }
        
        # Converter Data para datetime
        receitas['Data_dt'] = pd.to_datetime(receitas['Data'], format='%d/%m/%Y')
        
        # Resumo geral
        resumo = {
            'total_receitas': len(receitas),
            'valor_total': receitas['Valor'].sum(),
            'periodo': {
                'inicio': receitas['Data_dt'].min().strftime('%d/%m/%Y'),
                'fim': receitas['Data_dt'].max().strftime('%d/%m/%Y')
            }
        }
        
        # Por fonte de pagamento
        receitas_com_fonte = receitas[receitas['Fonte_Pagamento'] != '']
        if not receitas_com_fonte.empty:
            por_fonte = receitas_com_fonte.groupby('Fonte_Pagamento').agg({
                'Valor': ['sum', 'count', 'mean'],
                'Data_dt': ['min', 'max']
            }).round(2)
            
            resumo['por_fonte_pagamento'] = {}
            for fonte in por_fonte.index:
                resumo['por_fonte_pagamento'][fonte] = {
                    'total': por_fonte.loc[fonte, ('Valor', 'sum')],
                    'quantidade': por_fonte.loc[fonte, ('Valor', 'count')],
                    'media': por_fonte.loc[fonte, ('Valor', 'mean')],
                    'primeira_data': por_fonte.loc[fonte, ('Data_dt', 'min')].strftime('%d/%m/%Y'),
                    'ultima_data': por_fonte.loc[fonte, ('Data_dt', 'max')].strftime('%d/%m/%Y')
                }
        else:
            resumo['por_fonte_pagamento'] = {}
        
        # Por paciente
        receitas_com_paciente = receitas[receitas['Paciente'] != '']
        if not receitas_com_paciente.empty:
            por_paciente = receitas_com_paciente.groupby('Paciente').agg({
                'Valor': ['sum', 'count', 'mean'],
                'Data_dt': ['min', 'max']
            }).round(2)
            
            resumo['por_paciente'] = {}
            for paciente in por_paciente.index:
                resumo['por_paciente'][paciente] = {
                    'total': por_paciente.loc[paciente, ('Valor', 'sum')],
                    'quantidade': por_paciente.loc[paciente, ('Valor', 'count')],
                    'media': por_paciente.loc[paciente, ('Valor', 'mean')],
                    'primeira_data': por_paciente.loc[paciente, ('Data_dt', 'min')].strftime('%d/%m/%Y'),
                    'ultima_data': por_paciente.loc[paciente, ('Data_dt', 'max')].strftime('%d/%m/%Y')
                }
        else:
            resumo['por_paciente'] = {}
        
        # Por mês
        receitas['Mes_Ano'] = receitas['Data_dt'].dt.strftime('%m/%Y')
        por_mes = receitas.groupby('Mes_Ano')['Valor'].agg(['sum', 'count']).round(2)
        
        resumo['por_mes'] = {}
        for mes in por_mes.index:
            resumo['por_mes'][mes] = {
                'total': por_mes.loc[mes, 'sum'],
                'quantidade': por_mes.loc[mes, 'count']
            }
        
        # Estatísticas de preenchimento
        resumo['preenchimento'] = {
            'manual': len(receitas[receitas['Tipo_Preenchimento'] == 'manual']),
            'automatico': len(receitas[receitas['Tipo_Preenchimento'] == 'automatico']),
            'cartao_credito': len(receitas[receitas['Tipo_Preenchimento'] == 'cartao_credito'])
        }
        
        return resumo
    
    def obter_receitas_preenchimento_manual(self):
        """
        Obtém receitas que requerem preenchimento manual.
        
        Returns:
            pd.DataFrame: Receitas para preenchimento manual
        """
        receitas = self.carregar_receitas()
        
        if receitas.empty:
            return pd.DataFrame()
        
        return receitas[receitas['Requer_Preenchimento_Manual'] == True].copy()
    
    def atualizar_receita_por_dados(self, data, razao_social, valor, paciente=None, fonte_pagamento=None):
        """
        Atualiza receita baseada em data, razão social e valor.
        
        Args:
            data (str): Data da receita
            razao_social (str): Razão social original
            valor (float): Valor da receita
            paciente (str, optional): Novo nome do paciente
            fonte_pagamento (str, optional): Nova fonte de pagamento
            
        Returns:
            dict: Resultado da operação
        """
        try:
            receitas = self.carregar_receitas()
            
            if receitas.empty:
                return {'sucesso': False, 'erro': 'Nenhuma receita encontrada'}
            
            # Encontrar receita correspondente
            mask = (
                (receitas['Data'] == data) &
                (receitas['Razao_Social_Original'] == razao_social) &
                (receitas['Valor'] == valor)
            )
            
            receitas_encontradas = receitas[mask]
            
            if receitas_encontradas.empty:
                return {'sucesso': False, 'erro': 'Receita não encontrada'}
            
            # Atualizar primeira ocorrência
            index = receitas_encontradas.index[0]
            
            if paciente is not None:
                receitas.loc[index, 'Paciente'] = paciente
                if paciente.strip():
                    receitas.loc[index, 'Requer_Preenchimento_Manual'] = False
                    receitas.loc[index, 'Tipo_Preenchimento'] = 'manual_preenchido'
            
            if fonte_pagamento is not None:
                receitas.loc[index, 'Fonte_Pagamento'] = fonte_pagamento
            
            # Salvar
            receitas.to_csv(self.arquivo_receitas, index=False, encoding='utf-8')
            
            return {
                'sucesso': True,
                'receita_atualizada': {
                    'data': data,
                    'razao_social': razao_social,
                    'paciente': receitas.loc[index, 'Paciente'],
                    'fonte_pagamento': receitas.loc[index, 'Fonte_Pagamento'],
                    'valor': valor
                }
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    # ==================== MÉTODOS GERAIS ====================
    
    def obter_resumo_geral(self):
        """
        Gera resumo geral combinando despesas e receitas.
        
        Returns:
            dict: Resumo geral do sistema
        """
        resumo_despesas = self.obter_resumo_despesas()
        resumo_receitas = self.obter_resumo_receitas()
        historico = self.carregar_historico()
        
        return {
            'despesas': resumo_despesas,
            'receitas': resumo_receitas,
            'saldo_liquido': resumo_receitas['valor_total'] - resumo_despesas['valor_total'],
            'historico': {
                'total_arquivos_processados': historico.get('total_arquivos_processados', 0),
                'total_despesas_salvas': historico.get('total_despesas_salvas', 0),
                'total_receitas_salvas': historico.get('total_receitas_salvas', 0)
            }
        }
    
    def _registrar_processamento_despesas(self, arquivo_origem, novas_despesas, total_despesas):
        """Registra processamento de despesas no histórico."""
        try:
            historico = self.carregar_historico()
            
            novo_processamento = {
                'data_hora': datetime.now().isoformat(),
                'tipo': 'despesas',
                'arquivo_origem': arquivo_origem,
                'novas_despesas': novas_despesas,
                'total_despesas_apos': total_despesas
            }
            
            historico['processamentos'].append(novo_processamento)
            historico['total_arquivos_processados'] += 1
            historico['total_despesas_salvas'] = total_despesas
            
            # Manter apenas os últimos N processamentos
            config = self.carregar_configuracoes()
            max_historico = config.get('configuracoes_categorizacao', {}).get('max_historico', 100)
            
            if len(historico['processamentos']) > max_historico:
                historico['processamentos'] = historico['processamentos'][-max_historico:]
            
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao registrar processamento de despesas: {e}")
    
    def _registrar_processamento_receitas(self, arquivo_origem, novas_receitas, total_receitas):
        """Registra processamento de receitas no histórico."""
        try:
            historico = self.carregar_historico()
            
            novo_processamento = {
                'data_hora': datetime.now().isoformat(),
                'tipo': 'receitas_simples',
                'arquivo_origem': arquivo_origem,
                'novas_receitas': novas_receitas,
                'total_receitas_apos': total_receitas
            }
            
            historico['processamentos'].append(novo_processamento)
            historico['total_arquivos_processados'] += 1
            historico['total_receitas_salvas'] = total_receitas
            
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao registrar processamento de receitas: {e}")
    
    def carregar_historico(self):
        """Carrega histórico de processamentos."""
        try:
            with open(self.arquivo_historico, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            return {
                'processamentos': [], 
                'total_arquivos_processados': 0, 
                'total_despesas_salvas': 0,
                'total_receitas_salvas': 0
            }
    
    def carregar_configuracoes(self):
        """Carrega configurações do sistema."""
        try:
            with open(self.arquivo_config, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return {}
    
    def fazer_backup(self):
        """Cria backup dos dados."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.diretorio_dados, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup das despesas
            if os.path.exists(self.arquivo_despesas):
                backup_despesas = os.path.join(backup_dir, f'despesas_backup_{timestamp}.csv')
                pd.read_csv(self.arquivo_despesas).to_csv(backup_despesas, index=False, encoding='utf-8')
            
            # Backup das receitas
            if os.path.exists(self.arquivo_receitas):
                backup_receitas = os.path.join(backup_dir, f'receitas_backup_{timestamp}.csv')
                pd.read_csv(self.arquivo_receitas).to_csv(backup_receitas, index=False, encoding='utf-8')
            
            # Backup do histórico
            if os.path.exists(self.arquivo_historico):
                backup_historico = os.path.join(backup_dir, f'historico_backup_{timestamp}.json')
                with open(self.arquivo_historico, 'r', encoding='utf-8') as origem:
                    with open(backup_historico, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
            
            return {
                'sucesso': True,
                'timestamp': timestamp,
                'diretorio': backup_dir
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def limpar_dados(self, confirmar=False, tipo='todos'):
        """
        Limpa dados persistentes (usar com cuidado).
        
        Args:
            confirmar (bool): Deve ser True para confirmar a operação
            tipo (str): 'todos', 'despesas' ou 'receitas'
        """
        if not confirmar:
            return {'sucesso': False, 'erro': 'Operação não confirmada'}
        
        try:
            # Fazer backup antes de limpar
            backup_result = self.fazer_backup()
            
            if tipo in ['todos', 'despesas']:
                # Reinicializar arquivo de despesas
                df_despesas_vazio = pd.DataFrame(columns=[
                    'Data', 'Descricao', 'Valor', 'Razao_Social_Original', 
                    'Data_Processamento', 'Arquivo_Origem'
                ])
                df_despesas_vazio.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
            
            if tipo in ['todos', 'receitas']:
                # Reinicializar arquivo de receitas
                df_receitas_vazio = pd.DataFrame(columns=[
                    'Data', 'Razao_Social_Original', 'Razao_Social_Limpa', 'Valor',
                    'Paciente', 'Fonte_Pagamento', 'Tipo_Preenchimento',
                    'Requer_Preenchimento_Manual', 'Motivo_Categorizacao',
                    'Data_Processamento', 'Arquivo_Origem'
                ])
                df_receitas_vazio.to_csv(self.arquivo_receitas, index=False, encoding='utf-8')
            
            if tipo == 'todos':
                # Reinicializar histórico
                historico_vazio = {
                    'processamentos': [],
                    'total_arquivos_processados': 0,
                    'total_despesas_salvas': 0,
                    'total_receitas_salvas': 0
                }
                with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                    json.dump(historico_vazio, f, indent=2, ensure_ascii=False)
            
            return {
                'sucesso': True,
                'tipo_limpeza': tipo,
                'backup_criado': backup_result['sucesso'],
                'backup_timestamp': backup_result.get('timestamp', 'N/A')
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }

# Teste do sistema
if __name__ == "__main__":
    print("=== TESTE DO GERENCIADOR DE PERSISTÊNCIA UNIFICADO ===")
    
    gerenciador = GerenciadorPersistenciaUnificado()
    
    # Teste de despesas
    dados_despesas = pd.DataFrame([
        {'Data': '15/09/2025', 'Descricao': 'Limpeza', 'Valor': 346.00, 'Razao_Social_Original': 'GISELE CRISTINA DA SILVA', 'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')},
        {'Data': '10/09/2025', 'Descricao': 'Luz', 'Valor': 133.45, 'Razao_Social_Original': 'LIGHT SERVICOS', 'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    ])
    
    resultado_despesas = gerenciador.salvar_despesas(dados_despesas, 'teste_despesas.ofx')
    print(f"Despesas: {resultado_despesas}")
    
    # Teste de receitas
    dados_receitas = pd.DataFrame([
        {
            'Data': '16/09/2025', 'Razao_Social_Original': 'MARIA SILVA SANTOS', 'Razao_Social_Limpa': 'MARIA SILVA SANTOS',
            'Valor': 800.00, 'Paciente': 'MARIA SILVA SANTOS', 'Fonte_Pagamento': 'Particular',
            'Tipo_Preenchimento': 'automatico', 'Requer_Preenchimento_Manual': False,
            'Motivo_Categorizacao': 'Preenchimento automático - paciente identificado',
            'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
    ])
    
    resultado_receitas = gerenciador.salvar_receitas(dados_receitas, 'teste_receitas.ofx')
    print(f"Receitas: {resultado_receitas}")
    
    # Resumo geral
    resumo_geral = gerenciador.obter_resumo_geral()
    print(f"\\nResumo Geral:")
    print(f"- Despesas: R$ {resumo_geral['despesas']['valor_total']:,.2f}")
    print(f"- Receitas: R$ {resumo_geral['receitas']['valor_total']:,.2f}")
    print(f"- Saldo Líquido: R$ {resumo_geral['saldo_liquido']:,.2f}")
    
    print("\\nTeste concluído!")
