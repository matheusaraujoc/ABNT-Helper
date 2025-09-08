# gerador_docx.py
# Descrição: O Construtor. Aprimorado com a capacidade de gerar um sumário clicável.

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.section import WD_SECTION

# --- ## NOVO CÓDIGO: Imports necessários para manipular o XML ## ---
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from documento import DocumentoABNT
from normas_abnt import MotorNormasABNT

# --- ## NOVO CÓDIGO: Função auxiliar para criar o sumário (TOC) ## ---
def adicionar_sumario(doc, paragrafo):
    """
    Insere um campo de Tabela de Conteúdo (TOC) clicável em um parágrafo.
    Esta função manipula o XML subjacente do documento.
    """
    run = paragrafo.add_run()
    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'begin')
    
    # Define as instruções do sumário:
    # \o "1-3" -> Usar níveis de título de 1 a 3
    # \h -> Criar hyperlinks
    # \z -> Ocultar o sumário na visualização web
    # \u -> Usar os níveis de estrutura de tópicos aplicados
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'

    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')

    fldChar3 = OxmlElement('w:t')
    fldChar3.text = "Clique com o botão direito e 'Atualizar Campo' para gerar o sumário."
    
    fldChar4 = OxmlElement('w:fldChar')
    fldChar4.set(qn('w:fldCharType'), 'end')

    run._r.append(fldChar)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)
    run._r.append(fldChar4)
# --- FIM DO NOVO CÓDIGO ---


class GeradorDOCX:
    def __init__(self, doc_abnt: DocumentoABNT):
        self.doc_abnt = doc_abnt
        self.doc = Document()
        self.regras = MotorNormasABNT()
        self.regras.configurar_pagina_e_estilos(self.doc)

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
        
    def gerar_documento(self, caminho_arquivo: str):
        # Pré-textuais
        self._renderizar_capa()
        self._renderizar_folha_rosto()
        self._renderizar_resumo()
        
        # Início da seção textual
        section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._set_page_numbering(section)

        # Textuais
        # --- ## ALTERADO: Chama o novo método de sumário ## ---
        self._renderizar_sumario_real()
        
        for i, capitulo in enumerate(self.doc_abnt.capitulos, 1):
            self._renderizar_capitulo(capitulo, i)

        # Pós-textuais
        self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._renderizar_referencias()

        self.doc.save(caminho_arquivo)

    # --- Métodos _renderizar_capa, _renderizar_folha_rosto, _renderizar_resumo (sem alterações) ---
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
        
        p_final = self.doc.add_paragraph('\n' * 10) # Espaçamento
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
        
        self.doc.add_paragraph() # Espaço

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
        
        self.doc.add_paragraph() # Espaço
        
        p_kw = self.doc.add_paragraph()
        run_kw = p_kw.add_run("Palavras-chave: ")
        run_kw.bold = True
        texto_kw = self.doc_abnt.palavras_chave.replace(';', '.') + "."
        p_kw.add_run(texto_kw)

    # --- ## ALTERADO: Novo método para o sumário real ## ---
    def _renderizar_sumario_real(self):
        """Renderiza o título do sumário e insere o campo de TOC."""
        self.regras.aplicar_estilo_titulo_secao(self.doc, numero="", titulo_texto="SUMÁRIO")
        
        # Adiciona um parágrafo onde o sumário será inserido
        paragrafo_sumario = self.doc.add_paragraph()
        
        # Chama a função auxiliar para inserir o código do sumário
        adicionar_sumario(self.doc, paragrafo_sumario)

        # Adiciona uma instrução final para o usuário
        p_instrucao = self.doc.add_paragraph()
        run_instrucao = p_instrucao.add_run(
            "\n(Para gerar o sumário, clique com o botão direito no texto acima e selecione 'Atualizar Campo')"
        )
        run_instrucao.font.size = Pt(10)
        run_instrucao.italic = True
        p_instrucao.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        self.doc.add_page_break()
        
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