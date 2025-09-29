import pandas as pd
import os
from datetime import datetime
import json

class GerenciadorPersistencia:
    """
    Gerencia a persistência de dados de despesas e configurações
    do sistema de extração bancária.
    """
    
    def __init__(self, diretorio_dados='dados_persistentes'):
        self.diretorio_dados = diretorio_dados
        self.arquivo_despesas = os.path.join(diretorio_dados, 'despesas.csv')
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
            df_vazio = pd.DataFrame(columns=[
                'Data', 'Descricao', 'Valor', 'Razao_Social_Original', 
                'Data_Processamento', 'Arquivo_Origem'
            ])
            df_vazio.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
        
        # Inicializar histórico de processamentos
        if not os.path.exists(self.arquivo_historico):
            historico_vazio = {
                'processamentos': [],
                'total_arquivos_processados': 0,
                'total_despesas_salvas': 0
            }
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(historico_vazio, f, indent=2, ensure_ascii=False)
        
        # Inicializar configurações
        if not os.path.exists(self.arquivo_config):
            config_padrao = {
                'versao': '1.0',
                'ultima_atualizacao': datetime.now().isoformat(),
                'configuracoes_categorizacao': {
                    'permitir_duplicatas': False,
                    'backup_automatico': True,
                    'max_historico': 100
                }
            }
            with open(self.arquivo_config, 'w', encoding='utf-8') as f:
                json.dump(config_padrao, f, indent=2, ensure_ascii=False)
    
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
            self._registrar_processamento(arquivo_origem, novas_adicionadas, total_final)
            
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
    
    def _registrar_processamento(self, arquivo_origem, novas_despesas, total_despesas):
        """Registra um processamento no histórico."""
        try:
            historico = self.carregar_historico()
            
            novo_processamento = {
                'data_hora': datetime.now().isoformat(),
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
            print(f"Erro ao registrar processamento: {e}")
    
    def carregar_historico(self):
        """Carrega histórico de processamentos."""
        try:
            with open(self.arquivo_historico, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            return {'processamentos': [], 'total_arquivos_processados': 0, 'total_despesas_salvas': 0}
    
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
    
    def limpar_dados(self, confirmar=False):
        """
        Limpa todos os dados persistentes (usar com cuidado).
        
        Args:
            confirmar (bool): Deve ser True para confirmar a operação
        """
        if not confirmar:
            return {'sucesso': False, 'erro': 'Operação não confirmada'}
        
        try:
            # Fazer backup antes de limpar
            backup_result = self.fazer_backup()
            
            # Reinicializar arquivos
            self._inicializar_arquivos()
            
            return {
                'sucesso': True,
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
    print("=== TESTE DO GERENCIADOR DE PERSISTÊNCIA ===")
    
    gerenciador = GerenciadorPersistencia()
    
    # Dados de teste
    dados_teste = pd.DataFrame([
        {'Data': '15/09/2025', 'Descricao': 'Limpeza', 'Valor': 346.00, 'Razao_Social_Original': 'GISELE CRISTINA DA SILVA', 'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')},
        {'Data': '10/09/2025', 'Descricao': 'Luz', 'Valor': 133.45, 'Razao_Social_Original': 'LIGHT SERVICOS', 'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    ])
    
    # Salvar dados
    resultado = gerenciador.salvar_despesas(dados_teste, 'teste.ofx')
    print(f"Salvamento: {resultado}")
    
    # Carregar e mostrar resumo
    resumo = gerenciador.obter_resumo_despesas()
    print(f"\\nResumo: {resumo}")
    
    print("\\nTeste concluído!")
