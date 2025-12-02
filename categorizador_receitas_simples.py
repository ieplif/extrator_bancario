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
            'REDE': 'Cartão de Crédito'
        }
        
        # MAPEAMENTO AUTOMÁTICO: Razão Social -> Paciente Real
        # EDITÁVEL: Adicione ou edite os mapeamentos conforme necessário
        # Formato: 'RAZÃO SOCIAL PAGADORA': 'NOME DO PACIENTE REAL'
        self.mapeamento_razao_paciente = {
            'CARLOS HENRIQUE FRANGO': 'ANNA LUÍZA MONDIN MONTANHA',
            'FELIPE CUNHA MATOS': 'LETÍCIA P. S. MATTOS',
            'KARLOS ALEXANDRE OLIVEIRA': 'TÂNIA MARA BARRETO ALVES',
            'KAREN SILVA DE MELO': 'DONA AUGUSTA',
            'MATHEUS SILVA BERNARDES': 'ESTER ROCHA SANTOS DE OLIVEIRA',
            'ALESSANDRA CRISTINE VAZ SANTOS': 'SÔNIA CRISTINA VAZ SANTOS',
            'SOLUÇÃO ELETRONICA MOTO PEÇA': 'APARECIDA',
            'LMCC DA COSTA LUANA': 'LUANA MACHADO DE CAMPOS',
            'GPBR PARTICIPACOES LTDA': 'GYMPASS',
            'PIX QRS NATALIA SIL': 'NATÁLIA SILVEIRA RODRIGUES DE OLIVEIRA,',
            'ELSON DA SILVA LIMA': 'LÚCIA KURDIAN',
            'RAFAEL GOHN ALVES': 'PATRÍCIA REYNOZO',
            'RICARDO DA COSTA SILVA': 'GLAUCE LEANDRO E LUCINEIA LEANDRO',
            'LORRAN MORAES SARENTO': 'LAÍS CECÍLIO DA COSTA',
            'ALESSANDRA CRISTINE VAZ SANTOS': 'SÔNIA CRISTINA VAZ SANTOS'
            'ADRIANA CRISTINE VAZ SANTOS': 'SÔNIA CRISTINA VAZ SANTOS',
            'GILBERTO ALVES SILVA': 'LARISSSA DA VEIGA AMARAL',
        }

        # Mapeamento flexível para busca parcial (chave de busca -> chave completa do mapeamento)
        # EDITÁVEL: Adicione variações de nomes que podem aparecer no extrato
        self.mapeamento_flexivel = {
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
            'LORRAN MORAES': 'LORRAN MORAES SARENTO',
            'ALESSANDRA CRISTINE': 'ALESSANDRA CRISTINE VAZ SANTOS',
            'ADRIANA CRISTINE': 'ADRIANA CRISTINE VAZ SANTOS',
            'GILBERTO ALVES': 'GILBERTO ALVES SILVA',
        }
        
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

        # Remover "PIX RECEBIDO" do início
        texto = re.sub(r'^PIX\s+RECEBIDO\s+', '', texto, flags=re.IGNORECASE)

        # Remover números (CPF) do final
        texto = re.sub(r'\s*\d{2,}.*$', '', texto)

        # Remover números isolados
        texto = re.sub(r'\s+\d+\s*', ' ', texto)
    
        # Limpar espaços extras
        texto = re.sub(r'\s+', ' ', texto).strip()

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
        # Regra 1: REDE -> Cartão de Crédito
        if 'REDE' in razao_social_limpa.upper():
            self.estatisticas['cartao_credito'] += 1
            return {
                'paciente': '',
                'fonte_pagamento': 'Cartão de Crédito',
                'tipo_preenchimento': 'cartao_credito',
                'requer_preenchimento_manual': True,
                'motivo': 'Cartão de crédito - paciente para preenchimento manual'
            }
        
        # Regra 2: Lista específica -> Mapeamento automático (busca flexível)
        razao_upper = razao_social_limpa.upper()
        
        # Buscar por mapeamento flexível
        for busca, razao_completa in self.mapeamento_flexivel.items():
            if busca in razao_upper:
                # Obter o paciente real do mapeamento
                paciente_real = self.mapeamento_razao_paciente.get(razao_completa, '')
                
                # Se paciente está mapeado (não vazio), preencher automaticamente
                if paciente_real:
                    self.estatisticas['preenchimento_automatico'] += 1
                    return {
                        'paciente': paciente_real,
                        'fonte_pagamento': 'Particular',
                        'tipo_preenchimento': 'automatico_mapeado',
                        'requer_preenchimento_manual': False,
                        'motivo': f'Mapeamento automático: {razao_completa} → {paciente_real}'
                    }
                # Se paciente não está mapeado (vazio), requer preenchimento manual
                else:
                    self.estatisticas['preenchimento_manual'] += 1
                    return {
                        'paciente': '',
                        'fonte_pagamento': '',
                        'tipo_preenchimento': 'manual',
                        'requer_preenchimento_manual': True,
                        'motivo': f'Lista específica sem mapeamento - {razao_completa}'
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
            # Obter todas as datas desse paciente
            todas_datas = df_com_paciente[df_com_paciente['Paciente'] == paciente]['Data'].tolist()
            
            # Formatar todas as datas com tratamento robusto
            datas_formatadas = []
            for d in todas_datas:
                if pd.notna(d):
                    try:
                        # Se já for datetime, usar direto
                        if isinstance(d, (pd.Timestamp, datetime)):
                            datas_formatadas.append(d.strftime('%d/%m/%Y'))
                        # Se for string, converter com dayfirst=True (formato brasileiro)
                        else:
                            data_convertida = pd.to_datetime(d, dayfirst=True)
                            datas_formatadas.append(data_convertida.strftime('%d/%m/%Y'))
                    except:
                        # Em caso de erro, tentar converter sem especificar formato
                        try:
                            data_convertida = pd.to_datetime(d)
                            datas_formatadas.append(data_convertida.strftime('%d/%m/%Y'))
                        except:
                            pass  # Ignorar datas que não podem ser convertidas
            
            resumo[paciente] = {
                'total': pacientes.loc[paciente, ('Valor', 'sum')],
                'quantidade': pacientes.loc[paciente, ('Valor', 'count')],
                'media': pacientes.loc[paciente, ('Valor', 'mean')],
                'primeira_data': pacientes.loc[paciente, ('Data', 'min')],
                'ultima_data': pacientes.loc[paciente, ('Data', 'max')],
                'todas_datas': ', '.join(datas_formatadas) if datas_formatadas else 'Nenhuma data disponível'
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
