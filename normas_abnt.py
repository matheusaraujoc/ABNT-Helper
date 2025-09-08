# normas_abnt.py
# Descrição: O "Motor de Regras", com a lógica de estilo de tabela corrigida.

from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

class MotorNormasABNT:
    def __init__(self):
        # (constantes sem alteração)
        self.MARGEM_SUPERIOR = Cm(3)
        self.MARGEM_INFERIOR = Cm(2)
        self.MARGEM_ESQUERDA = Cm(3)
        self.MARGEM_DIREITA = Cm(2)
        self.FONTE_PADRAO = 'Times New Roman'
        self.TAMANHO_FONTE_PADRAO = Pt(12)
        self.TAMANHO_FONTE_CAPA = Pt(14)
        self.ESPAÇAMENTO_PADRAO = 1.5
        self.ESPAÇAMENTO_SIMPLES = 1.0
        self.RECUO_PRIMEIRA_LINHA = Cm(1.25)
        self.RECUO_CITACAO_LONGA = Cm(4)
        self.TAMANHO_FONTE_CITACAO_LONGA = Pt(10)
        self.TAMANHO_FONTE_LEGENDA = Pt(10)

    # --- ## CORREÇÃO: Lógica de aplicação de bordas refeita para ser mais robusta ## ---
    def aplicar_estilo_tabela_abnt(self, tabela):
        """
        Aplica o estilo de bordas abertas da ABNT na tabela, modificando
        corretamente as propriedades existentes em vez de adicionar novas.
        """
        tbl_pr = tabela._element.xpath('w:tblPr')[0]
        
        # Procura pelo elemento de bordas existente
        tbl_borders = tbl_pr.find(qn('w:tblBorders'))
        if tbl_borders is None:
            # Se não existir, cria um novo
            tbl_borders = OxmlElement('w:tblBorders')
            tbl_pr.append(tbl_borders)

        # Remove todas as definições de borda filhas para começar do zero
        for border in tbl_borders.findall(qn('w:*')):
            tbl_borders.remove(border)

        # Define as bordas horizontais (superior, inferior e interna)
        for border_name in ['top', 'bottom', 'insideH']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4') # '4' é 0.5pt
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), 'auto')
            tbl_borders.append(border)
            
        # Garante que as bordas verticais não existam
        for border_name in ['left', 'right', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'nil') # 'nil' significa "sem borda"
            tbl_borders.append(border)

    # (Restante dos métodos sem alterações)
    def configurar_pagina_e_estilos(self, doc):
        style = doc.styles['Normal']
        style.font.name = self.FONTE_PADRAO
        style.font.size = self.TAMANHO_FONTE_PADRAO
        style.paragraph_format.line_spacing = self.ESPAÇAMENTO_PADRAO
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)
        citacao_style = doc.styles.add_style('CitacaoLonga', 1)
        citacao_style.base_style = style
        citacao_style.font.size = self.TAMANHO_FONTE_CITACAO_LONGA
        citacao_style.paragraph_format.left_indent = self.RECUO_CITACAO_LONGA
        citacao_style.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES
        ref_style = doc.styles.add_style('Referencias', 1)
        ref_style.base_style = style
        ref_style.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES
        ref_style.paragraph_format.space_after = Pt(6)
        ref_style.paragraph_format.first_line_indent = 0
        for section in doc.sections:
            section.top_margin = self.MARGEM_SUPERIOR
            section.bottom_margin = self.MARGEM_INFERIOR
            section.left_margin = self.MARGEM_ESQUERDA
            section.right_margin = self.MARGEM_DIREITA
            
    def aplicar_estilo_paragrafo_normal(self, paragrafo, texto):
        paragrafo.style = 'Normal'
        paragrafo.paragraph_format.first_line_indent = self.RECUO_PRIMEIRA_LINHA
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        paragrafo.add_run(texto)
        
    def aplicar_estilo_titulo_secao(self, doc, numero, titulo_texto, nivel=1):
        titulo_formatado = f"{numero} {titulo_texto.upper() if nivel == 1 else titulo_texto}"
        heading = doc.add_heading(titulo_formatado, level=nivel)
        heading.style.font.name = self.FONTE_PADRAO
        heading.style.font.bold = True
        heading.style.font.size = self.TAMANHO_FONTE_PADRAO
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        heading.paragraph_format.first_line_indent = 0
        
    def aplicar_estilo_natureza_trabalho(self, paragrafo, texto):
        paragrafo.style = 'Normal'
        paragrafo.paragraph_format.left_indent = Cm(8)
        paragrafo.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        paragrafo.add_run(texto)
    
    def aplicar_estilo_resumo(self, paragrafo, texto):
        paragrafo.style = 'Normal'
        paragrafo.paragraph_format.line_spacing = self.ESPAÇAMENTO_SIMPLES
        paragrafo.paragraph_format.first_line_indent = 0
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        paragrafo.add_run(texto)
        
    def aplicar_estilo_referencia(self, paragrafo, texto_formatado):
        paragrafo.style = 'Referencias'
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        partes = texto_formatado.split('**')
        for i, parte in enumerate(partes):
            run = paragrafo.add_run(parte)
            if i == 1:
                run.bold = True