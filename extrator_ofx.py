import re
from datetime import datetime
import pandas as pd

class ExtratorOFX:
    def __init__(self):
        self.transacoes = []
        self.transacoes_filtradas = []  # Lançamentos informativos removidos
        
        # Padrões de lançamentos informativos que devem ser filtrados
        self.lancamentos_informativos = [
            'SALDO TOTAL DISPONÍVEL DIA',
            'SALDO ANTERIOR',
            'SALDO DISPONÍVEL',
            'SALDO INICIAL',
            'SALDO FINAL'
        ]

    def eh_lancamento_informativo(self, memo):
        """
        Verifica se um lançamento é informativo e deve ser filtrado.
        
        Args:
            memo: Texto do campo MEMO da transação
            
        Returns:
            bool: True se for informativo, False caso contrário
        """
        memo_upper = memo.upper().strip()
        
        # Verifica se contém algum padrão informativo
        for padrao in self.lancamentos_informativos:
            if padrao.upper() in memo_upper:
                return True
        
        # Verifica padrões adicionais
        padroes_informativos = [
            r'^SALDO\s+(TOTAL|DISPONIVEL|ANTERIOR|INICIAL|FINAL)',
            r'POSICAO\s+DO\s+DIA',
            r'EXTRATO\s+DO\s+DIA'
        ]
        
        for padrao in padroes_informativos:
            if re.search(padrao, memo_upper):
                return True
        
        return False

    def processar_arquivo(self, caminho_arquivo):
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                conteudo = file.read()
        except UnicodeDecodeError:
            with open(caminho_arquivo, 'r', encoding='latin1') as file:
                conteudo = file.read()

        # Extrair transações
        transacoes_raw = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', conteudo, re.DOTALL)
        
        transacoes_processadas = 0
        transacoes_filtradas = 0
        
        for t in transacoes_raw:
            # Regex corrigido para capturar valores até quebra de linha ou próxima tag
            data_match = re.search(r'<DTPOSTED>(.*?)(?=\n|<)', t)
            valor_match = re.search(r'<TRNAMT>(.*?)(?=\n|<)', t)
            memo_match = re.search(r'<MEMO>(.*?)(?=\n|</STMTTRN>)', t, re.DOTALL)

            if data_match and valor_match and memo_match:
                try:
                    # Processar memo
                    memo_str = memo_match.group(1).strip()
                    
                    # Verificar se é lançamento informativo
                    if self.eh_lancamento_informativo(memo_str):
                        transacoes_filtradas += 1
                        self.transacoes_filtradas.append({
                            'memo': memo_str,
                            'valor': float(valor_match.group(1).strip()),
                            'motivo': 'Lançamento informativo'
                        })
                        continue  # Pula esta transação
                    
                    # Processar data
                    data_str = data_match.group(1).strip()
                    data_obj = datetime.strptime(data_str[:8], '%Y%m%d')
                    data_formatada = data_obj.strftime('%d/%m/%Y')
                    
                    # Processar valor
                    valor_str = valor_match.group(1).strip()
                    valor_float = float(valor_str)
                    
                    # Extrair CNPJ/CPF do memo
                    cnpj_cpf = self.extrair_cnpj_cpf(memo_str)
                    
                    # Extrair razão social
                    razao_social = self.extrair_razao_social(memo_str)
                    
                    self.transacoes.append({
                        'Data': data_formatada,
                        'Lancamentos': memo_str,
                        'Razao Social': razao_social,
                        'CNPJ/CPF': cnpj_cpf or '',
                        'Valor': valor_float,
                        'Tipo': 'Credito' if valor_float > 0 else 'Debito'
                    })
                    
                    transacoes_processadas += 1
                    
                except (ValueError, IndexError) as e:
                    print(f"Erro ao processar transacao: {e}")
                    continue

        print(f"Transações processadas: {transacoes_processadas}")
        print(f"Lançamentos informativos filtrados: {transacoes_filtradas}")
        
        return self.transacoes

    def extrair_cnpj_cpf(self, texto):
        # Busca CNPJ (14 dígitos)
        cnpj_match = re.search(r'\b\d{14}\b', texto)
        if cnpj_match:
            return cnpj_match.group()
        
        # Busca CPF (11 dígitos)
        cpf_match = re.search(r'\b\d{11}\b', texto)
        if cpf_match:
            return cpf_match.group()
        
        return None

    def extrair_razao_social(self, memo):
        # Remove prefixos comuns
        prefixos = [
            'PIX TRANSF ', 'PIX ENVIADO ', 'TED ', 'SISPAG PIX QR-CODE ',
            'REDE  VISA ', 'REDE  MAST ', 'BOLETO  PAGO ', 'DEV PIX ',
            'TAR PIX PGTO TRANSF'
        ]
        
        texto = memo
        for prefixo in prefixos:
            if texto.startswith(prefixo):
                texto = texto[len(prefixo):].strip()
                break
        
        # Se tem documento, pega o nome que vem depois
        doc = self.extrair_cnpj_cpf(texto)
        if doc:
            partes = texto.split(doc)
            if len(partes) > 1:
                nome = partes[1].strip()
                # Remove códigos no final
                nome = re.sub(r'\s+\d+$', '', nome).strip()
                if nome:
                    return nome
        
        # Limpa datas e códigos
        texto = re.sub(r'\d{2}/\d{2}', '', texto).strip()
        texto = re.sub(r'\s+\d{8,}$', '', texto).strip()
        
        return texto if texto else memo

    def salvar_csv(self, nome_arquivo='extrato.csv'):
        if self.transacoes:
            df = pd.DataFrame(self.transacoes)
            df.to_csv(nome_arquivo, index=False, encoding='utf-8')
            return True
        return False

    def exibir_resumo(self):
        if not self.transacoes:
            print("Nenhuma transacao processada.")
            return
        
        total = len(self.transacoes)
        creditos = [t for t in self.transacoes if t['Valor'] > 0]
        debitos = [t for t in self.transacoes if t['Valor'] < 0]
        
        total_creditos = sum(t['Valor'] for t in creditos)
        total_debitos = sum(t['Valor'] for t in debitos)
        
        print(f"\n=== RESUMO (SEM LANÇAMENTOS INFORMATIVOS) ===")
        print(f"Transações válidas: {total}")
        print(f"Créditos: {len(creditos)} - R$ {total_creditos:,.2f}")
        print(f"Débitos: {len(debitos)} - R$ {total_debitos:,.2f}")
        print(f"Saldo líquido: R$ {(total_creditos + total_debitos):,.2f}")
        
        if self.transacoes_filtradas:
            print(f"\n=== LANÇAMENTOS FILTRADOS ===")
            print(f"Total filtrado: {len(self.transacoes_filtradas)}")
            for filtrada in self.transacoes_filtradas:
                print(f"- {filtrada['memo']} (R$ {filtrada['valor']:,.2f})")

    def obter_estatisticas_filtros(self):
        """Retorna estatísticas sobre os filtros aplicados."""
        return {
            'transacoes_validas': len(self.transacoes),
            'transacoes_filtradas': len(self.transacoes_filtradas),
            'detalhes_filtradas': self.transacoes_filtradas
        }

# Teste rápido
if __name__ == "__main__":
    extrator = ExtratorOFX()
    transacoes = extrator.processar_arquivo('/home/ubuntu/upload/Extrato_321200986529_19-09-2025_Parte1.ofx')
    print(f"Transacoes processadas: {len(transacoes)}")
    if transacoes:
        extrator.exibir_resumo()
        print(f"\nPrimeira transacao: {transacoes[0]}")
        
        # Mostrar estatísticas dos filtros
        stats = extrator.obter_estatisticas_filtros()
        print(f"\nEstatísticas dos filtros:")
        print(f"- Transações válidas: {stats['transacoes_validas']}")
        print(f"- Transações filtradas: {stats['transacoes_filtradas']}")
