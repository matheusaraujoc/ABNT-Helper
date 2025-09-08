# gerador_docx.py
# Descrição: Versão final do Construtor, com automação total do sumário via MS Word.

import os
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from documento import DocumentoABNT
from normas_abnt import MotorNormasABNT

# --- ## NOVO CÓDIGO: Import para automação do Word ## ---
try:
    import win32com.client as win32
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("AVISO: Biblioteca 'pywin32' não encontrada. A automação do sumário será desativada.")

def adicionar_sumario(doc, paragrafo):
    run = paragrafo.add_run()
    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

class GeradorDOCX:
    def __init__(self, doc_abnt: DocumentoABNT):
        self.doc_abnt = doc_abnt
        self.doc = Document()
        self.regras = MotorNormasABNT()
        self.regras.configurar_pagina_e_estilos(self.doc)

    # --- ## NOVO CÓDIGO: Método para controlar o Word ## ---
    def _atualizar_sumario_com_word(self, caminho_arquivo):
        """
        Abre o Word em segundo plano para forçar a atualização do sumário.
        Requer Windows e MS Word instalado.
        """
        if not WIN32_AVAILABLE:
            print("Não foi possível atualizar o sumário: pywin32 não está instalado.")
            return False

        try:
            print("Iniciando automação do MS Word para atualizar o sumário...")
            word = win32.DispatchEx("Word.Application")
            word.Visible = False # Roda invisível
            
            # Converte o caminho relativo para absoluto, essencial para o Word
            doc_path = os.path.abspath(caminho_arquivo)
            
            doc = word.Documents.Open(doc_path)
            
            # Atualiza todos os campos do documento (TOC, números de página, etc.)
            doc.Fields.Update()
            
            doc.Save()
            doc.Close(SaveChanges=False)
            
            print("Sumário atualizado com sucesso.")
            return True
        except Exception as e:
            print(f"ERRO: Falha ao automatizar o Word para atualizar o sumário: {e}")
            return False
        finally:
            if 'word' in locals():
                word.Quit()

    def gerar_documento(self, caminho_arquivo: str):
        # ... (código de renderização pré-textual, textual, pós-textual) ...
        # Pré-textuais
        self._renderizar_capa()
        self._renderizar_folha_rosto()
        self._renderizar_resumo()
        
        # Início da seção textual
        section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._set_page_numbering(section)

        # Textuais
        self._renderizar_sumario()
        
        for i, capitulo in enumerate(self.doc_abnt.capitulos, 1):
            self._renderizar_capitulo(capitulo, i)

        # Pós-textuais
        self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._renderizar_referencias()

        # Salva o documento pela primeira vez
        self.doc.save(caminho_arquivo)
        
        # --- ## ALTERADO: Chama a automação do Word após salvar ## ---
        # Tenta atualizar o sumário automaticamente
        self._atualizar_sumario_com_word(caminho_arquivo)

    def _renderizar_sumario(self):
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero="", titulo_texto="SUMÁRIO")
        paragrafo_sumario = self.doc.add_paragraph()
        adicionar_sumario(self.doc, paragrafo_sumario)
        self.doc.add_page_break()

    # --- O restante do arquivo (métodos de renderização) permanece o mesmo ---
    def _set_page_numbering(self, section):
        # (código sem alterações)
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
        # (código sem alterações)
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
        # (código sem alterações)
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
        texto_natureza = f"{self.doc_abnt.configuracoes.tipo_trabalho} apresentado ao curso de {self.doc_abnt.configuracoes.curso} da {self.doc_abnt.configuracoes.instituicao}, como requisito parcial para a obtenção do título de Bacharel."
        p_natureza = self.doc.add_paragraph()
        self.regras.aplicar_estilo_natureza_trabalho(p_natureza, texto_natureza)
        self.doc.add_paragraph()
        p_orientador = self.doc.add_paragraph()
        self.regras.aplicar_estilo_natureza_trabalho(p_orientador, f"Orientador(a): {self.doc_abnt.orientador}")
        p_final = self.doc.add_paragraph('\n' * 5)
        p_final.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_final.add_run(f"{self.doc_abnt.configuracoes.cidade.upper()}\n{self.doc_abnt.configuracoes.ano}")
        self.doc.add_page_break()
    
    def _renderizar_resumo(self):
        # (código sem alterações)
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero="", titulo_texto="RESUMO")
        p_resumo = self.doc.add_paragraph()
        self.regras.aplicar_estilo_resumo(p_resumo, self.doc_abnt.resumo)
        self.doc.add_paragraph()
        p_kw = self.doc.add_paragraph()
        run_kw = p_kw.add_run("Palavras-chave: ")
        run_kw.bold = True
        texto_kw = self.doc_abnt.palavras_chave.replace(';', '.') + "."
        p_kw.add_run(texto_kw)

    def _renderizar_capitulo(self, capitulo, numero):
        # (código sem alterações)
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero, capitulo.titulo)
        p = self.doc.add_paragraph()
        self.regras.aplicar_estilo_paragrafo_normal(p, capitulo.conteudo)

    def _renderizar_referencias(self):
        # (código sem alterações)
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero="", titulo_texto="REFERÊNCIAS")
        self.doc_abnt.ordenar_referencias()
        for ref in self.doc_abnt.referencias:
            p_ref = self.doc.add_paragraph()
            self.regras.aplicar_estilo_referencia(p_ref, ref.formatar())