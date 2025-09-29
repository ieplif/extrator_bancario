import pandas as pd
import os
from datetime import datetime
import json
from gerenciador_persistencia_unificado import GerenciadorPersistencia

class GerenciadorReceitasSimples(GerenciadorPersistencia):
    """
    Gerencia a persistência de dados de receitas com estrutura simples:
    - Paciente: Nome do paciente
    - Fonte_Pagamento: Como foi pago (Cartão de Crédito, Particular, etc.)
    """
    
    def __init__(self, diretorio_dados='dados_persistentes'):
        super().__init__(diretorio_dados)
        
        # Arquivo específico para receitas
        self.arquivo_receitas = os.path.join(diretorio_dados, 'receitas_simples.csv')
        
        # Inicializar arquivo específico
        self._inicializar_arquivo_receitas()
    
    def _inicializar_arquivo_receitas(self):
        """Inicializa arquivo específico de receitas."""
        
        if not os.path.exists(self.arquivo_receitas):
            df_vazio = pd.DataFrame(columns=[
                'Data', 'Razao_Social_Original', 'Razao_Social_Limpa', 'Valor',
                'Paciente', 'Fonte_Pagamento', 'Tipo_Preenchimento',
                'Requer_Preenchimento_Manual', 'Motivo_Categorizacao',
                'Data_Processamento', 'Arquivo_Origem'
            ])
            df_vazio.to_csv(self.arquivo_receitas, index=False, encoding='utf-8')
    
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
    
    def atualizar_receita(self, index, paciente=None, fonte_pagamento=None):
        """
        Atualiza campos de uma receita específica.
        
        Args:
            index (int): Índice da receita no DataFrame
            paciente (str, optional): Novo nome do paciente
            fonte_pagamento (str, optional): Nova fonte de pagamento
            
        Returns:
            dict: Resultado da operação
        """
        try:
            receitas = self.carregar_receitas()
            
            if receitas.empty or index >= len(receitas):
                return {'sucesso': False, 'erro': 'Receita não encontrada'}
            
            # Atualizar campos se fornecidos
            if paciente is not None:
                receitas.loc[index, 'Paciente'] = paciente
                # Se preencheu paciente, não requer mais preenchimento manual
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
                    'paciente': receitas.loc[index, 'Paciente'],
                    'fonte_pagamento': receitas.loc[index, 'Fonte_Pagamento'],
                    'valor': receitas.loc[index, 'Valor']
                }
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
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
            
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao registrar processamento de receitas: {e}")

# Teste do sistema
if __name__ == "__main__":
    print("=== TESTE DO GERENCIADOR DE RECEITAS SIMPLES ===")
    
    gerenciador = GerenciadorReceitasSimples()
    
    # Dados de teste
    dados_teste = pd.DataFrame([
        {
            'Data': '15/09/2025', 'Razao_Social_Original': 'REDECARD S A', 'Razao_Social_Limpa': 'REDECARD S A',
            'Valor': 1500.00, 'Paciente': '', 'Fonte_Pagamento': 'Cartão de Crédito',
            'Tipo_Preenchimento': 'cartao_credito', 'Requer_Preenchimento_Manual': True,
            'Motivo_Categorizacao': 'Cartão de crédito identificado',
            'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        },
        {
            'Data': '16/09/2025', 'Razao_Social_Original': 'MARIA SILVA SANTOS', 'Razao_Social_Limpa': 'MARIA SILVA SANTOS',
            'Valor': 800.00, 'Paciente': 'MARIA SILVA SANTOS', 'Fonte_Pagamento': 'Particular',
            'Tipo_Preenchimento': 'automatico', 'Requer_Preenchimento_Manual': False,
            'Motivo_Categorizacao': 'Preenchimento automático - paciente identificado',
            'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
    ])
    
    # Salvar dados
    resultado = gerenciador.salvar_receitas(dados_teste, 'teste_receitas_simples.ofx')
    print(f"Salvamento: {resultado}")
    
    # Carregar e mostrar resumo
    resumo = gerenciador.obter_resumo_receitas()
    print(f"\\nResumo: Total de receitas: {resumo['total_receitas']}")
    print(f"Valor total: R$ {resumo['valor_total']:,.2f}")
    print(f"Preenchimento manual: {resumo['preenchimento']['manual']}")
    print(f"Preenchimento automático: {resumo['preenchimento']['automatico']}")
    
    # Testar atualização
    resultado_atualizacao = gerenciador.atualizar_receita_por_dados(
        '15/09/2025', 'REDECARD S A', 1500.00, 
        paciente='JOÃO SILVA'
    )
    print(f"\\nAtualização: {resultado_atualizacao}")
    
    print("\\nTeste concluído!")
