#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Limpar Todos os Dados do Sistema
Mantém os backups intactos
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def limpar_dados_sistema():
    """
    Limpa todos os dados do sistema mantendo os backups.
    """
    
    print("="*80)
    print("LIMPEZA DE DADOS DO SISTEMA FINANCEIRO")
    print("="*80 + "\n")
    
    # Diretório de dados persistentes
    dir_dados = Path("dados_persistentes")
    
    if not dir_dados.exists():
        print("⚠️  Diretório 'dados_persistentes' não encontrado.")
        print("   Nada a limpar.")
        return
    
    print("📂 Diretório encontrado:", dir_dados.absolute())
    print()
    
    # Listar arquivos que serão removidos
    arquivos_principais = [
        'despesas.csv',
        'receitas_simples.csv',
        'resultados_mensais.csv',
        'historico_processamentos.json',
        'historico_fechamentos.json',
        'configuracoes.json'
    ]
    
    print("📋 Arquivos que serão REMOVIDOS:")
    print("-" * 80)
    
    arquivos_encontrados = []
    for arquivo in arquivos_principais:
        caminho = dir_dados / arquivo
        if caminho.exists():
            tamanho = caminho.stat().st_size
            print(f"  ❌ {arquivo} ({tamanho:,} bytes)")
            arquivos_encontrados.append(caminho)
        else:
            print(f"  ⚪ {arquivo} (não existe)")
    
    print()
    
    # Listar backups que serão MANTIDOS
    print("💾 Backups que serão MANTIDOS:")
    print("-" * 80)
    
    backups_dir = dir_dados / "backups"
    if backups_dir.exists():
        backups = list(backups_dir.glob("*"))
        if backups:
            for backup in sorted(backups):
                tamanho = backup.stat().st_size
                print(f"  ✅ {backup.name} ({tamanho:,} bytes)")
        else:
            print("  ⚪ Nenhum backup encontrado")
    else:
        print("  ⚪ Pasta de backups não existe")
    
    print()
    print("="*80)
    
    if not arquivos_encontrados:
        print("\n✅ Nenhum arquivo de dados encontrado. Sistema já está limpo!")
        return
    
    # Confirmação
    print(f"\n⚠️  ATENÇÃO: {len(arquivos_encontrados)} arquivo(s) será(ão) REMOVIDO(S)!")
    print("   Os backups serão MANTIDOS e podem ser restaurados depois.")
    print()
    
    resposta = input("   Deseja continuar? (digite 'SIM' para confirmar): ")
    
    if resposta.upper() != 'SIM':
        print("\n❌ Operação cancelada pelo usuário.")
        return
    
    print()
    print("🗑️  Removendo arquivos...")
    print("-" * 80)
    
    # Remover arquivos
    removidos = 0
    erros = 0
    
    for arquivo in arquivos_encontrados:
        try:
            arquivo.unlink()
            print(f"  ✅ Removido: {arquivo.name}")
            removidos += 1
        except Exception as e:
            print(f"  ❌ Erro ao remover {arquivo.name}: {e}")
            erros += 1
    
    print()
    print("="*80)
    print("RESUMO DA LIMPEZA")
    print("="*80)
    print(f"  ✅ Arquivos removidos: {removidos}")
    print(f"  ❌ Erros: {erros}")
    
    if backups_dir.exists():
        num_backups = len(list(backups_dir.glob("*")))
        print(f"  💾 Backups mantidos: {num_backups}")
    
    print()
    
    if removidos > 0:
        print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print()
        print("📝 Próximos passos:")
        print("   1. Reinicie a aplicação Streamlit")
        print("   2. Faça upload de um novo arquivo OFX no Dashboard")
        print("   3. Comece a usar o sistema do zero")
        print()
        print("💡 Dica: Se precisar restaurar dados antigos, use os backups mantidos.")
    else:
        print("⚠️  Nenhum arquivo foi removido.")
    
    print()
    print("="*80)


def criar_backup_antes_limpar():
    """
    Cria um backup de segurança antes de limpar os dados.
    """
    
    print("="*80)
    print("BACKUP DE SEGURANÇA ANTES DA LIMPEZA")
    print("="*80 + "\n")
    
    from gerenciador_persistencia_unificado import GerenciadorPersistenciaUnificado
    
    try:
        gerenciador = GerenciadorPersistenciaUnificado()
        resultado = gerenciador.fazer_backup()
        
        if resultado['sucesso']:
            print(f"✅ Backup criado com sucesso!")
            print(f"   Timestamp: {resultado['timestamp']}")
            print(f"   Diretório: {resultado.get('diretorio', 'N/A')}")
            print()
            return True
        else:
            print(f"❌ Erro ao criar backup: {resultado['erro']}")
            print()
            return False
    
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        print()
        return False


def menu_principal():
    """
    Menu principal do script de limpeza.
    """
    
    print()
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "LIMPEZA DE DADOS DO SISTEMA" + " "*31 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    print("Opções disponíveis:")
    print()
    print("  1. 💾 Criar backup de segurança ANTES de limpar")
    print("  2. 🗑️  Limpar dados (mantendo backups)")
    print("  3. 💾 + 🗑️  Criar backup E limpar dados")
    print("  4. ❌ Cancelar")
    print()
    
    opcao = input("Escolha uma opção (1-4): ")
    
    print()
    
    if opcao == '1':
        criar_backup_antes_limpar()
    
    elif opcao == '2':
        limpar_dados_sistema()
    
    elif opcao == '3':
        print("Executando: Backup + Limpeza")
        print()
        
        if criar_backup_antes_limpar():
            print("Prosseguindo com a limpeza...")
            print()
            limpar_dados_sistema()
        else:
            print("❌ Backup falhou. Limpeza cancelada por segurança.")
    
    elif opcao == '4':
        print("❌ Operação cancelada.")
    
    else:
        print("❌ Opção inválida.")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
