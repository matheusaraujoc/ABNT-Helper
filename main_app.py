# main_app.py
# Descrição: Versão definitiva com todas as funcionalidades e importações corrigidas.

import sys
import os
import re
from datetime import datetime
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
                               QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, 
                               QMessageBox, QTabWidget, QComboBox, 
                               QFormLayout, QMenuBar, QCheckBox)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from documento import DocumentoABNT, Autor, Capitulo
from gerador_docx import GeradorDOCX
from referencia import Livro, Artigo, Site
from aba_conteudo import AbaConteudo
from gerador_preview import GeradorHTMLPreview
from gerenciador_projeto import GerenciadorProjetos
from dialogs import ReferenciaDialog, DialogoFigura
# A LINHA ABAIXO ESTAVA FALTANDO E CAUSAVA O ERRO. FOI RE-ADICIONADA.
from modelos_trabalho import get_estrutura_por_nome, get_nomes_modelos

class ABNTHelperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ABNT Helper Final')
        self.setGeometry(100, 100, 1200, 800)
        
        self.documento = DocumentoABNT()
        self.gerenciador_projeto = GerenciadorProjetos()
        self.caminho_projeto_atual = None
        self.modificado = False
        self._populando_ui = False

        self._build_ui()
        self._conectar_sinais_modificacao()
        
        self._novo_projeto(primeira_execucao=True)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        
        menu_bar = QMenuBar(self)
        main_layout.setMenuBar(menu_bar)
        
        menu_arquivo = menu_bar.addMenu("&Arquivo")
        acao_novo = QAction("&Novo Projeto", self)
        acao_novo.triggered.connect(self._novo_projeto)
        menu_arquivo.addAction(acao_novo)
        acao_carregar = QAction("&Carregar Projeto...", self); acao_carregar.triggered.connect(self._carregar_projeto)
        menu_arquivo.addAction(acao_carregar)
        menu_arquivo.addSeparator()
        acao_salvar = QAction("&Salvar", self); acao_salvar.setShortcut("Ctrl+S"); acao_salvar.triggered.connect(self._salvar_projeto)
        menu_arquivo.addAction(acao_salvar)
        acao_salvar_como = QAction("Salvar &Como...", self); acao_salvar_como.triggered.connect(self._salvar_projeto_como)
        menu_arquivo.addAction(acao_salvar_como)
        menu_arquivo.addSeparator()
        acao_sair = QAction("Sai&r", self); acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)

        menu_editar = menu_bar.addMenu("&Editar")
        acao_localizar = QAction("&Localizar...", self)
        acao_localizar.setShortcut(QKeySequence.StandardKey.Find) # Atalho Ctrl+F
        acao_localizar.triggered.connect(self._alternar_barra_busca)
        menu_editar.addAction(acao_localizar)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.aba_conteudo = AbaConteudo(self.documento)
        
        self.tabs.addTab(self._criar_aba_geral(), "Geral e Pré-Textual")
        self.tabs.addTab(self.aba_conteudo, "Conteúdo Textual (Estrutura)")
        self.tabs.addTab(self._criar_aba_referencias(), "Referências")
        self.tabs.addTab(self._criar_aba_preview(), "Pré-Visualização")
        
        self.generate_btn = QPushButton("Gerar Documento .docx Final")
        self.generate_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.generate_btn.clicked.connect(self._gerar_documento_final)
        main_layout.addWidget(self.generate_btn)

    def _criar_aba_geral(self):
        widget = QWidget(); layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<h3>Configurações do Documento</h3>"))
        form_layout1 = QFormLayout(); self.cfg_tipo = QComboBox()
        self.cfg_tipo.addItems(get_nomes_modelos())
        self.cfg_tipo.currentTextChanged.connect(self._on_template_selecionado)
        self.cfg_instituicao = QLineEdit(); self.cfg_curso = QLineEdit()
        self.cfg_modalidade_curso = QLineEdit(); self.cfg_titulo_pretendido = QLineEdit()
        self.cfg_cidade = QLineEdit(); self.cfg_ano = QLineEdit()
        form_layout1.addRow("Tipo de Trabalho:", self.cfg_tipo); form_layout1.addRow("Instituição:", self.cfg_instituicao)
        form_layout1.addRow("Nome do Curso (Ex: Ciência da Computação):", self.cfg_curso); form_layout1.addRow("Modalidade do Curso (Ex: Bacharelado):", self.cfg_modalidade_curso)
        form_layout1.addRow("Título Pretendido (Ex: Bacharel):", self.cfg_titulo_pretendido); form_layout1.addRow("Cidade:", self.cfg_cidade)
        form_layout1.addRow("Ano:", self.cfg_ano); layout.addLayout(form_layout1)
        layout.addWidget(QLabel("<h3>Informações Pré-Textuais</h3>"))
        form_layout2 = QFormLayout(); self.titulo_input = QLineEdit(); self.autores_input = QTextEdit()
        self.orientador_input = QLineEdit(); self.resumo_input = QTextEdit(); self.keywords_input = QLineEdit()
        form_layout2.addRow("Título do Trabalho:", self.titulo_input); form_layout2.addRow("Autores (um por linha):", self.autores_input)
        form_layout2.addRow("Orientador(a):", self.orientador_input); form_layout2.addRow("Resumo:", self.resumo_input)
        form_layout2.addRow("Palavras-chave (separadas por ;):", self.keywords_input); layout.addLayout(form_layout2)
        return widget
        
    def _criar_aba_referencias(self):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.addWidget(QLabel("<h3>Gerenciador de Referências</h3>"))
        self.lista_referencias = QtWidgets.QListWidget(); self.lista_referencias.itemDoubleClicked.connect(self._editar_referencia)
        layout.addWidget(self.lista_referencias); btn_layout = QHBoxLayout(); btn_add = QPushButton("Adicionar")
        btn_edit = QPushButton("Editar Selecionada"); btn_del = QPushButton("Remover Selecionada")
        btn_layout.addWidget(btn_add); btn_layout.addWidget(btn_edit); btn_layout.addWidget(btn_del)
        btn_add.clicked.connect(self._adicionar_referencia); btn_edit.clicked.connect(self._editar_referencia)
        btn_del.clicked.connect(self._remover_referencia); layout.addLayout(btn_layout)
        return widget

    def _criar_aba_preview(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.busca_toolbar = QWidget()
        busca_layout = QHBoxLayout(self.busca_toolbar)
        busca_layout.setContentsMargins(0, 5, 0, 5)
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText("Buscar no documento...")
        btn_buscar_anterior = QPushButton("Anterior")
        btn_buscar_proximo = QPushButton("Próximo")
        self.busca_case_sensitive = QCheckBox("Diferenciar M/m")
        btn_fechar_busca = QPushButton("Fechar")
        btn_atualizar = QPushButton("Atualizar Pré-Visualização")
        busca_layout.addWidget(QLabel("Localizar:"))
        busca_layout.addWidget(self.busca_input)
        busca_layout.addWidget(btn_buscar_anterior)
        busca_layout.addWidget(btn_buscar_proximo)
        busca_layout.addWidget(self.busca_case_sensitive)
        busca_layout.addStretch()
        busca_layout.addWidget(btn_fechar_busca)
        layout.addWidget(self.busca_toolbar)
        self.busca_toolbar.setVisible(False)
        self.preview_display = QWebEngineView()
        self.preview_display.setHtml("<html><body><h1>Pré-Visualização</h1><p>Clique em 'Atualizar' para ver o seu documento.</p></body></html>")
        layout.addWidget(self.preview_display, 1)
        layout.addWidget(btn_atualizar)
        btn_atualizar.clicked.connect(self._atualizar_preview)
        btn_buscar_proximo.clicked.connect(self._buscar_proximo_preview)
        btn_buscar_anterior.clicked.connect(self._buscar_anterior_preview)
        self.busca_input.returnPressed.connect(self._buscar_proximo_preview)
        btn_fechar_busca.clicked.connect(self._alternar_barra_busca)
        return widget

    @QtCore.Slot()
    def _alternar_barra_busca(self):
        is_visible = self.busca_toolbar.isVisible()
        self.busca_toolbar.setVisible(not is_visible)
        if not is_visible:
            self.busca_input.setFocus()

    def _buscar_preview(self, direcao_reversa=False):
        texto_busca = self.busca_input.text()
        if not texto_busca: return
        flags = QWebEnginePage.FindFlag(0)
        if direcao_reversa: flags |= QWebEnginePage.FindFlag.FindBackward
        if self.busca_case_sensitive.isChecked(): flags |= QWebEnginePage.FindFlag.FindCaseSensitively
        self.preview_display.findText(texto_busca, flags)

    @QtCore.Slot()
    def _buscar_proximo_preview(self):
        self._buscar_preview(direcao_reversa=False)

    @QtCore.Slot()
    def _buscar_anterior_preview(self):
        self._buscar_preview(direcao_reversa=True)
        
    @QtCore.Slot(bool)
    def _novo_projeto(self, primeira_execucao=False):
        if not primeira_execucao and not self._verificar_alteracoes_nao_salvas():
            return
        self.documento = DocumentoABNT()
        estrutura_padrao = get_estrutura_por_nome("Trabalho de Conclusão de Curso (TCC)")
        for titulo in estrutura_padrao:
            self.documento.estrutura_textual.adicionar_filho(Capitulo(titulo=titulo, is_template_item=True))
        self.caminho_projeto_atual = None
        self.gerenciador_projeto.fechar_projeto()
        if hasattr(self, 'cfg_tipo'):
             self._popular_ui_com_documento()
        self.modificado = False
        self.setWindowTitle('ABNT Helper Final - Novo Projeto (TCC)')
    
    @QtCore.Slot(str)
    def _on_template_selecionado(self, nome_modelo):
        if self._populando_ui or not nome_modelo: return
        if nome_modelo == self.documento.configuracoes.tipo_trabalho: return
        resposta = QMessageBox.question(self, "Mudar Modelo de Trabalho",
                                          f"Mudar o modelo para '{nome_modelo}' irá reorganizar sua estrutura de capítulos.\n"
                                          "Capítulos existentes serão preservados. Capítulos que não pertencem ao novo modelo e que contêm conteúdo serão movidos para o final.\n\n"
                                          "Deseja continuar?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resposta == QMessageBox.StandardButton.No:
            self._populando_ui = True
            self.cfg_tipo.setCurrentText(self.documento.configuracoes.tipo_trabalho)
            self._populando_ui = False
            return
        mapa_capitulos_atuais = {c.titulo.upper().strip(): c for c in self.documento.estrutura_textual.filhos}
        titulos_novos = get_estrutura_por_nome(nome_modelo)
        nova_lista_de_capitulos = []
        for titulo_novo in titulos_novos:
            titulo_normalizado = titulo_novo.upper().strip()
            if titulo_normalizado in mapa_capitulos_atuais:
                capitulo_existente = mapa_capitulos_atuais.pop(titulo_normalizado)
                capitulo_existente.is_template_item = True
                nova_lista_de_capitulos.append(capitulo_existente)
            else:
                nova_lista_de_capitulos.append(Capitulo(titulo=titulo_novo, is_template_item=True))
        capitulos_orfaos_com_conteudo = []
        for orfao in mapa_capitulos_atuais.values():
            if orfao.conteudo.strip() or orfao.filhos:
                orfao.is_template_item = False
                capitulos_orfaos_com_conteudo.append(orfao)
        if capitulos_orfaos_com_conteudo:
            nova_lista_de_capitulos.extend(capitulos_orfaos_com_conteudo)
            QMessageBox.information(self, "Capítulos Preservados",
                                    "Alguns capítulos da estrutura anterior que continham conteúdo "
                                    "não fazem parte do novo modelo e foram movidos para o final.\n"
                                    "Capítulos órfãos que estavam vazios foram descartados.")
        self.documento.estrutura_textual.filhos = nova_lista_de_capitulos
        for filho in self.documento.estrutura_textual.filhos:
            filho.pai = self.documento.estrutura_textual
        self.aba_conteudo._popular_arvore()
        self.documento.configuracoes.tipo_trabalho = nome_modelo
        self._marcar_modificado()

    def _salvar_projeto(self):
        if not self.caminho_projeto_atual:
            self._salvar_projeto_como()
            return
        self.aba_conteudo.sincronizar_conteudo_pendente()
        self._sincronizar_modelo_com_ui()
        try:
            self.gerenciador_projeto.salvar_projeto(self.documento, self.caminho_projeto_atual)
            self.modificado = False
            self.setWindowTitle(f'ABNT Helper Final - {os.path.basename(self.caminho_projeto_atual)}')
            QMessageBox.information(self, "Sucesso", "Projeto salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o projeto:\n{e}")

    def _salvar_projeto_como(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Projeto Como...", "", "Arquivo ABNF (*.abnf)")
        if caminho:
            self.caminho_projeto_atual = caminho
            self._salvar_projeto()

    def _carregar_projeto(self):
        if self._verificar_alteracoes_nao_salvas():
            caminho, _ = QFileDialog.getOpenFileName(self, "Carregar Projeto", "", "Arquivo ABNF (*.abnf)")
            if caminho:
                try:
                    self.documento = self.gerenciador_projeto.carregar_projeto(caminho)
                    self.caminho_projeto_atual = caminho
                    self._popular_ui_com_documento()
                    self.modificado = False
                    self.setWindowTitle(f'ABNT Helper Final - {os.path.basename(caminho)}')
                    QMessageBox.information(self, "Sucesso", "Projeto carregado com sucesso!")
                except Exception as e:
                    QMessageBox.critical(self, "Erro ao Carregar", f"Não foi possível carregar o projeto:\n{e}")
                    self.gerenciador_projeto.fechar_projeto()

    def _popular_ui_com_documento(self):
        self._populando_ui = True
        cfg = self.documento.configuracoes
        self.cfg_tipo.setCurrentText(cfg.tipo_trabalho)
        self.cfg_instituicao.setText(cfg.instituicao); self.cfg_curso.setText(cfg.curso)
        self.cfg_modalidade_curso.setText(cfg.modalidade_curso); self.cfg_titulo_pretendido.setText(cfg.titulo_pretendido)
        self.cfg_cidade.setText(cfg.cidade); self.cfg_ano.setText(str(cfg.ano))
        self.titulo_input.setText(self.documento.titulo)
        self.autores_input.setPlainText('\n'.join([a.nome_completo for a in self.documento.autores]))
        self.orientador_input.setText(self.documento.orientador)
        self.resumo_input.setPlainText(self.documento.resumo)
        self.keywords_input.setText(self.documento.palavras_chave)
        self.aba_conteudo.documento = self.documento
        self.aba_conteudo._popular_arvore()
        if self.aba_conteudo.arvore_capitulos.topLevelItemCount() > 0:
            self.aba_conteudo.arvore_capitulos.setCurrentItem(self.aba_conteudo.arvore_capitulos.topLevelItem(0))
        else:
            self.aba_conteudo._carregar_capitulo_no_editor(None, None)
        self.lista_referencias.clear()
        for ref in self.documento.referencias:
            self.lista_referencias.addItem(ref.formatar().replace('**', ''))
        self._populando_ui = False

    def _verificar_alteracoes_nao_salvas(self) -> bool:
        if not self.modificado: return True
        resposta = QMessageBox.question(self, "Salvar Alterações?",
                                          "Você tem alterações não salvas. Deseja salvá-las?",
                                          QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if resposta == QMessageBox.StandardButton.Cancel: return False
        if resposta == QMessageBox.StandardButton.Save: self._salvar_projeto()
        return True

    def _marcar_modificado(self):
        if self._populando_ui: return
        if not self.modificado:
            self.modificado = True
            self.setWindowTitle(self.windowTitle() + '*')
        
    def _conectar_sinais_modificacao(self):
        self.cfg_tipo.currentTextChanged.connect(self._marcar_modificado)
        self.cfg_instituicao.textChanged.connect(self._marcar_modificado); self.cfg_curso.textChanged.connect(self._marcar_modificado)
        self.cfg_modalidade_curso.textChanged.connect(self._marcar_modificado); self.cfg_titulo_pretendido.textChanged.connect(self._marcar_modificado)
        self.cfg_cidade.textChanged.connect(self._marcar_modificado); self.cfg_ano.textChanged.connect(self._marcar_modificado)
        self.titulo_input.textChanged.connect(self._marcar_modificado); self.autores_input.textChanged.connect(self._marcar_modificado)
        self.orientador_input.textChanged.connect(self._marcar_modificado); self.resumo_input.textChanged.connect(self._marcar_modificado)
        self.keywords_input.textChanged.connect(self._marcar_modificado)
        self.aba_conteudo.editor_capitulo.textChanged.connect(self._marcar_modificado)
        self.aba_conteudo.arvore_capitulos.estruturaAlterada.connect(self._marcar_modificado)
        self.aba_conteudo.arvore_capitulos.itemChanged.connect(self._marcar_modificado)

    def closeEvent(self, event):
        if self._verificar_alteracoes_nao_salvas():
            self.gerenciador_projeto.fechar_projeto()
            event.accept()
        else:
            event.ignore()

    @QtCore.Slot()
    def _adicionar_referencia(self):
        dialog = ReferenciaDialog(parent=self)
        if dialog.exec():
            nova_ref = dialog.get_data()
            if nova_ref:
                self.documento.referencias.append(nova_ref); self.lista_referencias.addItem(nova_ref.formatar().replace('**', ''))
                self._marcar_modificado()

    @QtCore.Slot()
    def _editar_referencia(self):
        linha = self.lista_referencias.currentRow()
        if linha == -1: QMessageBox.warning(self, "Atenção", "Nenhuma referência selecionada para editar."); return
        ref_para_editar = self.documento.referencias[linha]; dialog = ReferenciaDialog(ref=ref_para_editar, parent=self)
        if dialog.exec():
            ref_atualizada = dialog.get_data()
            if ref_atualizada:
                self.documento.referencias[linha] = ref_atualizada; item_lista = self.lista_referencias.item(linha)
                item_lista.setText(ref_atualizada.formatar().replace('**', ''))
                self._marcar_modificado()

    @QtCore.Slot()
    def _remover_referencia(self):
        linha = self.lista_referencias.currentRow()
        if linha == -1: return
        if QMessageBox.question(self, "Confirmar", "Remover esta referência?") == QMessageBox.StandardButton.Yes:
            self.lista_referencias.takeItem(linha); del self.documento.referencias[linha]
            self._marcar_modificado()
            
    def _sincronizar_modelo_com_ui(self):
        cfg = self.documento.configuracoes; cfg.tipo_trabalho = self.cfg_tipo.currentText()
        cfg.instituicao = self.cfg_instituicao.text(); cfg.curso = self.cfg_curso.text()
        cfg.modalidade_curso = self.cfg_modalidade_curso.text(); cfg.titulo_pretendido = self.cfg_titulo_pretendido.text()
        cfg.cidade = self.cfg_cidade.text(); cfg.ano = int(self.cfg_ano.text() or datetime.now().year)
        self.documento.titulo = self.titulo_input.text()
        self.documento.autores = [Autor(n.strip()) for n in self.autores_input.toPlainText().splitlines() if n.strip()]
        self.documento.orientador = self.orientador_input.text(); self.documento.resumo = self.resumo_input.toPlainText()
        self.documento.palavras_chave = self.keywords_input.text()

    @QtCore.Slot()
    def _atualizar_preview(self):
        self.aba_conteudo.sincronizar_conteudo_pendente()
        self._sincronizar_modelo_com_ui()
        self.preview_display.findText("") 
        gerador = GeradorHTMLPreview(self.documento)
        html_content = gerador.gerar_html()
        base_url = QtCore.QUrl.fromLocalFile(os.path.abspath(os.path.dirname(__file__)))
        self.preview_display.setHtml(html_content, baseUrl=base_url)
        QMessageBox.information(self, "Atualizado", "A pré-visualização foi atualizada com sucesso.")

    def _gerar_documento_final(self):
        self.aba_conteudo.sincronizar_conteudo_pendente()
        self._sincronizar_modelo_com_ui()
        if not self.documento.titulo or not self.documento.autores:
            QMessageBox.warning(self, "Erro", "Título e Autores são campos obrigatórios."); return
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Documento", "trabalho_abnt.docx", "Word Documents (*.docx)")
        if not filename: return
        try:
            gerador = GeradorDOCX(self.documento)
            gerador.gerar_documento(filename)
            QMessageBox.information(self, "Sucesso", f"Documento .docx gerado com sucesso em:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Geração", f"Ocorreu um erro: {e}")

if __name__ == '__main__':
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        print("ERRO: A dependência 'PySide6-WebEngineWidgets' não está instalada.")
        print("Por favor, execute: pip install PySide6-WebEngineWidgets")
        sys.exit(1)
        
    app = QApplication(sys.argv)
    win = ABNTHelperApp()
    win.show()
    sys.exit(app.exec())