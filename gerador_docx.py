# gerador_docx.py
# Descrição: Corrigido o erro de importação da unidade 'Cm'.

import os
from docx import Document
from docx.shared import Cm, Pt # ## CORREÇÃO: 'Cm' foi adicionado a esta linha ##
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from documento import DocumentoABNT, Capitulo
from normas_abnt import MotorNormasABNT

try:
    import win32com.client as win32
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("AVISO: Biblioteca 'pywin32' não encontrada. A automação do sumário será desativada.")

def adicionar_sumario(doc, paragrafo_placeholder):
    sdt = OxmlElement('w:sdt')
    sdtContent = OxmlElement('w:sdtContent')
    p = OxmlElement('w:p'); r = OxmlElement('w:r')
    fldChar_begin = OxmlElement('w:fldChar'); fldChar_begin.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar_separate = OxmlElement('w:fldChar'); fldChar_separate.set(qn('w:fldCharType'), 'separate')
    fldChar_end = OxmlElement('w:fldChar'); fldChar_end.set(qn('w:fldCharType'), 'end')
    r.append(fldChar_begin); r.append(instrText); r.append(fldChar_separate); r.append(fldChar_end)
    p.append(r); sdtContent.append(p); sdt.append(sdtContent)
    p_xml = paragrafo_placeholder._p; p_xml.addnext(sdt); p_xml.getparent().remove(p_xml)

class GeradorDOCX:
    def __init__(self, doc_abnt: DocumentoABNT):
        self.doc_abnt = doc_abnt
        self.doc = Document()
        self.regras = MotorNormasABNT()
        self.regras.configurar_pagina_e_estilos(self.doc)
        self.contador_tabelas = 0
        self.contador_figuras = 0

    def _atualizar_sumario_com_word(self, caminho_arquivo):
        if not WIN32_AVAILABLE:
            print("Não foi possível atualizar o sumário: pywin32 não está instalado.")
            return False
        word = None
        try:
            print("Iniciando automação do MS Word para reconstrução do sumário...")
            word = win32.DispatchEx("Word.Application")
            word.Visible = False
            doc_path = os.path.abspath(caminho_arquivo)
            doc = word.Documents.Open(doc_path)
            word.Selection.WholeStory()
            word.Selection.Fields.Update()
            doc.Save()
            doc.Close(SaveChanges=False)
            print("Sumário clicável gerado e atualizado com sucesso.")
            return True
        except Exception as e:
            print(f"ERRO: Falha ao automatizar o Word para atualizar o sumário: {e}")
            return False
        finally:
            if word is not None:
                word.Quit()
    
    def gerar_documento(self, caminho_arquivo: str):
        self._renderizar_capa()
        self._renderizar_folha_rosto()
        self._renderizar_resumo()
        section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._set_page_numbering(section)
        self._renderizar_sumario()
        self._renderizar_secoes_recursivamente(self.doc_abnt.estrutura_textual)
        self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._renderizar_referencias()
        self.doc.save(caminho_arquivo)
        self._atualizar_sumario_com_word(caminho_arquivo)
    
    def _renderizar_secoes_recursivamente(self, no_pai: Capitulo, prefixo_numeracao=""):
        for i, no_filho in enumerate(no_pai.filhos, 1):
            numero_completo = f"{prefixo_numeracao}{i}"
            nivel_titulo = len(numero_completo.split('.'))
            self.regras.aplicar_estilo_titulo_secao(self.doc, numero_completo, no_filho.titulo, nivel=nivel_titulo)
            if no_filho.conteudo:
                p = self.doc.add_paragraph()
                self.regras.aplicar_estilo_paragrafo_normal(p, no_filho.conteudo)
            if no_filho.tabelas:
                for tabela in no_filho.tabelas:
                    self.contador_tabelas += 1
                    tabela.numero = self.contador_tabelas
                    self._renderizar_tabela(tabela)
            if no_filho.figuras:
                for figura in no_filho.figuras:
                    self.contador_figuras += 1
                    figura.numero = self.contador_figuras
                    self._renderizar_figura(figura)
            self._renderizar_secoes_recursivamente(no_filho, prefixo_numeracao=f"{numero_completo}.")

    def _renderizar_tabela(self, tabela_obj):
        p_titulo = self.doc.add_paragraph()
        p_titulo.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run_titulo = p_titulo.add_run(f"Tabela {tabela_obj.numero} – {tabela_obj.titulo}")
        run_titulo.font.size = self.regras.TAMANHO_FONTE_LEGENDA
        p_titulo.paragraph_format.space_after = Pt(6)
        if not tabela_obj.dados: return
        num_rows = len(tabela_obj.dados)
        num_cols = len(tabela_obj.dados[0]) if num_rows > 0 else 0
        t = self.doc.add_table(rows=num_rows, cols=num_cols)
        t.style = 'Table Grid'
        for i, row_data in enumerate(tabela_obj.dados):
            for j, cell_data in enumerate(row_data):
                cell = t.cell(i, j)
                cell.text = cell_data
                p = cell.paragraphs[0]
                run = p.runs[0]
                run.font.name = self.regras.FONTE_PADRAO
                run.font.size = self.regras.TAMANHO_FONTE_LEGENDA
                if i == 0:
                    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        if tabela_obj.estilo_borda == 'abnt':
            self.regras.aplicar_estilo_tabela_abnt(t)
        if tabela_obj.fonte:
            fonte_texto = f"Fonte: {tabela_obj.fonte}"
            p_fonte = self.doc.add_paragraph()
            run_fonte = p_fonte.add_run(fonte_texto)
            run_fonte.font.size = self.regras.TAMANHO_FONTE_LEGENDA
            p_fonte.paragraph_format.space_before = Pt(6)

    def _renderizar_figura(self, figura_obj):
        p_imagem = self.doc.add_paragraph()
        p_imagem.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_imagem.add_run().add_picture(figura_obj.caminho_processado, width=Cm(figura_obj.largura_cm))
        p_imagem.paragraph_format.space_before = Pt(6)
        p_imagem.paragraph_format.space_after = Pt(0)
        p_titulo = self.doc.add_paragraph()
        p_titulo.add_run(f"Figura {figura_obj.numero} – {figura_obj.titulo}")
        self.regras.aplicar_estilo_legenda(p_titulo, is_titulo=True)
        if figura_obj.fonte:
            p_fonte = self.doc.add_paragraph()
            p_fonte.add_run(f"Fonte: {figura_obj.fonte}")
            self.regras.aplicar_estilo_legenda(p_fonte, is_titulo=False)

    def _set_page_numbering(self, section):
        section.header.is_linked_to_previous = False
        header_p = section.header.paragraphs[0]
        header_p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        run = header_p.add_run()
        fldChar_begin = OxmlElement('w:fldChar')
        fldChar_begin.set(qn('w:fldCharType'), 'begin')
        run._r.append(fldChar_begin)
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = 'PAGE'
        run._r.append(instrText)
        fldChar_end = OxmlElement('w:fldChar')
        fldChar_end.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar_end)
        
    def _renderizar_capa(self):
        p_inst = self.doc.add_paragraph()
        p_inst.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = p_inst.add_run(self.doc_abnt.configuracoes.instituicao.upper())
        run.bold = True
        self.doc.add_paragraph().add_run('\n')
        p_autores = self.doc.add_paragraph()
        p_autores.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        nomes_autores = '\n'.join([a.nome_completo.upper() for a in self.doc_abnt.autores])
        run = p_autores.add_run(nomes_autores)
        run.bold = True
        self.doc.add_paragraph().add_run('\n' * 2)
        p_titulo = self.doc.add_paragraph()
        p_titulo.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = p_titulo.add_run(self.doc_abnt.titulo.upper())
        run.bold = True
        run.font.size = self.regras.TAMANHO_FONTE_CAPA
        p_final = self.doc.add_paragraph('\n' * 10)
        p_final.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_final.add_run(f"{self.doc_abnt.configuracoes.cidade.upper()}\n{self.doc_abnt.configuracoes.ano}")
        self.doc.add_page_break()

    def _renderizar_folha_rosto(self):
        cfg = self.doc_abnt.configuracoes
        nomes_autores = '\n'.join([a.nome_completo.upper() for a in self.doc_abnt.autores])
        p_autores = self.doc.add_paragraph()
        p_autores.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_autores.add_run(nomes_autores).bold = True
        self.doc.add_paragraph('\n' * 2)
        p_titulo = self.doc.add_paragraph()
        p_titulo.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = p_titulo.add_run(self.doc_abnt.titulo.upper())
        run.bold = True
        run.font.size = self.regras.TAMANHO_FONTE_CAPA
        self.doc.add_paragraph('\n' * 2)
        texto_natureza = (f"{cfg.tipo_trabalho} apresentado ao curso de {cfg.modalidade_curso} em {cfg.curso} da {cfg.instituicao}, "
                         f"como requisito parcial para a obtenção do título de {cfg.titulo_pretendido}.")
        p_natureza = self.doc.add_paragraph()
        self.regras.aplicar_estilo_natureza_trabalho(p_natureza, texto_natureza)
        self.doc.add_paragraph()
        p_orientador = self.doc.add_paragraph()
        self.regras.aplicar_estilo_natureza_trabalho(p_orientador, f"Orientador(a): {self.doc_abnt.orientador}")
        p_final = self.doc.add_paragraph('\n' * 5)
        p_final.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_final.add_run(f"{cfg.cidade.upper()}\n{cfg.ano}")
        self.doc.add_page_break()
    
    def _renderizar_resumo(self):
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero="", titulo_texto="RESUMO")
        p_resumo = self.doc.add_paragraph()
        self.regras.aplicar_estilo_resumo(p_resumo, self.doc_abnt.resumo)
        self.doc.add_paragraph()
        p_kw = self.doc.add_paragraph()
        run_kw = p_kw.add_run("Palavras-chave: ")
        run_kw.bold = True
        texto_kw = self.doc_abnt.palavras_chave.replace(';', '.') + "."
        p_kw.add_run(texto_kw)

    def _renderizar_sumario(self):
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero="", titulo_texto="SUMÁRIO")
        paragrafo_placeholder = self.doc.add_paragraph()
        adicionar_sumario(self.doc, paragrafo_placeholder)
        self.doc.add_page_break()

    def _renderizar_referencias(self):
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero="", titulo_texto="REFERÊNCIAS")
        self.doc_abnt.ordenar_referencias()
        for ref in self.doc_abnt.referencias:
            p_ref = self.doc.add_paragraph()
            self.regras.aplicar_estilo_referencia(p_ref, ref.formatar())