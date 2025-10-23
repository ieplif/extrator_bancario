"""
Exportador de Relatórios com Identidade Visual Humaniza
Gera relatórios em PDF e Excel com a paleta de cores da clínica
"""

import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io
import os

class ExportadorRelatoriosHumaniza:
    """Exporta relatórios com identidade visual da clínica Humaniza."""
    
    # Paleta de cores Humaniza
    CORES = {
        'terracota': (191, 111, 78),      # #BF6F4E
        'bege': (207, 167, 142),          # #CFA78E
        'verde_claro': (182, 183, 165),   # #B6B7A5
        'verde_sage': (132, 149, 133),    # #849585
        'creme': (233, 229, 220)          # #E9E5DC
    }
    
    def __init__(self):
        self.logo_path = os.path.join(os.path.dirname(__file__), "logo_humaniza.png")
    
    def exportar_resultado_pdf(self, resultado_mes, observacoes=""):
        """
        Exporta resultado mensal para PDF com identidade Humaniza.
        
        Args:
            resultado_mes (dict): Dados do resultado mensal
            observacoes (str): Observações adicionais
            
        Returns:
            bytes: Arquivo PDF em bytes
        """
        pdf = FPDF()
        pdf.add_page()
        
        # Logo
        try:
            pdf.image(self.logo_path, x=10, y=8, w=50)
        except:
            pass
        
        # Cabeçalho
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(*self.CORES['verde_sage'])
        pdf.cell(0, 10, '', 0, 1)  # Espaço para logo
        pdf.cell(0, 10, f"Resultado Mensal - {resultado_mes['mes_ano']}", 0, 1, 'C')
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
        pdf.ln(10)
        
        # Receita Bruta
        pdf.set_fill_color(*self.CORES['creme'])
        pdf.set_text_color(*self.CORES['verde_sage'])
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Receita Bruta', 0, 1, 'L', True)
        
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, f"R$ {resultado_mes['receita_bruta']:,.2f}", 0, 1, 'L')
        pdf.ln(5)
        
        # Despesas Operacionais
        pdf.set_fill_color(*self.CORES['creme'])
        pdf.set_text_color(*self.CORES['terracota'])
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Despesas Operacionais', 0, 1, 'L', True)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        despesas = resultado_mes['despesas_operacionais']
        categorias = ['Aluguel', 'Luz', 'Fisioterapeutas', 'Limpeza', 'Diversos', 'Tributos']
        
        for cat in categorias:
            if cat in despesas:
                pdf.cell(100, 6, f"  {cat}", 0, 0, 'L')
                pdf.cell(0, 6, f"R$ {despesas[cat]:,.2f}", 0, 1, 'R')
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(100, 7, 'Total Operacionais', 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {resultado_mes['total_operacionais']:,.2f}", 0, 1, 'R')
        pdf.ln(5)
        
        # Resultado Bruto
        pdf.set_fill_color(*self.CORES['creme'])
        pdf.set_text_color(*self.CORES['verde_sage'])
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Resultado Bruto', 0, 1, 'L', True)
        
        pdf.set_font('Arial', 'B', 11)
        cor = self.CORES['verde_sage'] if resultado_mes['resultado_bruto'] >= 0 else self.CORES['terracota']
        pdf.set_text_color(*cor)
        pdf.cell(0, 7, f"R$ {resultado_mes['resultado_bruto']:,.2f}", 0, 1, 'L')
        pdf.ln(5)
        
        # Retirada
        pdf.set_fill_color(*self.CORES['creme'])
        pdf.set_text_color(*self.CORES['terracota'])
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Retirada', 0, 1, 'L', True)
        
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, f"R$ {resultado_mes['retirada']:,.2f}", 0, 1, 'L')
        pdf.ln(5)
        
        # Resultado Líquido
        pdf.set_fill_color(*self.CORES['creme'])
        pdf.set_text_color(*self.CORES['verde_sage'])
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Resultado Líquido', 0, 1, 'L', True)
        
        pdf.set_font('Arial', 'B', 13)
        cor = self.CORES['verde_sage'] if resultado_mes['resultado_liquido'] >= 0 else self.CORES['terracota']
        pdf.set_text_color(*cor)
        pdf.cell(0, 8, f"R$ {resultado_mes['resultado_liquido']:,.2f}", 0, 1, 'L')
        pdf.ln(10)
        
        # Observações
        if observacoes:
            pdf.set_fill_color(*self.CORES['creme'])
            pdf.set_text_color(*self.CORES['verde_sage'])
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, 'Observações', 0, 1, 'L', True)
            
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, observacoes)
        
        # Rodapé
        #pdf.set_y(-20)
        #pdf.set_font('Arial', 'I', 8)
        #pdf.set_text_color(150, 150, 150)
        #pdf.cell(0, 10, 'Humaniza - Sistema de Gestão Financeira', 0, 0, 'C')
        
        return bytes(pdf.output())

    
    def exportar_despesas_excel(self, despesas_df, mes_ano=None):
        """
        Exporta despesas para Excel com formatação Humaniza.
        
        Args:
            despesas_df (pd.DataFrame): DataFrame com despesas
            mes_ano (str): Mês/Ano para filtro (opcional)
            
        Returns:
            bytes: Arquivo Excel em bytes
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Filtrar por mês se fornecido
            if mes_ano and 'Mes_Ano' in despesas_df.columns:
                df_export = despesas_df[despesas_df['Mes_Ano'] == mes_ano].copy()
            else:
                df_export = despesas_df.copy()
            
            # Formatar valores
            if 'Valor' in df_export.columns:
                df_export['Valor'] = df_export['Valor'].apply(lambda x: f"R$ {x:,.2f}")
            
            # Exportar
            df_export.to_excel(writer, sheet_name='Despesas', index=False)
            
            # Formatação (básica, pode ser expandida)
            worksheet = writer.sheets['Despesas']
            worksheet.sheet_properties.tabColor = "849585"  # Verde sage
        
        output.seek(0)
        return output.getvalue()
    
    def exportar_receitas_excel(self, receitas_df, mes_ano=None):
        """
        Exporta receitas para Excel com formatação Humaniza.
        
        Args:
            receitas_df (pd.DataFrame): DataFrame com receitas
            mes_ano (str): Mês/Ano para filtro (opcional)
            
        Returns:
            bytes: Arquivo Excel em bytes
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Filtrar por mês se fornecido
            if mes_ano and 'Mes_Ano' in receitas_df.columns:
                df_export = receitas_df[receitas_df['Mes_Ano'] == mes_ano].copy()
            else:
                df_export = receitas_df.copy()
            
            # Formatar valores
            if 'Valor' in df_export.columns:
                df_export['Valor'] = df_export['Valor'].apply(lambda x: f"R$ {x:,.2f}")
            
            # Exportar
            df_export.to_excel(writer, sheet_name='Receitas', index=False)
            
            # Formatação
            worksheet = writer.sheets['Receitas']
            worksheet.sheet_properties.tabColor = "849585"  # Verde sage
        
        output.seek(0)
        return output.getvalue()

