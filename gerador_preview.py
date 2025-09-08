# gerador_preview.py
# Descrição: Corrigida a formatação dos nomes dos autores na capa e folha de rosto.

import os
import re
from documento import DocumentoABNT, Capitulo
from referencia import formatar_autores

# --- CONSTANTES DE ESTIMATIVA DE ALTURA (EM CM) ---
ALTURA_CONTEUDO_PAGINA = 24.7  # (29.7cm - 3cm margem sup - 2cm margem inf)
ALTURA_LINHA_TEXTO = 0.6
ALTURA_TITULO_SECAO = 1.5
ALTURA_LEGENDA = 1.2
ALTURA_LINHA_TABELA = 0.8

class GeradorHTMLPreview:
    def __init__(self, doc_abnt: DocumentoABNT):
        self.doc_abnt = doc_abnt
        self.paginas_html = []
        self.conteudo_pagina_atual = []
        self.altura_restante = ALTURA_CONTEUDO_PAGINA
        self.contador_tabelas = 0
        self.contador_figuras = 0

    def _nova_pagina(self):
        """Finaliza a página atual e começa uma nova."""
        if self.conteudo_pagina_atual:
            pagina_conteudo = "".join(self.conteudo_pagina_atual)
            self.paginas_html.append(f'<div class="pagina">{pagina_conteudo}</div>')
        self.conteudo_pagina_atual = []
        self.altura_restante = ALTURA_CONTEUDO_PAGINA

    def _adicionar_elemento(self, html_elemento, altura_estimada):
        """Adiciona um elemento à página, quebrando-a se não houver espaço."""
        if html_elemento.startswith("<h1") and self.altura_restante < (altura_estimada + ALTURA_LINHA_TEXTO * 2):
            self._nova_pagina()
        if self.altura_restante < altura_estimada:
            self._nova_pagina()
        self.conteudo_pagina_atual.append(html_elemento)
        self.altura_restante -= altura_estimada

    def gerar_html(self) -> str:
        """Gera o código HTML completo da pré-visualização paginada."""
        cfg = self.doc_abnt.configuracoes
        
        html_style = """
        <style>
            body { font-family: 'Times New Roman', Times, serif; font-size: 12pt; background-color: #E0E0E0; }
            .pagina {
                width: 21cm; height: 29.7cm; padding: 3cm 2cm 2cm 3cm;
                margin: 20px auto; background-color: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.2); box-sizing: border-box;
                position: relative; overflow: hidden; /* Esconde o conteúdo que vazar */
            }
            h1 { font-size: 12pt; font-weight: bold; text-transform: uppercase; margin-top: 1em; margin-bottom: 1em; }
            p { margin: 0; padding: 0; line-height: 1.5; }
            p.corpo-texto { text-align: justify; text-indent: 1.25cm; }
            .capa, .folha-rosto { text-align: center; }
            .capa p, .folha-rosto p { text-indent: 0; }
            .natureza { text-indent: 0; margin-left: 8cm; font-size: 11pt; text-align: justify; line-height: 1.5; }
            .resumo-paragrafo { text-indent: 1.25cm; text-align: justify; line-height: 1.5; }
            .resumo-titulo-palavras-chave { text-indent: 0; font-weight: bold; margin-top: 1em;}
            .referencia { text-align: justify; line-height: 1.0; margin-bottom: 12px; }
            .legenda { font-size: 10pt; text-align: center; text-indent: 0; line-height: 1.2; }
            .fonte { font-size: 10pt; text-align: left; text-indent: 0; line-height: 1.2; margin-top: 2px; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 10pt; }
            th, td { border: 1px solid black; padding: 4px; text-align: left; }
            table.abnt { border: none; }
            table.abnt th, table.abnt td { border: none; }
            table.abnt thead tr { border-top: 1px solid black; border-bottom: 1px solid black; }
            table.abnt tbody tr:last-of-type { border-bottom: 1px solid black; }
            img { display: block; margin: 1em auto; max-width: 100%; height: auto; }
            .posicao-final-pagina { position: absolute; bottom: 2cm; width: 16cm; left: 3cm; text-align: center; }
        </style>
        """
        
        # --- ## CORREÇÃO: Formatação dos nomes dos autores para capa/rosto ## ---
        # ABNT para capa/rosto pede nomes completos, um por linha. Usamos <br> para isso em HTML.
        autores_capa_html = "<br>".join([a.nome_completo.upper() for a in self.doc_abnt.autores])

        # --- GERAÇÃO DAS PÁGINAS ---
        # Página da Capa
        self.conteudo_pagina_atual.append(f"""
        <div class="capa">
            <br><br><p><strong>{cfg.instituicao.upper()}</strong></p><br><br><br>
            <p><strong>{autores_capa_html}</strong></p>
            <br><br><br><br><p><strong>{self.doc_abnt.titulo.upper()}</strong></p>
            <div class="posicao-final-pagina"><p>{cfg.cidade.upper()}</p><p>{cfg.ano}</p></div>
        </div>""")
        self._nova_pagina()

        # Página da Folha de Rosto
        self.conteudo_pagina_atual.append(f"""
        <div class="folha-rosto">
             <br><br><br><br><p><strong>{autores_capa_html}</strong></p>
            <br><br><br><br><p><strong>{self.doc_abnt.titulo.upper()}</strong></p><br><br><br>
            <p class="natureza">{cfg.tipo_trabalho} apresentado ao curso de {cfg.modalidade_curso} em {cfg.curso} da {cfg.instituicao}, como requisito parcial para a obtenção do título de {cfg.titulo_pretendido}.</p>
            <br><p class="natureza">Orientador(a): {self.doc_abnt.orientador}</p>
            <div class="posicao-final-pagina"><p>{cfg.cidade.upper()}</p><p>{cfg.ano}</p></div>
        </div>""")
        self._nova_pagina()

        # Página de Resumo
        resumo_html = f"""<h1>RESUMO</h1><p class="resumo-paragrafo">{self.doc_abnt.resumo}</p><p><br></p><p class="resumo-titulo-palavras-chave">Palavras-chave: <span style="font-weight: normal;">{self.doc_abnt.palavras_chave.replace(';', '.')}.</span></p>"""
        altura_resumo = (len(self.doc_abnt.resumo) / 80 + 5) * ALTURA_LINHA_TEXTO
        self._adicionar_elemento(resumo_html, altura_resumo)
        self._nova_pagina()

        # Páginas de Conteúdo
        self._renderizar_secoes_recursivamente_html(self.doc_abnt.estrutura_textual)
        
        # Página de Referências
        self._nova_pagina() 
        self._adicionar_elemento("<h1>REFERÊNCIAS</h1>", ALTURA_TITULO_SECAO)
        self.doc_abnt.ordenar_referencias()
        for ref in self.doc_abnt.referencias:
            ref_formatada = ref.formatar().replace('**', '<strong>').replace('**', '</strong>')
            ref_html = f'<p class="referencia">{ref_formatada}</p>'
            altura_ref = (len(ref_formatada) / 100 + 1) * (ALTURA_LINHA_TEXTO * 0.8)
            self._adicionar_elemento(ref_html, altura_ref)

        self._nova_pagina()

        return f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{html_style}</head><body>{''.join(self.paginas_html)}</body></html>"

    def _renderizar_secoes_recursivamente_html(self, no_pai: Capitulo, prefixo_numeracao=""):
        # (código sem alterações)
        for i, no_filho in enumerate(no_pai.filhos, 1):
            numero_completo = f"{prefixo_numeracao}{i}"
            titulo_texto = f"{numero_completo} {no_filho.titulo.upper() if len(numero_completo.split('.')) == 1 else no_filho.titulo}"
            self._adicionar_elemento(f"<h1>{titulo_texto}</h1>", ALTURA_TITULO_SECAO)
            if no_filho.conteudo:
                padrao = r"\{\{(Tabela|Figura):([^}]+)\}\}"
                partes_conteudo = re.split(padrao, no_filho.conteudo)
                for k, parte in enumerate(partes_conteudo):
                    if k % 3 == 0:
                        for paragrafo in parte.strip().split('\n'):
                            if paragrafo.strip():
                                altura_paragrafo = (len(paragrafo) / 80 + 1) * ALTURA_LINHA_TEXTO
                                self._adicionar_elemento(f'<p class="corpo-texto">{paragrafo.strip()}</p>', altura_paragrafo)
                    elif k % 3 == 1:
                        tipo = parte
                        titulo = partes_conteudo[k+1]
                        if tipo == "Tabela":
                            tabela_obj = next((t for t in no_filho.tabelas if t.titulo == titulo), None)
                            if tabela_obj:
                                self.contador_tabelas += 1; tabela_obj.numero = self.contador_tabelas
                                altura_tabela = (len(tabela_obj.dados) * ALTURA_LINHA_TABELA) + (ALTURA_LEGENDA * 2)
                                self._adicionar_elemento(self._renderizar_tabela_html(tabela_obj), altura_tabela)
                        elif tipo == "Figura":
                            figura_obj = next((f for f in no_filho.figuras if f.titulo == titulo), None)
                            if figura_obj:
                                self.contador_figuras += 1; figura_obj.numero = self.contador_figuras
                                altura_figura = (figura_obj.largura_cm / 16 * 9) + (ALTURA_LEGENDA * 2)
                                self._adicionar_elemento(self._renderizar_figura_html(figura_obj), altura_figura)
            self._renderizar_secoes_recursivamente_html(no_filho, f"{numero_completo}.")

    def _renderizar_tabela_html(self, tabela) -> str:
        # (código sem alterações)
        classe_css = 'abnt' if tabela.estilo_borda == 'abnt' else ''
        html = f'<div><p class="legenda">Tabela {tabela.numero} – {tabela.titulo}</p><table class="{classe_css}" align="center">'
        if tabela.dados:
            html += '<thead><tr>'
            for header in tabela.dados[0]: html += f'<th>{header}</th>'
            html += '</tr></thead><tbody>'
            for row in tabela.dados[1:]:
                html += '<tr>'
                for cell in row: html += f'<td>{cell}</td>'
                html += '</tr>'
            html += '</tbody>'
        html += '</table>'
        if tabela.fonte: html += f'<p class="fonte">Fonte: {tabela.fonte}</p>'
        html += '</div>'
        return html

    def _renderizar_figura_html(self, figura) -> str:
        # (código sem alterações)
        caminho_abs = os.path.abspath(figura.caminho_processado)
        url_local = f"file:///{caminho_abs.replace(os.path.sep, '/')}"
        html = f'<div><img src="{url_local}" style="width: {figura.largura_cm}cm;">'
        html += f'<p class="legenda">Figura {figura.numero} – {figura.titulo}</p>'
        if figura.fonte: html += f'<p class="fonte">Fonte: {figura.fonte}</p>'
        html += '</div>'
        return html