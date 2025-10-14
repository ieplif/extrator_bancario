import re
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
            'GPBR PARTICIPACOES LTDA',
            'PIX QRS NATALIA SIL',
            'ELSON DA SILVA LIMA',
            'RAFAEL GOHN ALVES',
            'RICARDO DA COSTA SILVA',
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
            return ''
        
        # Converter para string e remover espaços extras
        texto = str(razao_social).strip()
        
        # Remover caracteres especiais comuns
        texto = re.sub(r'[^\w\s]', ' ', texto)
        
        # Remover espaços múltiplos
        texto = re.sub(r'\s+', ' ', texto)
        
        # Converter para maiúsculas
        texto = texto.upper()
        
        return texto.strip()
    
    def _aplicar_regras_categorizacao(self, razao_social_limpa):
        """
        Aplica as regras de categorização definidas.
        
        Args:
            razao_social_limpa (str): Razão social limpa
            
        Returns:
            dict: Resultado da categorização
        """
        
        # Regra 1: REDECARD -> Cartão de Crédito
        if 'REDECARD' in razao_social_limpa.upper():
            self.estatisticas['cartao_credito'] += 1
            return {
                'paciente': '',
                'fonte_pagamento': 'Cartão de Crédito',
                'tipo_preenchimento': 'cartao_credito',
                'requer_preenchimento_manual': True,
                'motivo': 'Cartão de crédito - paciente para preenchimento manual'
            }
        
        # Regra 2: Lista específica -> Preenchimento manual (busca flexível)
        razao_upper = razao_social_limpa.upper()
        
        # Mapeamento flexível para busca parcial
        nomes_flexiveis = {
            'FELIPE CUNHA': 'FELIPE CUNHA MATOS',
            'KARLOS ALEXANDRE': 'KARLOS ALEXANDRE OLIVEIRA', 
            'CARLOS HENRIQUE': 'CARLOS HENRIQUE FRANGO',
            'SOLUCAO ELETRONICA': 'SOLUÇÃO ELETRONICA MOTO PEÇA',
            'KAREN SILVA': 'KAREN SILVA DE MELO',
            'MATHEUS SILVA': 'MATHEUS SILVA BERNARDES',
            'LMCC DA COSTA': 'LMCC DA COSTA LUANA',
            'GPBR PARTICIPACOES': 'GPBR PARTICIPACOES LTDA',
            'ALESSANDRA CRISTINE': 'ALESSANDRA CRISTINE VAZ SANTOS',
            'NATALIA SIL': 'PIX QRS NATALIA SIL',
            'ELSON DA SILVA': 'ELSON DA SILVA LIMA',
            'RAFAEL GOHN': 'RAFAEL GOHN ALVES',
            'RICARDO DA COSTA': 'RICARDO DA COSTA SILVA',
        }
        
        for busca, nome_original in nomes_flexiveis.items():
            if busca in razao_upper:
                self.estatisticas['preenchimento_manual'] += 1
                return {
                    'paciente': '',
                    'fonte_pagamento': '',
                    'tipo_preenchimento': 'manual',
                    'requer_preenchimento_manual': True,
                    'motivo': f'Lista específica - {nome_original}'
                }
        
        # Regra 3: Demais -> Preenchimento automático
        self.estatisticas['preenchimento_automatico'] += 1
        return {
            'paciente': razao_social_limpa,
            'fonte_pagamento': 'Particular',
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
            self.estatisticas['total_creditos'] += 1
        
        # Converter para DataFrame
        if receitas_categorizadas:
            df_receitas = pd.DataFrame(receitas_categorizadas)
            self.receitas = receitas_categorizadas
            return df_receitas
        else:
            return pd.DataFrame()
    
    def obter_estatisticas(self):
        """
        Retorna estatísticas do processamento.
        
        Returns:
            dict: Estatísticas detalhadas
        """
        return self.estatisticas.copy()
    
    def obter_resumo_por_tipo(self):
        """
        Gera resumo das receitas por tipo de preenchimento.
        
        Returns:
            dict: Resumo por tipo
        """
        if not self.receitas:
            return {}
        
        df = pd.DataFrame(self.receitas)
        
        resumo = {}
        
        # Agrupar por tipo de preenchimento
        tipos = df.groupby('Tipo_Preenchimento').agg({
            'Valor': ['sum', 'count', 'mean'],
            'Data': ['min', 'max']
        }).round(2)
        
        for tipo in tipos.index:
            resumo[tipo] = {
                'total': tipos.loc[tipo, ('Valor', 'sum')],
                'quantidade': tipos.loc[tipo, ('Valor', 'count')],
                'media': tipos.loc[tipo, ('Valor', 'mean')],
                'primeira_data': tipos.loc[tipo, ('Data', 'min')],
                'ultima_data': tipos.loc[tipo, ('Data', 'max')]
            }
        
        return resumo
    
    def obter_receitas_por_paciente(self):
        """
        Gera resumo das receitas por paciente.
        
        Returns:
            dict: Resumo por paciente
        """
        if not self.receitas:
            return {}
        
        df = pd.DataFrame(self.receitas)
        
        # Filtrar apenas receitas com paciente preenchido
        df_com_paciente = df[df['Paciente'] != '']
        
        if df_com_paciente.empty:
            return {}
        
        resumo = {}
        
        # Agrupar por paciente
        pacientes = df_com_paciente.groupby('Paciente').agg({
            'Valor': ['sum', 'count', 'mean'],
            'Data': ['min', 'max']
        }).round(2)
        
        for paciente in pacientes.index:
            resumo[paciente] = {
                'total': pacientes.loc[paciente, ('Valor', 'sum')],
                'quantidade': pacientes.loc[paciente, ('Valor', 'count')],
                'media': pacientes.loc[paciente, ('Valor', 'mean')],
                'primeira_data': pacientes.loc[paciente, ('Data', 'min')],
                'ultima_data': pacientes.loc[paciente, ('Data', 'max')]
            }
        
        return resumo

    
    def obter_receitas_por_fonte(self):
        """
        Gera resumo das receitas por fonte de pagamento.
        
        Returns:
            dict: Resumo por fonte
        """
        if not self.receitas:
            return {}
        
        df = pd.DataFrame(self.receitas)
        
        # Filtrar apenas receitas com fonte preenchida
        df_com_fonte = df[df['Fonte_Pagamento'] != '']
        
        if df_com_fonte.empty:
            return {}
        
        resumo = {}
        
        # Agrupar por fonte de pagamento
        fontes = df_com_fonte.groupby('Fonte_Pagamento').agg({
            'Valor': ['sum', 'count', 'mean'],
            'Data': ['min', 'max']
        }).round(2)
        
        for fonte in fontes.index:
            resumo[fonte] = {
                'total': fontes.loc[fonte, ('Valor', 'sum')],
                'quantidade': fontes.loc[fonte, ('Valor', 'count')],
                'media': fontes.loc[fonte, ('Valor', 'mean')],
                'primeira_data': fontes.loc[fonte, ('Data', 'min')],
                'ultima_data': fontes.loc[fonte, ('Data', 'max')]
            }
        
        return resumo
    
    def obter_receitas_preenchimento_manual(self):
        """
        Retorna apenas as receitas que requerem preenchimento manual.
        
        Returns:
            pd.DataFrame: Receitas para preenchimento manual
        """
        if not self.receitas:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.receitas)
        return df[df['Requer_Preenchimento_Manual'] == True].copy()
    
    def salvar_csv(self, nome_arquivo='receitas_categorizadas.csv'):
        """
        Salva as receitas categorizadas em arquivo CSV.
        
        Args:
            nome_arquivo (str): Nome do arquivo CSV
            
        Returns:
            bool: True se salvou com sucesso
        """
        if self.receitas:
            df = pd.DataFrame(self.receitas)
            df.to_csv(nome_arquivo, index=False, encoding='utf-8')
            return True
        return False
    
    def exibir_resumo(self):
        """
        Exibe resumo das receitas categorizadas.
        """
        if not self.receitas:
            print("Nenhuma receita processada.")
            return
        
        print("=== RESUMO DAS RECEITAS CATEGORIZADAS ===")
        print(f"Total de créditos processados: {self.estatisticas['total_creditos']}")
        print(f"Cartão de crédito: {self.estatisticas['cartao_credito']}")
        print(f"Preenchimento manual: {self.estatisticas['preenchimento_manual']}")
        print(f"Preenchimento automático: {self.estatisticas['preenchimento_automatico']}")
        
        # Resumo por tipo
        resumo_tipo = self.obter_resumo_por_tipo()
        if resumo_tipo:
            print("\n=== RESUMO POR TIPO DE PREENCHIMENTO ===")
            for tipo, dados in resumo_tipo.items():
                print(f"{tipo.upper()}:")
                print(f"  - Total: R$ {dados['total']:,.2f}")
                print(f"  - Quantidade: {dados['quantidade']}")
                print(f"  - Média: R$ {dados['media']:,.2f}")
        
        # Resumo por fonte
        resumo_fonte = self.obter_receitas_por_fonte()
        if resumo_fonte:
            print("\n=== RESUMO POR FONTE DE PAGAMENTO ===")
            for fonte, dados in resumo_fonte.items():
                print(f"{fonte}:")
                print(f"  - Total: R$ {dados['total']:,.2f}")
                print(f"  - Quantidade: {dados['quantidade']}")
                print(f"  - Média: R$ {dados['media']:,.2f}")

# Teste do sistema
if __name__ == "__main__":
    print("=== TESTE DO CATEGORIZADOR DE RECEITAS SIMPLES ===")
    
    # Dados de teste
    transacoes_teste = [
        {'Data': '15/09/2025', 'Valor': 1500.00, 'Razao Social': 'REDECARD INSTITUICAO DE PAGAMENTO S.A.'},
        {'Data': '16/09/2025', 'Valor': 800.00, 'Razao Social': 'MARIA SILVA SANTOS'},
        {'Data': '17/09/2025', 'Valor': 600.00, 'Razao Social': 'FELIPE CUNHA DE MATTOS'},
        {'Data': '18/09/2025', 'Valor': 450.00, 'Razao Social': 'KARLOS ALEXANDRE V OLIVEIRA'},
        {'Data': '19/09/2025', 'Valor': 300.00, 'Razao Social': 'CARLOS HENRIQUE OLIVEIRA FRANGO DA SILVA'}
    ]
    
    categorizador = CategorizadorReceitasSimples()
    receitas = categorizador.processar_creditos(transacoes_teste)
    
    print(f"Receitas processadas: {len(receitas)}")
    
    if not receitas.empty:
        categorizador.exibir_resumo()
        
        print("\n=== PRIMEIRAS 3 RECEITAS ===")
        for i, (_, receita) in enumerate(receitas.head(3).iterrows()):
            print(f"{i+1}. {receita['Razao_Social_Original']} - R$ {receita['Valor']:,.2f}")
            print(f"   Paciente: \"{receita['Paciente']}\"")
            print(f"   Fonte: \"{receita['Fonte_Pagamento']}\"")
            print(f"   Tipo: {receita['Tipo_Preenchimento']}")
            print(f"   Manual: {receita['Requer_Preenchimento_Manual']}")
            print()
    
    print("Teste concluído!")
