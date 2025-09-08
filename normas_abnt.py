# normas_abnt.py
# Descrição: O "Motor de Regras". Centraliza todas as constantes e lógicas
# de formatação da ABNT para ser usado por qualquer gerador de documento.

from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

class MotorNormasABNT:
    """
    Esta classe é a fonte única de verdade para todas as especificações ABNT.
    Ela não sabe como criar um documento, apenas como formatar seus elementos.
    """
    def __init__(self):
        # --- Constantes de Página e Fonte (NBR 14724) ---
        self.MARGEM_SUPERIOR = Cm(3)
        self.MARGEM_INFERIOR = Cm(2)
        self.MARGEM_ESQUERDA = Cm(3)
        self.MARGEM_DIREITA = Cm(2)
        
        self.FONTE_PADRAO = 'Times New Roman'
        self.TAMANHO_FONTE_PADRAO = Pt(12)
        self.TAMANHO_FONTE_CAPA = Pt(14)
        
        self.ESPAÇAMENTO_PADRAO = 1.5
        self.ESPAÇAMENTO_SIMPLES = 1.0

        # --- Constantes de Formatação de Texto ---
        self.RECUO_PRIMEIRA_LINHA = Cm(1.25)
        self.RECUO_CITACAO_LONGA = Cm(4)
        self.TAMANHO_FONTE_CITACAO_LONGA = Pt(10)
    
    def configurar_pagina_e_estilos(self, doc):
        """Aplica as configurações de página e define os estilos base no documento."""
        # Configuração de margens para todas as seções
        for section in doc.sections:
            section.top_margin = self.MARGEM_SUPERIOR
            section.bottom_margin = self.MARGEM_INFERIOR
            section.left_margin = self.MARGEM_ESQUERDA
            section.right_margin = self.MARGEM_DIREITA

        # Estilo Padrão 'Normal'
        style = doc.styles['Normal']
        style.font.name = self.FONTE_PADRAO
        style.font.size = self.TAMANHO_FONTE_PADRAO
        style.paragraph_format.line_spacing = self.ESPAÇAMENTO_PADRAO
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)

        # Estilo para Citação Longa
        citacao_style = doc.styles.add_style('CitacaoLonga', 1)
        citacao_style.base_style = style
        citacao_style.font.size = self.TAMANHO_FONTE_CITACAO_LONGA
        citacao_style.paragraph_format.left_indent = self.RECUO_CITACAO_LONGA
        citacao_style.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES

        # Estilo para Referências
        ref_style = doc.styles.add_style('Referencias', 1)
        ref_style.base_style = style
        ref_style.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES
        ref_style.paragraph_format.space_after = Pt(6) # Espaçamento entre referências
        ref_style.paragraph_format.first_line_indent = 0 # Referências não têm recuo
    
    def aplicar_estilo_paragrafo_normal(self, paragrafo, texto):
        """Aplica o estilo de um parágrafo de corpo de texto comum."""
        paragrafo.style = 'Normal'
        paragrafo.paragraph_format.first_line_indent = self.RECUO_PRIMEIRA_LINHA
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        paragrafo.add_run(texto)

    def aplicar_estilo_titulo_secao(self, doc, numero, titulo_texto, nivel=1):
        """Aplica o estilo de um título de seção primária (ex: 1 TÍTULO)."""
        # ABNT: Títulos de seção sem recuo, alinhados à esquerda.
        titulo_formatado = f"{numero} {titulo_texto.upper()}"
        heading = doc.add_heading(titulo_formatado, level=nivel)
        heading.style.font.name = self.FONTE_PADRAO
        heading.style.font.bold = True
        heading.style.font.size = self.TAMANHO_FONTE_PADRAO
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        heading.paragraph_format.first_line_indent = 0

    def aplicar_estilo_natureza_trabalho(self, paragrafo, texto):
        """Aplica o estilo do parágrafo da natureza do trabalho na folha de rosto."""
        paragrafo.style = 'Normal'
        paragrafo.paragraph_format.left_indent = Cm(8)
        paragrafo.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        paragrafo.add_run(texto)
    
    def aplicar_estilo_resumo(self, paragrafo, texto):
        """Aplica o estilo do parágrafo do resumo."""
        paragrafo.style = 'Normal'
        paragrafo.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES
        paragrafo.paragraph_format.first_line_indent = 0
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        paragrafo.add_run(texto)

    def aplicar_estilo_referencia(self, paragrafo, texto_formatado):
        """Aplica o estilo a um parágrafo de referência bibliográfica."""
        paragrafo.style = 'Referencias'
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        
        # Lógica para aplicar negrito apenas no título
        partes = texto_formatado.split('**')
        for i, parte in enumerate(partes):
            run = paragrafo.add_run(parte)
            if i == 1: # A parte do meio, entre '**', é o título
                run.bold = True