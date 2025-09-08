# normas_abnt.py
# Descrição: O "Motor de Regras" que centraliza todas as especificações da ABNT.

from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

class MotorNormasABNT:
    def __init__(self):
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

    def aplicar_estilo_tabela_abnt(self, tabela):
        tbl_pr = tabela._element.xpath('w:tblPr')[0]
        tbl_borders = tbl_pr.find(qn('w:tblBorders'))
        if tbl_borders is None:
            tbl_borders = OxmlElement('w:tblBorders')
            tbl_pr.append(tbl_borders)
        for border in tbl_borders.findall(qn('w:*')):
            tbl_borders.remove(border)
        for border_name in ['top', 'bottom', 'insideH']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), 'auto')
            tbl_borders.append(border)
        for border_name in ['left', 'right', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'nil')
            tbl_borders.append(border)

    def aplicar_estilo_legenda(self, paragrafo, is_titulo=True):
        paragrafo.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER if is_titulo else WD_PARAGRAPH_ALIGNMENT.LEFT
        paragrafo.paragraph_format.space_before = Pt(0) if is_titulo else Pt(6)
        paragrafo.paragraph_format.space_after = Pt(6) if is_titulo else Pt(12)
        paragrafo.paragraph_format.line_spacing = 1.0
        for run in paragrafo.runs:
            run.font.name = self.FONTE_PADRAO
            run.font.size = self.TAMANHO_FONTE_LEGENDA

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