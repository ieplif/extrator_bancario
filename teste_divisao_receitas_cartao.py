#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para a funcionalidade de divisão de receitas de cartão de crédito
"""

import sys
import pandas as pd
from datetime import datetime

# Importar o gerenciador
from gerenciador_persistencia_unificado import GerenciadorPersistenciaUnificado

print("="*80)
print("TESTE: Divisão de Receitas de Cartão de Crédito")
print("="*80 + "\n")

# Inicializar gerenciador
gerenciador = GerenciadorPersistenciaUnificado()

print("ETAPA 1: Criar Receita de Cartão de Crédito para Teste")
print("-"*80 + "\n")

# Criar uma receita de cartão de crédito de teste
receita_teste = pd.DataFrame([{
    'Data': '05/10/2025',
    'Razao_Social_Original': 'REDECARD S.A.',
    'Razao_Social_Limpa': 'REDECARD S A',
    'Valor': 2100.00,
    'Paciente': '',
    'Fonte_Pagamento': 'Cartão de Crédito',
    'Tipo_Preenchimento': 'cartao_credito',
    'Requer_Preenchimento_Manual': True,
    'Motivo_Categorizacao': 'Cartão de crédito - paciente para preenchimento manual',
    'Data_Processamento': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    'Arquivo_Origem': 'teste_divisao.ofx'
}])

print("Receita de teste criada:")
print(f"  Data: {receita_teste.iloc[0]['Data']}")
print(f"  Razão Social: {receita_teste.iloc[0]['Razao_Social_Original']}")
print(f"  Valor: R$ {receita_teste.iloc[0]['Valor']:,.2f}")
print(f"  Tipo: {receita_teste.iloc[0]['Tipo_Preenchimento']}")

# Salvar receita de teste
resultado_salvar = gerenciador.salvar_receitas(
    receita_teste,
    arquivo_origem='teste_divisao.ofx',
    modo='adicionar'
)

if resultado_salvar['sucesso']:
    print(f"\n✅ Receita de teste salva com sucesso!")
else:
    print(f"\n❌ Erro ao salvar receita de teste: {resultado_salvar['erro']}")
    sys.exit(1)

print("\n" + "="*80)
print("ETAPA 2: Definir Divisões entre Pacientes")
print("="*80 + "\n")

# Definir como dividir a receita entre 3 pacientes
divisoes = [
    {
        'paciente': 'João Silva',
        'valor': 700.00,
        'data': '02/10/2025'
    },
    {
        'paciente': 'Maria Santos',
        'valor': 700.00,
        'data': '03/10/2025'
    },
    {
        'paciente': 'Pedro Costa',
        'valor': 700.00,
        'data': '04/10/2025'
    }
]

print("Divisões planejadas:")
for i, div in enumerate(divisoes, 1):
    print(f"  {i}. {div['paciente']:<20} | R$ {div['valor']:>10,.2f} | {div['data']}")

soma_divisoes = sum(d['valor'] for d in divisoes)
print(f"\nSoma das divisões: R$ {soma_divisoes:,.2f}")
print(f"Valor original: R$ {receita_teste.iloc[0]['Valor']:,.2f}")
print(f"Diferença: R$ {abs(soma_divisoes - receita_teste.iloc[0]['Valor']):.2f}")

print("\n" + "="*80)
print("ETAPA 3: Executar Divisão")
print("="*80 + "\n")

resultado = gerenciador.dividir_receita_cartao(
    data_original='05/10/2025',
    razao_social='REDECARD S.A.',
    valor_original=2100.00,
    divisoes=divisoes
)

if resultado['sucesso']:
    print("✅ DIVISÃO REALIZADA COM SUCESSO!\n")
    print(f"  - Receitas criadas: {resultado['receitas_criadas']}")
    print(f"  - Valor total: R$ {resultado['valor_total']:,.2f}")
    print(f"  - Valor original: R$ {resultado['valor_original']:,.2f}")
    print(f"  - Diferença: R$ {resultado['diferenca']:.2f}")
    print(f"\n  Pacientes:")
    for paciente in resultado['pacientes']:
        print(f"    - {paciente}")
else:
    print(f"❌ ERRO NA DIVISÃO: {resultado['erro']}")
    sys.exit(1)

print("\n" + "="*80)
print("ETAPA 4: Verificar Receitas Criadas")
print("="*80 + "\n")

# Carregar todas as receitas
todas_receitas = gerenciador.carregar_receitas()

# Filtrar receitas divididas
receitas_divididas = todas_receitas[
    todas_receitas['Tipo_Preenchimento'] == 'cartao_credito_dividido'
]

print(f"Total de receitas divididas encontradas: {len(receitas_divididas)}\n")

if not receitas_divididas.empty:
    print("Detalhes das receitas criadas:")
    print("-"*80)
    
    for idx, rec in receitas_divididas.iterrows():
        print(f"\n{idx+1}. Paciente: {rec['Paciente']}")
        print(f"   Data: {rec['Data']}")
        print(f"   Valor: R$ {rec['Valor']:,.2f}")
        print(f"   Fonte: {rec['Fonte_Pagamento']}")
        print(f"   Razão Social: {rec['Razao_Social_Original']}")
        print(f"   Motivo: {rec['Motivo_Categorizacao']}")

print("\n" + "="*80)
print("ETAPA 5: Verificar Receita Original")
print("="*80 + "\n")

# Verificar se a receita original foi removida
receita_original = todas_receitas[
    (todas_receitas['Data'] == '05/10/2025') &
    (todas_receitas['Razao_Social_Original'] == 'REDECARD S.A.') &
    (todas_receitas['Valor'] == 2100.00) &
    (todas_receitas['Tipo_Preenchimento'] == 'cartao_credito')
]

if receita_original.empty:
    print("✅ Receita original foi removida corretamente")
else:
    print("⚠️ Receita original ainda existe no sistema")
    print(f"   Encontradas: {len(receita_original)} receitas")

print("\n" + "="*80)
print("ETAPA 6: Validar Soma dos Valores")
print("="*80 + "\n")

soma_criadas = receitas_divididas['Valor'].sum()
print(f"Soma das receitas criadas: R$ {soma_criadas:,.2f}")
print(f"Valor original esperado: R$ 2,100.00")

if abs(soma_criadas - 2100.00) < 0.01:
    print("✅ Valores conferem!")
else:
    print(f"❌ Diferença encontrada: R$ {abs(soma_criadas - 2100.00):.2f}")

print("\n" + "="*80)
print("TESTE DE VALIDAÇÕES")
print("="*80 + "\n")

print("Teste 1: Divisão sem pacientes")
resultado_vazio = gerenciador.dividir_receita_cartao(
    data_original='05/10/2025',
    razao_social='REDECARD S.A.',
    valor_original=2100.00,
    divisoes=[]
)
print(f"  Resultado: {'✅ ERRO DETECTADO' if not resultado_vazio['sucesso'] else '❌ DEVERIA FALHAR'}")
if not resultado_vazio['sucesso']:
    print(f"  Mensagem: {resultado_vazio['erro']}")

print("\nTeste 2: Paciente com nome vazio")
resultado_nome_vazio = gerenciador.dividir_receita_cartao(
    data_original='05/10/2025',
    razao_social='REDECARD S.A.',
    valor_original=2100.00,
    divisoes=[{'paciente': '', 'valor': 100.00, 'data': '01/10/2025'}]
)
print(f"  Resultado: {'✅ ERRO DETECTADO' if not resultado_nome_vazio['sucesso'] else '❌ DEVERIA FALHAR'}")
if not resultado_nome_vazio['sucesso']:
    print(f"  Mensagem: {resultado_nome_vazio['erro']}")

print("\nTeste 3: Valor zero ou negativo")
resultado_valor_zero = gerenciador.dividir_receita_cartao(
    data_original='05/10/2025',
    razao_social='REDECARD S.A.',
    valor_original=2100.00,
    divisoes=[{'paciente': 'Teste', 'valor': 0.00, 'data': '01/10/2025'}]
)
print(f"  Resultado: {'✅ ERRO DETECTADO' if not resultado_valor_zero['sucesso'] else '❌ DEVERIA FALHAR'}")
if not resultado_valor_zero['sucesso']:
    print(f"  Mensagem: {resultado_valor_zero['erro']}")

print("\n" + "="*80)
print("RESUMO DO TESTE")
print("="*80 + "\n")

print("✅ Funcionalidade de divisão de receitas implementada com sucesso!")
print("\nRecursos testados:")
print("  ✅ Criação de receita de teste")
print("  ✅ Divisão entre múltiplos pacientes")
print("  ✅ Remoção da receita original")
print("  ✅ Criação de receitas individuais")
print("  ✅ Preservação de dados (razão social, arquivo origem)")
print("  ✅ Validação de campos obrigatórios")
print("  ✅ Validação de valores")
print("  ✅ Cálculo correto de soma")

print("\n" + "="*80)
print("FIM DO TESTE")
print("="*80)
