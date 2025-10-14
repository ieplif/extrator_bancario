import pandas as pd
import os
from datetime import datetime
import re

class CategorizadorDespesas:
    """
    Sistema de categorização automática de despesas baseado em regras
    de Razão Social para organizar gastos em categorias específicas.
    """
    
    def __init__(self, arquivo_despesas='despesas_persistentes.csv'):
        self.arquivo_despesas = arquivo_despesas
        self.regras_categorizacao = {
            'Retirada': ['CAISSA', 'FILIPE DE SOUZA RIBEIRO'],
            'Limpeza': ['GISELE CRISTINA DA SILVA'],
            'Luz': ['LIGHT'],
            'Aluguel': ['PJBANK'],
            'Fisioterapeutas': ['BEATRIZ PRETA RICART', 'RAFAELA MAGALHAES DE FRANCA'],
            'Contabilidade': ['ELISANGELA VIANNA BARRETO'],
        }
        
    def categorizar_despesa(self, razao_social):
        """
        Categoriza uma despesa baseada na razão social.
        
        Args:
            razao_social (str): Nome da razão social da transação
            
        Returns:
            str: Categoria da despesa
        """
        if not razao_social:
            return 'Diversos'
        
        razao_upper = razao_social.upper().strip()
        
        # Aplicar regras de categorização
        for categoria, palavras_chave in self.regras_categorizacao.items():
            for palavra in palavras_chave:
                if palavra.upper() in razao_upper:
                    return categoria
        
        # Se não encontrou nenhuma regra, categoriza como Diversos
        return 'Diversos'
    
    def processar_debitos(self, transacoes):
        """
        Processa apenas os débitos das transações e os categoriza.
        
        Args:
            transacoes (list): Lista de transações extraídas do OFX
            
        Returns:
            pd.DataFrame: DataFrame com despesas categorizadas
        """
        despesas = []
        
        for transacao in transacoes:
            # Processar apenas débitos (valores negativos)
            if transacao['Valor'] < 0:
                categoria = self.categorizar_despesa(transacao['Razao Social'])
                
                despesa = {
                    'Data': transacao['Data'],
                    'Descricao': categoria,
                    'Valor': abs(transacao['Valor']),  # Valor absoluto para despesas
                    'Razao_Social_Original': transacao['Razao Social'],
                    'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                }
                
                despesas.append(despesa)
        
        return pd.DataFrame(despesas)
    
    def carregar_despesas_existentes(self):
        """
        Carrega despesas já salvas no arquivo persistente.
        
        Returns:
            pd.DataFrame: DataFrame com despesas existentes ou vazio
        """
        if os.path.exists(self.arquivo_despesas):
            try:
                return pd.read_csv(self.arquivo_despesas, encoding='utf-8')
            except Exception as e:
                print(f"Erro ao carregar despesas existentes: {e}")
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    
    def salvar_despesas(self, novas_despesas, sobrescrever=False):
        """
        Salva despesas na tabela persistente.
        
        Args:
            novas_despesas (pd.DataFrame): Novas despesas a serem salvas
            sobrescrever (bool): Se True, sobrescreve arquivo. Se False, adiciona.
            
        Returns:
            dict: Estatísticas da operação
        """
        if novas_despesas.empty:
            return {'total_salvas': 0, 'novas': 0, 'existentes': 0}
        
        if sobrescrever:
            # Sobrescrever arquivo
            novas_despesas.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
            stats = {
                'total_salvas': len(novas_despesas),
                'novas': len(novas_despesas),
                'existentes': 0,
                'modo': 'sobrescrito'
            }
        else:
            # Adicionar às despesas existentes
            despesas_existentes = self.carregar_despesas_existentes()
            
            if despesas_existentes.empty:
                # Primeiro salvamento
                novas_despesas.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
                stats = {
                    'total_salvas': len(novas_despesas),
                    'novas': len(novas_despesas),
                    'existentes': 0,
                    'modo': 'primeiro_salvamento'
                }
            else:
                # Combinar com existentes
                todas_despesas = pd.concat([despesas_existentes, novas_despesas], ignore_index=True)
                todas_despesas.to_csv(self.arquivo_despesas, index=False, encoding='utf-8')
                
                stats = {
                    'total_salvas': len(todas_despesas),
                    'novas': len(novas_despesas),
                    'existentes': len(despesas_existentes),
                    'modo': 'adicionado'
                }
        
        return stats
    
    def obter_resumo_categorias(self, despesas_df=None):
        """
        Gera resumo das despesas por categoria.
        
        Args:
            despesas_df (pd.DataFrame): DataFrame de despesas. Se None, carrega do arquivo.
            
        Returns:
            dict: Resumo por categoria
        """
        if despesas_df is None:
            despesas_df = self.carregar_despesas_existentes()
        
        if despesas_df.empty:
            return {}
        
        resumo = despesas_df.groupby('Descricao').agg({
            'Valor': ['sum', 'count'],
            'Data': ['min', 'max']
        }).round(2)
        
        # Simplificar estrutura do DataFrame
        resumo_dict = {}
        for categoria in resumo.index:
            resumo_dict[categoria] = {
                'total': resumo.loc[categoria, ('Valor', 'sum')],
                'quantidade': resumo.loc[categoria, ('Valor', 'count')],
                'primeira_data': resumo.loc[categoria, ('Data', 'min')],
                'ultima_data': resumo.loc[categoria, ('Data', 'max')]
            }
        
        return resumo_dict
    
    def obter_estatisticas_regras(self, transacoes):
        """
        Mostra estatísticas de como as regras foram aplicadas.
        
        Args:
            transacoes (list): Lista de transações
            
        Returns:
            dict: Estatísticas das regras aplicadas
        """
        debitos = [t for t in transacoes if t['Valor'] < 0]
        
        stats = {
            'total_debitos': len(debitos),
            'por_categoria': {},
            'regras_aplicadas': {}
        }
        
        for transacao in debitos:
            categoria = self.categorizar_despesa(transacao['Razao Social'])
            
            # Contar por categoria
            if categoria not in stats['por_categoria']:
                stats['por_categoria'][categoria] = {
                    'quantidade': 0,
                    'valor_total': 0,
                    'exemplos': []
                }
            
            stats['por_categoria'][categoria]['quantidade'] += 1
            stats['por_categoria'][categoria]['valor_total'] += abs(transacao['Valor'])
            
            # Adicionar exemplo (máximo 3 por categoria)
            if len(stats['por_categoria'][categoria]['exemplos']) < 3:
                stats['por_categoria'][categoria]['exemplos'].append({
                    'razao_social': transacao['Razao Social'],
                    'valor': abs(transacao['Valor'])
                })
        
        return stats

# Função de teste
def testar_categorizador():
    """Função para testar o categorizador com dados de exemplo."""
    
    # Dados de exemplo baseados no extrato real
    transacoes_exemplo = [
        {'Data': '18/09/2025', 'Razao Social': 'CAISSA PETERMANN DE MENDONCA', 'Valor': -40.00, 'Tipo': 'Debito'},
        {'Data': '15/09/2025', 'Razao Social': 'GISELE CRISTINA DA SILVA', 'Valor': -346.00, 'Tipo': 'Debito'},
        {'Data': '10/09/2025', 'Razao Social': 'LIGHT SERVICOS DE ELETRICIDADE S A', 'Valor': -133.45, 'Tipo': 'Debito'},
        {'Data': '03/09/2025', 'Razao Social': 'PJBANK PAGAMENTOS S A', 'Valor': -2930.83, 'Tipo': 'Debito'},
        {'Data': '03/09/2025', 'Razao Social': 'BEATRIZ PRETA RICART', 'Valor': -2625.20, 'Tipo': 'Debito'},
        {'Data': '03/09/2025', 'Razao Social': 'RAFAELA MAGALHAES DE FRANCA', 'Valor': -1365.40, 'Tipo': 'Debito'},
        {'Data': '15/09/2025', 'Razao Social': 'FILIPE DE SOUZA RIBEIRO', 'Valor': -4000.00, 'Tipo': 'Debito'},
        {'Data': '17/09/2025', 'Razao Social': 'BAZAR O AMIGAO SHOPPING', 'Valor': -38.97, 'Tipo': 'Debito'},
    ]
    
    categorizador = CategorizadorDespesas()
    
    # Processar débitos
    despesas_df = categorizador.processar_debitos(transacoes_exemplo)
    
    print("=== TESTE DO CATEGORIZADOR ===")
    print(f"Total de débitos processados: {len(despesas_df)}")
    print("\nDespesas categorizadas:")
    print(despesas_df[['Data', 'Descricao', 'Valor', 'Razao_Social_Original']].to_string(index=False))
    
    # Obter estatísticas
    stats = categorizador.obter_estatisticas_regras(transacoes_exemplo)
    print(f"\n=== ESTATÍSTICAS ===")
    print(f"Total de débitos: {stats['total_debitos']}")
    print("\nPor categoria:")
    for categoria, dados in stats['por_categoria'].items():
        print(f"- {categoria}: {dados['quantidade']} transações, R$ {dados['valor_total']:,.2f}")
    
    return despesas_df, categorizador

if __name__ == "__main__":
    testar_categorizador()
