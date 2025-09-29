import pandas as pd
from datetime import datetime

class CategorizadorReceitasSimples:
    """
    Categoriza receitas (créditos) com lógica simples usando duas colunas:
    - Paciente: Nome do paciente (preenchido automaticamente ou manual)
    - Fonte de Pagamento: Como foi pago (Cartão de Crédito, Particular, etc.)
    """
    
    def __init__(self):
        self.receitas = []
        
        # Regras específicas para Fonte de Pagamento
        self.regras_fonte_pagamento = {
            'REDECARD': 'Cartão de Crédito'
        }
        
        # Lista de razões sociais que devem ficar com campos vazios para preenchimento manual
        # EDITÁVEL: Adicione ou remova nomes conforme necessário
        self.razoes_preenchimento_manual = [
            'ALESSANDRA CRISTINE VAZ SANTOS',
            'KAREN SILVA DE MELO', 
            'KARLOS ALEXANDRE OLIVEIRA',
            'CARLOS HENRIQUE FRANGO',
            'FELIPE CUNHA MATOS',
            'MATHEUS SILVA BERNARDES',
            'SOLUÇÃO ELETRONICA MOTO PEÇA',
            'LMCC DA COSTA LUANA',
            'GPBR PARTICIPACOES LTDA'
        ]
        
        # Estatísticas do processamento
        self.estatisticas = {
            'total_creditos': 0,
            'cartao_credito': 0,
            'preenchimento_manual': 0,
            'preenchimento_automatico': 0
        }
    
    def _limpar_razao_social(self, razao_social):
        """
        Limpa e padroniza a razão social.
        
        Args:
            razao_social (str): Razão social original
            
        Returns:
            str: Razão social limpa
        """
        if not razao_social:
            return ""
        
        # Converter para maiúsculo e remover espaços extras
        razao_limpa = str(razao_social).upper().strip()
        
        # Remover espaços múltiplos
        import re
        razao_limpa = re.sub(r'\s+', ' ', razao_limpa)
        
        return razao_limpa
    
    def _aplicar_regras_categorizacao(self, razao_social_limpa):
        """
        Aplica as regras de categorização para determinar Paciente e Fonte de Pagamento.
        
        Args:
            razao_social_limpa (str): Razão social limpa
            
        Returns:
            dict: Resultado da categorização
        """
        # Verificar se é cartão de crédito (REDECARD)
        if 'REDECARD' in razao_social_limpa:
            return {
                'paciente': '',  # Vazio para preenchimento manual
                'fonte_pagamento': 'Cartão de Crédito',
                'tipo_preenchimento': 'cartao_credito',
                'requer_preenchimento_manual': True,
                'motivo': 'Cartão de crédito identificado'
            }
        
        # Verificar se está na lista de preenchimento manual
        for razao_manual in self.razoes_preenchimento_manual:
            if razao_manual in razao_social_limpa:
                return {
                    'paciente': '',  # Vazio para preenchimento manual
                    'fonte_pagamento': '',  # Vazio para preenchimento manual
                    'tipo_preenchimento': 'manual',
                    'requer_preenchimento_manual': True,
                    'motivo': f'Razão social na lista de preenchimento manual: {razao_manual}'
                }
        
        # Caso padrão: Razão Social vira Paciente automaticamente
        return {
            'paciente': razao_social_limpa,  # Preenchimento automático
            'fonte_pagamento': 'Particular',  # Padrão para pacientes
            'tipo_preenchimento': 'automatico',
            'requer_preenchimento_manual': False,
            'motivo': 'Preenchimento automático - paciente identificado'
        }
    
    def processar_creditos(self, transacoes):
        """
        Processa e categoriza todas as receitas (créditos) das transações.
        
        Args:
            transacoes (list): Lista de transações do extrator OFX
            
        Returns:
            pd.DataFrame: DataFrame com receitas categorizadas
        """
        receitas_categorizadas = []
        
        # Filtrar apenas créditos (valores positivos)
        creditos = [t for t in transacoes if t['Valor'] > 0]
        
        # Resetar estatísticas
        self.estatisticas = {
            'total_creditos': 0,
            'cartao_credito': 0,
            'preenchimento_manual': 0,
            'preenchimento_automatico': 0
        }
        
        for transacao in creditos:
            # Extrair dados básicos
            data = transacao['Data']
            razao_social_original = transacao.get('Razao Social', '')
            valor = transacao['Valor']
            
            # Limpar razão social
            razao_social_limpa = self._limpar_razao_social(razao_social_original)
            
            # Aplicar regras de categorização
            resultado_categorizacao = self._aplicar_regras_categorizacao(razao_social_limpa)
            
            # Criar registro da receita
            receita = {
                'Data': data,
                'Razao_Social_Original': razao_social_original,
                'Razao_Social_Limpa': razao_social_limpa,
                'Valor': valor,
                'Paciente': resultado_categorizacao['paciente'],
                'Fonte_Pagamento': resultado_categorizacao['fonte_pagamento'],
                'Tipo_Preenchimento': resultado_categorizacao['tipo_preenchimento'],
                'Requer_Preenchimento_Manual': resultado_categorizacao['requer_preenchimento_manual'],
                'Motivo_Categorizacao': resultado_categorizacao['motivo'],
                'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
            receitas_categorizadas.append(receita)
            
            # Atualizar estatísticas
            self.estatisticas['total_creditos'] += 1
            
            if resultado_categorizacao['tipo_preenchimento'] == 'cartao_credito':
                self.estatisticas['cartao_credito'] += 1
            elif resultado_categorizacao['tipo_preenchimento'] == 'manual':
                self.estatisticas['preenchimento_manual'] += 1
            elif resultado_categorizacao['tipo_preenchimento'] == 'automatico':
                self.estatisticas['preenchimento_automatico'] += 1
        
        # Converter para DataFrame
        df_receitas = pd.DataFrame(receitas_categorizadas)
        
        return df_receitas
    
    def obter_estatisticas(self):
        """
        Obtém estatísticas do processamento.
        
        Returns:
            dict: Estatísticas detalhadas
        """
        return self.estatisticas.copy()
    
    def obter_receitas_preenchimento_manual(self, df_receitas):
        """
        Obtém receitas que requerem preenchimento manual.
        
        Args:
            df_receitas (pd.DataFrame): DataFrame com receitas categorizadas
            
        Returns:
            pd.DataFrame: Receitas que requerem preenchimento manual
        """
        return df_receitas[df_receitas['Requer_Preenchimento_Manual'] == True].copy()
    
    def obter_receitas_por_fonte(self, df_receitas):
        """
        Agrupa receitas por fonte de pagamento.
        
        Args:
            df_receitas (pd.DataFrame): DataFrame com receitas categorizadas
            
        Returns:
            dict: Resumo por fonte de pagamento
        """
        if df_receitas.empty:
            return {}
        
        # Filtrar apenas receitas com fonte de pagamento preenchida
        receitas_com_fonte = df_receitas[df_receitas['Fonte_Pagamento'] != '']
        
        if receitas_com_fonte.empty:
            return {}
        
        resumo_fonte = receitas_com_fonte.groupby('Fonte_Pagamento').agg({
            'Valor': ['sum', 'count', 'mean'],
            'Data': ['min', 'max']
        }).round(2)
        
        resultado = {}
        for fonte in resumo_fonte.index:
            resultado[fonte] = {
                'total': resumo_fonte.loc[fonte, ('Valor', 'sum')],
                'quantidade': resumo_fonte.loc[fonte, ('Valor', 'count')],
                'media': resumo_fonte.loc[fonte, ('Valor', 'mean')],
                'primeira_data': resumo_fonte.loc[fonte, ('Data', 'min')],
                'ultima_data': resumo_fonte.loc[fonte, ('Data', 'max')]
            }
        
        return resultado
    
    def obter_receitas_por_paciente(self, df_receitas):
        """
        Agrupa receitas por paciente.
        
        Args:
            df_receitas (pd.DataFrame): DataFrame com receitas categorizadas
            
        Returns:
            dict: Resumo por paciente
        """
        if df_receitas.empty:
            return {}
        
        # Filtrar apenas receitas com paciente preenchido
        receitas_com_paciente = df_receitas[df_receitas['Paciente'] != '']
        
        if receitas_com_paciente.empty:
            return {}
        
        resumo_paciente = receitas_com_paciente.groupby('Paciente').agg({
            'Valor': ['sum', 'count', 'mean'],
            'Data': ['min', 'max']
        }).round(2)
        
        resultado = {}
        for paciente in resumo_paciente.index:
            resultado[paciente] = {
                'total': resumo_paciente.loc[paciente, ('Valor', 'sum')],
                'quantidade': resumo_paciente.loc[paciente, ('Valor', 'count')],
                'media': resumo_paciente.loc[paciente, ('Valor', 'mean')],
                'primeira_data': resumo_paciente.loc[paciente, ('Data', 'min')],
                'ultima_data': resumo_paciente.loc[paciente, ('Data', 'max')]
            }
        
        return resultado
    
    def adicionar_razao_preenchimento_manual(self, nova_razao):
        """
        Adiciona uma nova razão social à lista de preenchimento manual.
        
        Args:
            nova_razao (str): Nova razão social para preenchimento manual
        """
        razao_limpa = self._limpar_razao_social(nova_razao)
        if razao_limpa and razao_limpa not in self.razoes_preenchimento_manual:
            self.razoes_preenchimento_manual.append(razao_limpa)
    
    def remover_razao_preenchimento_manual(self, razao_remover):
        """
        Remove uma razão social da lista de preenchimento manual.
        
        Args:
            razao_remover (str): Razão social para remover
        """
        razao_limpa = self._limpar_razao_social(razao_remover)
        if razao_limpa in self.razoes_preenchimento_manual:
            self.razoes_preenchimento_manual.remove(razao_limpa)
    
    def listar_razoes_preenchimento_manual(self):
        """
        Lista todas as razões sociais configuradas para preenchimento manual.
        
        Returns:
            list: Lista de razões sociais
        """
        return self.razoes_preenchimento_manual.copy()

# Teste do sistema
if __name__ == "__main__":
    print("=== TESTE DO CATEGORIZADOR DE RECEITAS SIMPLES ===")
    
    # Dados de teste simulando créditos
    transacoes_teste = [
        {'Data': '15/09/2025', 'Valor': 1500.00, 'Razao Social': 'REDECARD S A'},
        {'Data': '16/09/2025', 'Valor': 800.00, 'Razao Social': 'MARIA SILVA SANTOS'},
        {'Data': '17/09/2025', 'Valor': 1200.00, 'Razao Social': 'ALESSANDRA CRISTINE VAZ SANTOS'},
        {'Data': '18/09/2025', 'Valor': 2000.00, 'Razao Social': 'JOAO PEREIRA OLIVEIRA'},
        {'Data': '19/09/2025', 'Valor': 600.00, 'Razao Social': 'KAREN SILVA DE MELO'},
        {'Data': '20/09/2025', 'Valor': 900.00, 'Razao Social': 'ANA COSTA RIBEIRO'},
    ]
    
    categorizador = CategorizadorReceitasSimples()
    receitas = categorizador.processar_creditos(transacoes_teste)
    
    print(f"Total de créditos processados: {len(receitas)}")
    print("\nReceitas categorizadas:")
    print(receitas[['Data', 'Paciente', 'Fonte_Pagamento', 'Valor', 'Tipo_Preenchimento']].to_string(index=False))
    
    print("\n=== ESTATÍSTICAS ===")
    stats = categorizador.obter_estatisticas()
    print(f"Total de créditos: {stats['total_creditos']}")
    print(f"Cartão de crédito: {stats['cartao_credito']}")
    print(f"Preenchimento manual: {stats['preenchimento_manual']}")
    print(f"Preenchimento automático: {stats['preenchimento_automatico']}")
    
    print("\n=== RECEITAS POR FONTE DE PAGAMENTO ===")
    por_fonte = categorizador.obter_receitas_por_fonte(receitas)
    for fonte, dados in por_fonte.items():
        print(f"{fonte}: R$ {dados['total']:,.2f} ({dados['quantidade']} transações)")
    
    print("\n=== RECEITAS POR PACIENTE ===")
    por_paciente = categorizador.obter_receitas_por_paciente(receitas)
    for paciente, dados in por_paciente.items():
        print(f"{paciente}: R$ {dados['total']:,.2f} ({dados['quantidade']} transações)")
    
    print("\n=== RECEITAS PARA PREENCHIMENTO MANUAL ===")
    manuais = categorizador.obter_receitas_preenchimento_manual(receitas)
    print(f"Total para preenchimento manual: {len(manuais)}")
    for _, receita in manuais.iterrows():
        print(f"- {receita['Razao_Social_Original']}: R$ {receita['Valor']:,.2f} ({receita['Motivo_Categorizacao']})")
    
    print("\nTeste concluído!")
