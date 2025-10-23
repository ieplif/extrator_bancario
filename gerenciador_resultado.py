import pandas as pd
import os
from datetime import datetime
import json

class GerenciadorResultado:
    """
    Gerencia fechamentos mensais e cálculo de resultados.
    """
    
    def __init__(self, diretorio_dados='dados_persistentes'):
        self.diretorio_dados = diretorio_dados
        self.arquivo_resultados = os.path.join(diretorio_dados, 'resultados_mensais.csv')
        self.arquivo_historico = os.path.join(diretorio_dados, 'historico_fechamentos.json')
        
        # Criar diretório se não existir
        os.makedirs(diretorio_dados, exist_ok=True)
        
        # Inicializar arquivos se não existirem
        self._inicializar_arquivos()
    
    def _inicializar_arquivos(self):
        """Inicializa arquivos de dados se não existirem."""
        
        # Inicializar arquivo de resultados
        if not os.path.exists(self.arquivo_resultados):
            df_resultados_vazio = pd.DataFrame(columns=[
                'Mes_Ano', 'Receita_Bruta', 'Aluguel', 'Luz', 'Fisioterapeutas',
                'Limpeza', 'Tributos', 'Diversos', 'Total_Operacionais', 'Resultado_Bruto',
                'Retirada', 'Resultado_Liquido', 'Data_Fechamento', 'Observacoes'
            ])
            df_resultados_vazio.to_csv(self.arquivo_resultados, index=False, encoding='utf-8')
        
        # Inicializar histórico
        if not os.path.exists(self.arquivo_historico):
            historico_vazio = {
                'fechamentos': [],
                'total_fechamentos': 0
            }
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(historico_vazio, f, indent=2, ensure_ascii=False)
    
    def calcular_resultado_mes(self, mes_ano, receitas_df, despesas_df):
        """
        Calcula resultado do mês baseado em receitas e despesas.
        
        Args:
            mes_ano (str): Mês no formato MM/YYYY
            receitas_df (pd.DataFrame): DataFrame de receitas do mês
            despesas_df (pd.DataFrame): DataFrame de despesas do mês
            
        Returns:
            dict: Resultado calculado
        """
        try:
            # Calcular receita bruta
            receita_bruta = receitas_df['Valor'].sum() if not receitas_df.empty else 0
            
            # Calcular despesas operacionais por categoria
            despesas_operacionais = {
                'Aluguel': 0,
                'Luz': 0,
                'Fisioterapeutas': 0,
                'Limpeza': 0,
                'Tributos': 0,
                'Diversos': 0
            }
            
            retirada = 0
            
            if not despesas_df.empty:
                for categoria in despesas_operacionais.keys():
                    valor = despesas_df[despesas_df['Descricao'] == categoria]['Valor'].sum()
                    despesas_operacionais[categoria] = abs(valor)  # Garantir valor positivo
                
                # Calcular retirada
                retirada = abs(despesas_df[despesas_df['Descricao'] == 'Retirada']['Valor'].sum())
            
            # Calcular totais
            total_operacionais = sum(despesas_operacionais.values())
            resultado_bruto = receita_bruta - total_operacionais
            resultado_liquido = resultado_bruto - retirada
            
            return {
                'mes_ano': mes_ano,
                'receita_bruta': receita_bruta,
                'despesas_operacionais': despesas_operacionais,
                'total_operacionais': total_operacionais,
                'resultado_bruto': resultado_bruto,
                'retirada': retirada,
                'resultado_liquido': resultado_liquido,
                'data_fechamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'erro': str(e),
                'mes_ano': mes_ano,
                'receita_bruta': 0,
                'despesas_operacionais': {k: 0 for k in despesas_operacionais.keys()},
                'total_operacionais': 0,
                'resultado_bruto': 0,
                'retirada': 0,
                'resultado_liquido': 0
            }
    
    def salvar_fechamento(self, resultado_calculado, observacoes=''):
        """
        Salva fechamento mensal.
        
        Args:
            resultado_calculado (dict): Resultado do cálculo
            observacoes (str): Observações do fechamento
            
        Returns:
            dict: Resultado da operação
        """
        try:
            # Verificar se já existe fechamento para o mês
            resultados_existentes = self.carregar_resultados()
            mes_ano = resultado_calculado['mes_ano']
            
            if not resultados_existentes.empty:
                if mes_ano in resultados_existentes['Mes_Ano'].values:
                    return {
                        'sucesso': False,
                        'erro': f'Já existe fechamento para {mes_ano}. Use sobrescrever se necessário.'
                    }
            
            # Preparar dados para salvar
            novo_resultado = {
                'Mes_Ano': mes_ano,
                'Receita_Bruta': resultado_calculado['receita_bruta'],
                'Aluguel': resultado_calculado['despesas_operacionais']['Aluguel'],
                'Luz': resultado_calculado['despesas_operacionais']['Luz'],
                'Fisioterapeutas': resultado_calculado['despesas_operacionais']['Fisioterapeutas'],
                'Limpeza': resultado_calculado['despesas_operacionais']['Limpeza'],
                'Tributos': resultado_calculado['despesas_operacionais']['Tributos'],
                'Diversos': resultado_calculado['despesas_operacionais']['Diversos'],
                'Total_Operacionais': resultado_calculado['total_operacionais'],
                'Resultado_Bruto': resultado_calculado['resultado_bruto'],
                'Retirada': resultado_calculado['retirada'],
                'Resultado_Liquido': resultado_calculado['resultado_liquido'],
                'Data_Fechamento': resultado_calculado['data_fechamento'],
                'Observacoes': observacoes
            }
            
            # Adicionar aos dados existentes
            if resultados_existentes.empty:
                df_novo = pd.DataFrame([novo_resultado])
            else:
                df_novo = pd.concat([resultados_existentes, pd.DataFrame([novo_resultado])], ignore_index=True)
            
            # Ordenar por mês/ano (mais recente primeiro)
            df_novo['Data_Ordenacao'] = pd.to_datetime(df_novo['Mes_Ano'], format='%m/%Y')
            df_novo = df_novo.sort_values('Data_Ordenacao', ascending=False).drop('Data_Ordenacao', axis=1)
            
            # Salvar
            df_novo.to_csv(self.arquivo_resultados, index=False, encoding='utf-8')
            
            # Registrar no histórico
            self._registrar_fechamento(resultado_calculado)
            
            return {
                'sucesso': True,
                'mes_ano': mes_ano,
                'resultado_liquido': resultado_calculado['resultado_liquido']
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def sobrescrever_fechamento(self, resultado_calculado, observacoes=''):
        """
        Sobrescreve fechamento existente.
        
        Args:
            resultado_calculado (dict): Resultado do cálculo
            observacoes (str): Observações do fechamento
            
        Returns:
            dict: Resultado da operação
        """
        try:
            resultados_existentes = self.carregar_resultados()
            mes_ano = resultado_calculado['mes_ano']
            
            # Remover fechamento existente se houver
            if not resultados_existentes.empty:
                resultados_existentes = resultados_existentes[resultados_existentes['Mes_Ano'] != mes_ano]
            
            # Preparar novo resultado
            novo_resultado = {
                'Mes_Ano': mes_ano,
                'Receita_Bruta': resultado_calculado['receita_bruta'],
                'Aluguel': resultado_calculado['despesas_operacionais']['Aluguel'],
                'Luz': resultado_calculado['despesas_operacionais']['Luz'],
                'Fisioterapeutas': resultado_calculado['despesas_operacionais']['Fisioterapeutas'],
                'Limpeza': resultado_calculado['despesas_operacionais']['Limpeza'],
                'Tributos': resultado_calculado['despesas_operacionais']['Tributos'],
                'Diversos': resultado_calculado['despesas_operacionais']['Diversos'],
                'Total_Operacionais': resultado_calculado['total_operacionais'],
                'Resultado_Bruto': resultado_calculado['resultado_bruto'],
                'Retirada': resultado_calculado['retirada'],
                'Resultado_Liquido': resultado_calculado['resultado_liquido'],
                'Data_Fechamento': resultado_calculado['data_fechamento'],
                'Observacoes': observacoes
            }
            
            # Adicionar novo resultado
            if resultados_existentes.empty:
                df_novo = pd.DataFrame([novo_resultado])
            else:
                df_novo = pd.concat([resultados_existentes, pd.DataFrame([novo_resultado])], ignore_index=True)
            
            # Ordenar por mês/ano
            df_novo['Data_Ordenacao'] = pd.to_datetime(df_novo['Mes_Ano'], format='%m/%Y')
            df_novo = df_novo.sort_values('Data_Ordenacao', ascending=False).drop('Data_Ordenacao', axis=1)
            
            # Salvar
            df_novo.to_csv(self.arquivo_resultados, index=False, encoding='utf-8')
            
            return {
                'sucesso': True,
                'mes_ano': mes_ano,
                'resultado_liquido': resultado_calculado['resultado_liquido'],
                'sobrescrito': True
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def carregar_resultados(self):
        """
        Carrega todos os resultados salvos.
        
        Returns:
            pd.DataFrame: DataFrame com resultados
        """
        try:
            if os.path.exists(self.arquivo_resultados):
                return pd.read_csv(self.arquivo_resultados, encoding='utf-8')
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Erro ao carregar resultados: {e}")
            return pd.DataFrame()
    
    def obter_resultado_mes(self, mes_ano):
        """
        Obtém resultado de um mês específico.
        
        Args:
            mes_ano (str): Mês no formato MM/YYYY
            
        Returns:
            dict: Resultado do mês ou None
        """
        resultados = self.carregar_resultados()
        
        if resultados.empty:
            return None
        
        resultado_mes = resultados[resultados['Mes_Ano'] == mes_ano]
        
        if resultado_mes.empty:
            return None
        
        return resultado_mes.iloc[0].to_dict()
    
    def obter_resumo_anual(self, ano):
        """
        Gera resumo anual dos resultados.
        
        Args:
            ano (str): Ano (YYYY)
            
        Returns:
            dict: Resumo anual
        """
        resultados = self.carregar_resultados()
        
        if resultados.empty:
            return {
                'ano': ano,
                'meses_fechados': 0,
                'receita_bruta_total': 0,
                'despesas_operacionais_total': 0,
                'retirada_total': 0,
                'resultado_liquido_total': 0,
                'meses': []
            }
        
        # Filtrar pelo ano
        resultados['Ano'] = resultados['Mes_Ano'].str.split('/').str[1]
        resultados_ano = resultados[resultados['Ano'] == ano]
        
        if resultados_ano.empty:
            return {
                'ano': ano,
                'meses_fechados': 0,
                'receita_bruta_total': 0,
                'despesas_operacionais_total': 0,
                'retirada_total': 0,
                'resultado_liquido_total': 0,
                'meses': []
            }
        
        return {
            'ano': ano,
            'meses_fechados': len(resultados_ano),
            'receita_bruta_total': resultados_ano['Receita_Bruta'].sum(),
            'despesas_operacionais_total': resultados_ano['Total_Operacionais'].sum(),
            'retirada_total': resultados_ano['Retirada'].sum(),
            'resultado_liquido_total': resultados_ano['Resultado_Liquido'].sum(),
            'meses': resultados_ano['Mes_Ano'].tolist()
        }
    
    def _registrar_fechamento(self, resultado_calculado):
        """Registra fechamento no histórico."""
        try:
            historico = self.carregar_historico()
            
            novo_fechamento = {
                'data_hora': datetime.now().isoformat(),
                'mes_ano': resultado_calculado['mes_ano'],
                'receita_bruta': resultado_calculado['receita_bruta'],
                'resultado_liquido': resultado_calculado['resultado_liquido']
            }
            
            historico['fechamentos'].append(novo_fechamento)
            historico['total_fechamentos'] += 1
            
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao registrar fechamento: {e}")
    
    def carregar_historico(self):
        """Carrega histórico de fechamentos."""
        try:
            with open(self.arquivo_historico, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            return {'fechamentos': [], 'total_fechamentos': 0}
    
    def excluir_fechamento(self, mes_ano):
        """
        Exclui fechamento de um mês.
        
        Args:
            mes_ano (str): Mês no formato MM/YYYY
            
        Returns:
            dict: Resultado da operação
        """
        try:
            resultados = self.carregar_resultados()
            
            if resultados.empty:
                return {'sucesso': False, 'erro': 'Nenhum resultado encontrado'}
            
            if mes_ano not in resultados['Mes_Ano'].values:
                return {'sucesso': False, 'erro': f'Fechamento de {mes_ano} não encontrado'}
            
            # Remover o fechamento
            resultados_filtrados = resultados[resultados['Mes_Ano'] != mes_ano]
            
            # Salvar
            resultados_filtrados.to_csv(self.arquivo_resultados, index=False, encoding='utf-8')
            
            return {
                'sucesso': True,
                'mes_ano': mes_ano
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

# Teste do sistema
if __name__ == "__main__":
    print("=== TESTE DO GERENCIADOR DE RESULTADO ===")
    
    gerenciador = GerenciadorResultado()
    
    # Dados de teste
    receitas_teste = pd.DataFrame([
        {'Valor': 15000.00, 'Paciente': 'Cliente 1'},
        {'Valor': 8000.00, 'Paciente': 'Cliente 2'}
    ])
    
    despesas_teste = pd.DataFrame([
        {'Descricao': 'Aluguel', 'Valor': -3000.00},
        {'Descricao': 'Luz', 'Valor': -200.00},
        {'Descricao': 'Fisioterapeutas', 'Valor': -4000.00},
        {'Descricao': 'Retirada', 'Valor': -8000.00}
    ])
    
    # Calcular resultado
    resultado = gerenciador.calcular_resultado_mes('09/2025', receitas_teste, despesas_teste)
    
    print("Resultado calculado:")
    print(f"- Receita Bruta: R$ {resultado['receita_bruta']:,.2f}")
    print(f"- Total Operacionais: R$ {resultado['total_operacionais']:,.2f}")
    print(f"- Resultado Bruto: R$ {resultado['resultado_bruto']:,.2f}")
    print(f"- Retirada: R$ {resultado['retirada']:,.2f}")
    print(f"- Resultado Líquido: R$ {resultado['resultado_liquido']:,.2f}")
    
    # Salvar fechamento
    resultado_salvar = gerenciador.salvar_fechamento(resultado, "Teste de fechamento")
    print(f"\\nSalvamento: {resultado_salvar}")
    
    print("\\nTeste concluído!")
