# main_app.py
# Descrição: Versão com a proporção do QSplitter ajustada para um melhor equilíbrio.

import sys
import os

os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'

import shutil
from datetime import datetime
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
                               QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
                               QMessageBox, QTabWidget, QComboBox,
                               QFormLayout, QMenuBar, QCheckBox, QSplitter)
from PySide6.QtGui import QAction, QKeySequence, QActionGroup
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

# --- Assume que os arquivos abaixo estão na mesma pasta ---
from documento import DocumentoABNT, Autor, Capitulo
from gerador_docx import GeradorDOCX
from referencia import Livro, Artigo, Site
from aba_conteudo import AbaConteudo
from gerador_preview import GeradorHTMLPreview
from gerenciador_projeto import GerenciadorProjetos
from dialogs import ReferenciaDialog, DialogoFigura
from modelos_trabalho import get_estrutura_por_nome, get_nomes_modelos

# --- Imports para a tela inicial e gerenciamento de configuração/recuperação ---
from tela_inicial import TelaInicial
import gerenciador_config
import gerenciador_recuperacao
from dialogs import DialogoRecuperacao
# -------------------------------------------------------------------------------

class ABNTHelperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ABNT Helper Final')
        self.setGeometry(100, 100, 1400, 800)

        self.config = gerenciador_config.carregar_config()
        self.documento = DocumentoABNT()
        self.gerenciador_projeto = GerenciadorProjetos()
        self.caminho_projeto_atual = None
        self.modificado = False
        self._populando_ui = False
        
        self.wants_to_restart = False

        self.modo_preview = "lado_a_lado"
        self.preview_update_timer = QtCore.QTimer(self)
        self.preview_update_timer.setSingleShot(True)
        self.preview_update_timer.setInterval(750)
        self.preview_update_timer.timeout.connect(self._atualizar_preview)
        
        self.autosave_timer = QtCore.QTimer(self)
        intervalo_ms = self.config['recovery']['autosave_periodic_interval_min'] * 60 * 1000
        self.autosave_timer.setInterval(intervalo_ms)
        self.autosave_timer.timeout.connect(self._auto_salvar_recuperacao)
        
        self.scroll_posicao = 0
        self.main_layout = QVBoxLayout(self)
        self.main_content_widget = None

        self._build_ui()
        self._conectar_sinais_modificacao()
        gerenciador_recuperacao.setup_diretorios()

    def _build_ui(self):
        menu_bar = QMenuBar(self)
        self.main_layout.setMenuBar(menu_bar)

        menu_arquivo = menu_bar.addMenu("&Arquivo")
        
        acao_novo = QAction("&Novo Projeto", self)
        acao_novo.triggered.connect(self._novo_projeto)
        menu_arquivo.addAction(acao_novo)
        
        acao_carregar = QAction("&Carregar Projeto...", self)
        acao_carregar.triggered.connect(self._carregar_projeto)
        menu_arquivo.addAction(acao_carregar)
        menu_arquivo.addSeparator()

        acao_salvar = QAction("&Salvar", self)
        acao_salvar.setShortcut("Ctrl+S")
        acao_salvar.triggered.connect(self._salvar_projeto)
        menu_arquivo.addAction(acao_salvar)
        
        acao_salvar_como = QAction("Salvar &Como...", self)
        acao_salvar_como.triggered.connect(self._salvar_projeto_como)
        menu_arquivo.addAction(acao_salvar_como)
        menu_arquivo.addSeparator()

        acao_voltar = QAction("Voltar à Tela Inicial", self)
        acao_voltar.triggered.connect(self._voltar_tela_inicial)
        menu_arquivo.addAction(acao_voltar)
        menu_arquivo.addSeparator()

        acao_sair = QAction("Sai&r", self)
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)
        
        menu_editar = menu_bar.addMenu("&Editar")
        acao_localizar = QAction("&Localizar...", self)
        acao_localizar.setShortcut(QKeySequence.StandardKey.Find)
        acao_localizar.triggered.connect(self._alternar_barra_busca)
        menu_editar.addAction(acao_localizar)

        menu_visualizacao = menu_bar.addMenu("&Visualização")
        grupo_modos = QActionGroup(self)
        grupo_modos.setExclusive(True)
        
        self.acao_modo_lado_a_lado = QAction("Pré-visualização Lado a Lado", self, checkable=True)
        self.acao_modo_lado_a_lado.setChecked(True)
        self.acao_modo_lado_a_lado.triggered.connect(lambda: self._alternar_modo_preview("lado_a_lado"))
        menu_visualizacao.addAction(self.acao_modo_lado_a_lado)
        grupo_modos.addAction(self.acao_modo_lado_a_lado)
        
        self.acao_modo_aba = QAction("Pré-visualização como Aba", self, checkable=True)
        self.acao_modo_aba.triggered.connect(lambda: self._alternar_modo_preview("aba"))
        menu_visualizacao.addAction(self.acao_modo_aba)
        grupo_modos.addAction(self.acao_modo_aba)

        self.tabs = QTabWidget()
        self.aba_conteudo = AbaConteudo(self.documento)
        self.tabs.addTab(self._criar_aba_geral(), "Geral e Pré-Textual")
        self.tabs.addTab(self.aba_conteudo, "Conteúdo Textual (Estrutura)")
        self.tabs.addTab(self._criar_aba_referencias(), "Referências")
        self.preview_container = self._criar_painel_preview()

        self.generate_btn = QPushButton("Gerar Documento .docx Final")
        self.generate_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.generate_btn.clicked.connect(self._gerar_documento_final)
        self.main_layout.addWidget(self.generate_btn)

        self._reconfigurar_layout()

    @QtCore.Slot()
    def _voltar_tela_inicial(self):
        if self._verificar_alteracoes_nao_salvas():
            self.wants_to_restart = True
            self.close()

    @QtCore.Slot(str)
    def _alternar_modo_preview(self, novo_modo):
        if self.modo_preview != novo_modo:
            self.modo_preview = novo_modo
            self._reconfigurar_layout()

    def _reconfigurar_layout(self):
        if self.main_content_widget is not None:
            self.main_content_widget.setParent(None)
            if isinstance(self.main_content_widget, QSplitter):
                self.main_content_widget.deleteLater()
        self.main_content_widget = None
        
        if self.modo_preview == "lado_a_lado":
            index_preview = self.tabs.indexOf(self.preview_container)
            if index_preview != -1:
                self.tabs.removeTab(index_preview)
            self.btn_atualizar_preview.setVisible(False)
            splitter = QSplitter(QtCore.Qt.Orientation.Horizontal, self)
            splitter.addWidget(self.tabs)
            splitter.addWidget(self.preview_container)
            
            # --- AQUI ESTÁ A CORREÇÃO ---
            # Invertemos a proporção para dar mais espaço ao painel de edição
            splitter.setSizes([800, 600]) 
            
            self.main_content_widget = splitter
            self.preview_container.show()
        else:
            index_preview = self.tabs.indexOf(self.preview_container)
            if index_preview == -1:
                self.tabs.addTab(self.preview_container, "Pré-Visualização")
            self.btn_atualizar_preview.setVisible(True)
            self.main_content_widget = self.tabs
        
        self.main_layout.insertWidget(0, self.main_content_widget, 1)

    def _criar_aba_geral(self):
        # ... (código existente sem alterações)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<h3>Configurações do Documento</h3>"))
        
        form_layout1 = QFormLayout()
        self.cfg_tipo = QComboBox()
        self.cfg_tipo.addItems(get_nomes_modelos())
        self.cfg_tipo.currentTextChanged.connect(self._on_template_selecionado)
        self.cfg_instituicao = QLineEdit()
        self.cfg_curso = QLineEdit()
        self.cfg_modalidade_curso = QLineEdit()
        self.cfg_titulo_pretendido = QLineEdit()
        self.cfg_cidade = QLineEdit()
        self.cfg_ano = QLineEdit()
        form_layout1.addRow("Tipo de Trabalho:", self.cfg_tipo)
        form_layout1.addRow("Instituição:", self.cfg_instituicao)
        form_layout1.addRow("Nome do Curso (Ex: Ciência da Computação):", self.cfg_curso)
        form_layout1.addRow("Modalidade do Curso (Ex: Bacharelado):", self.cfg_modalidade_curso)
        form_layout1.addRow("Título Pretendido (Ex: Bacharel):", self.cfg_titulo_pretendido)
        form_layout1.addRow("Cidade:", self.cfg_cidade)
        form_layout1.addRow("Ano:", self.cfg_ano)
        layout.addLayout(form_layout1)
        
        layout.addWidget(QLabel("<h3>Informações Pré-Textuais</h3>"))
        form_layout2 = QFormLayout()
        self.titulo_input = QLineEdit()
        self.autores_input = QTextEdit()
        self.orientador_input = QLineEdit()
        self.resumo_input = QTextEdit()
        self.keywords_input = QLineEdit()
        form_layout2.addRow("Título do Trabalho:", self.titulo_input)
        form_layout2.addRow("Autores (um por linha):", self.autores_input)
        form_layout2.addRow("Orientador(a):", self.orientador_input)
        form_layout2.addRow("Resumo:", self.resumo_input)
        form_layout2.addRow("Palavras-chave (separadas por ;):", self.keywords_input)
        layout.addLayout(form_layout2)
        
        return widget

    def _criar_aba_referencias(self):
        # ... (código existente sem alterações)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<h3>Gerenciador de Referências</h3>"))
        
        self.lista_referencias = QtWidgets.QListWidget()
        self.lista_referencias.itemDoubleClicked.connect(self._editar_referencia)
        layout.addWidget(self.lista_referencias)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Adicionar")
        btn_edit = QPushButton("Editar Selecionada")
        btn_del = QPushButton("Remover Selecionada")
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_add.clicked.connect(self._adicionar_referencia)
        btn_edit.clicked.connect(self._editar_referencia)
        btn_del.clicked.connect(self._remover_referencia)
        layout.addLayout(btn_layout)
        
        return widget

    def _criar_painel_preview(self):
        # ... (código existente sem alterações)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        
        self.busca_toolbar = QWidget()
        busca_layout = QHBoxLayout(self.busca_toolbar)
        busca_layout.setContentsMargins(2, 5, 2, 5)
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText("Buscar na pré-visualização...")
        btn_buscar_anterior = QPushButton("Anterior")
        btn_buscar_proximo = QPushButton("Próximo")
        self.busca_case_sensitive = QCheckBox("Diferenciar M/m")
        btn_fechar_busca = QPushButton("Fechar")
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
        self.preview_display.setHtml("<html><body><h1>Pré-Visualização</h1><p>A pré-visualização será atualizada aqui.</p></body></html>")
        self.preview_display.setZoomFactor(0.75)
        self.preview_display.loadFinished.connect(self._restaurar_scroll_preview)
        layout.addWidget(self.preview_display, 1)
        
        self.btn_atualizar_preview = QPushButton("Atualizar Pré-Visualização")
        self.btn_atualizar_preview.clicked.connect(self._atualizar_preview)
        self.btn_atualizar_preview.setVisible(False)
        layout.addWidget(self.btn_atualizar_preview)
        
        btn_buscar_proximo.clicked.connect(self._buscar_proximo_preview)
        btn_buscar_anterior.clicked.connect(self._buscar_anterior_preview)
        self.busca_input.returnPressed.connect(self._buscar_proximo_preview)
        btn_fechar_busca.clicked.connect(self._alternar_barra_busca)
        
        return widget

    # ... (O restante do arquivo, a partir daqui, não precisa de alterações)
    # ... (Ele será idêntico ao que você já tem)

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
        if direcao_reversa:
            flags |= QWebEnginePage.FindFlag.FindBackward
        if self.busca_case_sensitive.isChecked():
            flags |= QWebEnginePage.FindFlag.FindCaseSensitively
        self.preview_display.findText(texto_busca, flags)

    @QtCore.Slot()
    def _buscar_proximo_preview(self):
        self._buscar_preview(direcao_reversa=False)
        
    @QtCore.Slot()
    def _buscar_anterior_preview(self):
        self._buscar_preview(direcao_reversa=True)
        
    @QtCore.Slot()
    def _disparar_atualizacao_automatica(self):
        if self.modo_preview == "lado_a_lado":
            self.preview_update_timer.start()
            
    def _salvar_scroll_preview(self):
        self.preview_display.page().runJavaScript("window.scrollY;", self._on_scroll_posicao_recebida)
        
    @QtCore.Slot(object)
    def _on_scroll_posicao_recebida(self, result):
        if isinstance(result, (int, float)):
            self.scroll_posicao = result
            
    @QtCore.Slot()
    def _restaurar_scroll_preview(self):
        self.preview_display.page().runJavaScript(f"window.scrollTo(0, {self.scroll_posicao});")

    @QtCore.Slot()
    def _atualizar_preview(self):
        if self.modo_preview == "lado_a_lado":
            self._salvar_scroll_preview()
        self.aba_conteudo.sincronizar_conteudo_pendente()
        self._sincronizar_modelo_com_ui()
        self.preview_display.findText("")
        gerador = GeradorHTMLPreview(self.documento)
        html_content = gerador.gerar_html()
        base_url = QtCore.QUrl.fromLocalFile(os.path.abspath(os.path.dirname(__file__)))
        self.preview_display.setHtml(html_content, baseUrl=base_url)
        if self.modo_preview == "aba":
            QMessageBox.information(self, "Atualizado", "A pré-visualização foi atualizada com sucesso.")

    def _marcar_modificado(self):
        if self._populando_ui:
            return
        if not self.modificado:
            self.modificado = True
            self.setWindowTitle(self.windowTitle() + '*')
        if self.config['recovery']['autosave_enabled']:
            if not self.autosave_timer.isActive():
                intervalo_min = self.config['recovery']['autosave_periodic_interval_min']
                print(f"Primeira modificação detectada. Iniciando auto-save periódico a cada {intervalo_min} minutos.")
                self.autosave_timer.start()
        self._disparar_atualizacao_automatica()

    def closeEvent(self, event):
        if self._verificar_alteracoes_nao_salvas():
            if self.caminho_projeto_atual or self.modificado:
                 gerenciador_recuperacao.limpar_recuperacao(self.caminho_projeto_atual)
            self.gerenciador_projeto.fechar_projeto()
            event.accept()
        else:
            event.ignore()

    @QtCore.Slot(bool)
    def _novo_projeto(self, primeira_execucao=False):
        if not primeira_execucao and not self._verificar_alteracoes_nao_salvas():
            return
        modelo_padrao = get_nomes_modelos()[0]
        self.iniciar_novo_projeto_com_modelo(modelo_padrao)

    @QtCore.Slot(str)
    def _on_template_selecionado(self, nome_modelo):
        if self._populando_ui or not nome_modelo or nome_modelo == self.documento.configuracoes.tipo_trabalho:
            return
        resposta = QMessageBox.question(self, "Mudar Modelo de Trabalho",
                                        f"Mudar o modelo para '{nome_modelo}' irá reorganizar sua estrutura de capítulos.\n"
                                        "Capítulos existentes serão preservados...\nDeseja continuar?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resposta == QMessageBox.StandardButton.No:
            self._populando_ui = True
            self.cfg_tipo.setCurrentText(self.documento.configuracoes.tipo_trabalho)
            self._populando_ui = False
            return
        mapa_capitulos_atuais = {c.titulo.upper().strip(): c for c in self.documento.estrutura_textual.filhos}
        titulos_novos = get_estrutura_por_nome(nome_modelo)
        nova_lista_de_capitulos = [mapa_capitulos_atuais.pop(t.upper().strip(), Capitulo(titulo=t, is_template_item=True)) for t in titulos_novos]
        capitulos_orfaos = [c for c in mapa_capitulos_atuais.values() if c.conteudo.strip() or c.filhos]
        if capitulos_orfaos:
            for c in capitulos_orfaos:
                c.is_template_item = False
            nova_lista_de_capitulos.extend(capitulos_orfaos)
            QMessageBox.information(self, "Capítulos Preservados", "Capítulos com conteúdo que não pertencem ao novo modelo foram movidos para o final.")
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
        if self.config['backup']['backup_on_save_enabled']:
            gerenciador_recuperacao.criar_backup(self.caminho_projeto_atual, self.config['backup']['max_backups_per_project'])
        self.aba_conteudo.sincronizar_conteudo_pendente()
        self._sincronizar_modelo_com_ui()
        try:
            self.gerenciador_projeto.salvar_projeto(self.documento, self.caminho_projeto_atual)
            self.modificado = False
            self.setWindowTitle(f'ABNT Helper Final - {os.path.basename(self.caminho_projeto_atual)}')
            QMessageBox.information(self, "Sucesso", "Projeto salvo com sucesso!")
            print("Trabalho salvo manualmente. Timer de recuperação pausado.")
            self.autosave_timer.stop()
            gerenciador_recuperacao.limpar_recuperacao(self.caminho_projeto_atual)
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
                self.carregar_projeto_pelo_caminho(caminho)

    def _popular_ui_com_documento(self):
        self._populando_ui = True
        cfg = self.documento.configuracoes
        self.cfg_tipo.setCurrentText(cfg.tipo_trabalho)
        self.cfg_instituicao.setText(cfg.instituicao)
        self.cfg_curso.setText(cfg.curso)
        self.cfg_modalidade_curso.setText(cfg.modalidade_curso)
        self.cfg_titulo_pretendido.setText(cfg.titulo_pretendido)
        self.cfg_cidade.setText(cfg.cidade)
        self.cfg_ano.setText(str(cfg.ano))
        self.titulo_input.setText(self.documento.titulo)
        self.autores_input.setPlainText('\n'.join([a.nome_completo for a in self.documento.autores]))
        self.orientador_input.setText(self.documento.orientador)
        self.resumo_input.setPlainText(self.documento.resumo)
        self.keywords_input.setText(self.documento.palavras_chave)
        self.aba_conteudo.documento = self.documento
        self.aba_conteudo._popular_arvore()
        self.aba_conteudo.atualizar_bancos_visuais()
        if self.aba_conteudo.arvore_capitulos.topLevelItemCount() > 0:
            self.aba_conteudo.arvore_capitulos.setCurrentItem(self.aba_conteudo.arvore_capitulos.topLevelItem(0))
        self.lista_referencias.clear()
        for ref in self.documento.referencias:
            self.lista_referencias.addItem(ref.formatar().replace('**', ''))
        self._populando_ui = False
        self._disparar_atualizacao_automatica()

    def _verificar_alteracoes_nao_salvas(self) -> bool:
        if not self.modificado:
            return True
        resposta = QMessageBox.question(self, "Salvar Alterações?",
                                        "Você tem alterações não salvas. Deseja salvá-las?",
                                        QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if resposta == QMessageBox.StandardButton.Cancel:
            return False
        if resposta == QMessageBox.StandardButton.Save:
            self._salvar_projeto()
        return True

    def _conectar_sinais_modificacao(self):
        self.cfg_tipo.currentTextChanged.connect(self._marcar_modificado)
        self.cfg_instituicao.textChanged.connect(self._marcar_modificado)
        self.cfg_curso.textChanged.connect(self._marcar_modificado)
        self.cfg_modalidade_curso.textChanged.connect(self._marcar_modificado)
        self.cfg_titulo_pretendido.textChanged.connect(self._marcar_modificado)
        self.cfg_cidade.textChanged.connect(self._marcar_modificado)
        self.cfg_ano.textChanged.connect(self._marcar_modificado)
        self.titulo_input.textChanged.connect(self._marcar_modificado)
        self.autores_input.textChanged.connect(self._marcar_modificado)
        self.orientador_input.textChanged.connect(self._marcar_modificado)
        self.resumo_input.textChanged.connect(self._marcar_modificado)
        self.keywords_input.textChanged.connect(self._marcar_modificado)
        self.aba_conteudo.editor_capitulo.textChanged.connect(self._marcar_modificado)
        self.aba_conteudo.arvore_capitulos.estruturaAlterada.connect(self._marcar_modificado)
        self.aba_conteudo.arvore_capitulos.itemChanged.connect(self._marcar_modificado)

    @QtCore.Slot()
    def _adicionar_referencia(self):
        dialog = ReferenciaDialog(parent=self)
        if dialog.exec():
            nova_ref = dialog.get_data()
            if nova_ref:
                self.documento.referencias.append(nova_ref)
                self.lista_referencias.addItem(nova_ref.formatar().replace('**', ''))
                self._marcar_modificado()

    @QtCore.Slot()
    def _editar_referencia(self):
        linha = self.lista_referencias.currentRow()
        if linha == -1:
            QMessageBox.warning(self, "Atenção", "Nenhuma referência selecionada para editar.")
            return
        ref_para_editar = self.documento.referencias[linha]
        dialog = ReferenciaDialog(ref=ref_para_editar, parent=self)
        if dialog.exec():
            ref_atualizada = dialog.get_data()
            if ref_atualizada:
                self.documento.referencias[linha] = ref_atualizada
                self.lista_referencias.item(linha).setText(ref_atualizada.formatar().replace('**', ''))
                self._marcar_modificado()

    @QtCore.Slot()
    def _remover_referencia(self):
        linha = self.lista_referencias.currentRow()
        if linha == -1: return
        if QMessageBox.question(self, "Confirmar", "Remover esta referência?") == QMessageBox.StandardButton.Yes:
            self.lista_referencias.takeItem(linha)
            del self.documento.referencias[linha]
            self._marcar_modificado()

    def _sincronizar_modelo_com_ui(self):
        cfg = self.documento.configuracoes
        cfg.tipo_trabalho = self.cfg_tipo.currentText()
        cfg.instituicao = self.cfg_instituicao.text()
        cfg.curso = self.cfg_curso.text()
        cfg.modalidade_curso = self.cfg_modalidade_curso.text()
        cfg.titulo_pretendido = self.cfg_titulo_pretendido.text()
        cfg.cidade = self.cfg_cidade.text()
        cfg.ano = int(self.cfg_ano.text() or datetime.now().year)
        self.documento.titulo = self.titulo_input.text()
        self.documento.autores = [Autor(n.strip()) for n in self.autores_input.toPlainText().splitlines() if n.strip()]
        self.documento.orientador = self.orientador_input.text()
        self.documento.resumo = self.resumo_input.toPlainText()
        self.documento.palavras_chave = self.keywords_input.text()

    def _gerar_documento_final(self):
        self.aba_conteudo.sincronizar_conteudo_pendente()
        self._sincronizar_modelo_com_ui()
        if not self.documento.titulo or not self.documento.autores:
            QMessageBox.warning(self, "Erro", "Título e Autores são campos obrigatórios.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Documento", "trabalho_abnt.docx", "Word Documents (*.docx)")
        if not filename: return
        try:
            gerador = GeradorDOCX(self.documento)
            gerador.gerar_documento(filename)
            QMessageBox.information(self, "Sucesso", f"Documento .docx gerado com sucesso em:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Geração", f"Ocorreu um erro: {e}")

    @QtCore.Slot()
    def _auto_salvar_recuperacao(self):
        if not self.modificado: return
        print(f"[{datetime.now():%H:%M:%S}] TIMER PERIÓDICO DISPARADO! Executando auto-save...")
        self.aba_conteudo.sincronizar_conteudo_pendente()
        self._sincronizar_modelo_com_ui()
        gerenciador_recuperacao.salvar_recuperacao(self.gerenciador_projeto, self.documento, self.caminho_projeto_atual)

    def carregar_projeto_pelo_caminho(self, caminho, is_recovery=False):
        if not is_recovery and not self._verificar_alteracoes_nao_salvas():
            self.close()
            return
        try:
            self.documento = self.gerenciador_projeto.carregar_projeto(caminho)
            self._popular_ui_com_documento()
            if is_recovery:
                self.caminho_projeto_atual = None
                self.modificado = True
                self.setWindowTitle(f'ABNT Helper Final - ARQUIVO RECUPERADO*')
                QMessageBox.information(self, "Arquivo Recuperado", "O arquivo foi recuperado com sucesso.\nUse 'Salvar Como...' para salvá-lo em um local permanente.")
                gerenciador_recuperacao.limpar_recuperacao_pelo_caminho_direto(caminho)
                self._marcar_modificado()
            else:
                self.caminho_projeto_atual = caminho
                self.modificado = False
                self.setWindowTitle(f'ABNT Helper Final - {os.path.basename(caminho)}')
                gerenciador_config.add_projeto_recente(caminho)
                gerenciador_recuperacao.limpar_recuperacao(caminho)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar", f"Não foi possível carregar o projeto:\n{e}")
            self.gerenciador_projeto.fechar_projeto()

    def iniciar_novo_projeto_com_modelo(self, nome_modelo):
        if not self._verificar_alteracoes_nao_salvas(): return
        gerenciador_recuperacao.limpar_recuperacao(self.caminho_projeto_atual)
        if self.autosave_timer.isActive(): self.autosave_timer.stop()
        self.documento = DocumentoABNT()
        estrutura = get_estrutura_por_nome(nome_modelo)
        for titulo in estrutura:
            self.documento.estrutura_textual.adicionar_filho(Capitulo(titulo=titulo, is_template_item=True))
        self.caminho_projeto_atual = None
        self.gerenciador_projeto.fechar_projeto()
        if hasattr(self, 'cfg_tipo'):
            self._popular_ui_com_documento()
            self._populando_ui = True
            self.cfg_tipo.setCurrentText(nome_modelo)
            self.documento.configuracoes.tipo_trabalho = nome_modelo
            self._populando_ui = False
        self.modificado = False
        self.setWindowTitle(f'ABNT Helper Final - Novo Projeto ({nome_modelo})')
        self._disparar_atualizacao_automatica()


if __name__ == '__main__':
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        print("ERRO: A dependência 'PySide6-WebEngineWidgets' não está instalada.")
        print("Por favor, execute: pip install PySide6-WebEngineWidgets")
        sys.exit(1)

    app = QApplication(sys.argv)
    
    # Loop principal para permitir voltar à tela inicial
    while True:
        gerenciador_recuperacao.setup_diretorios()
        
        acao_inicial = None
        dados_iniciais = None

        # Verificação automática de recuperação PRIMEIRO.
        arquivos_recuperaveis = gerenciador_recuperacao.verificar_arquivos_recuperaveis()
        if arquivos_recuperaveis:
            dialog = DialogoRecuperacao(arquivos_recuperaveis)
            if dialog.exec():
                if dialog.arquivos_para_recuperar:
                    acao_inicial = 'recuperar'
                    dados_iniciais = dialog.arquivos_para_recuperar
                
                for arq_info in dialog.arquivos_para_descartar:
                    gerenciador_recuperacao.limpar_recuperacao_pelo_caminho_direto(arq_info['recovery_file_path'])

        # Se nenhuma recuperação automática foi iniciada, mostra a tela inicial.
        if not acao_inicial:
            tela_inicial = TelaInicial()
            if tela_inicial.exec():
                acao_inicial, dados_iniciais = tela_inicial.get_resultado()

        # Se nenhuma ação foi escolhida (usuário fechou a tela inicial), sai do loop.
        if not acao_inicial:
            break

        # Bloco de processamento da ação
        if acao_inicial == 'recuperar':
            arquivos_para_recuperar = dados_iniciais
            primeiro_para_abrir = arquivos_para_recuperar.pop(0)
            caminho_primeiro = primeiro_para_abrir['recovery_file_path']
            
            outros_recuperados = []
            if arquivos_para_recuperar:
                desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
                for arq_info in arquivos_para_recuperar:
                    nome_original = arq_info.get('original_name', 'arquivo_recuperado').replace('.abnf', '')
                    caminho_seguro = os.path.join(desktop, f"[RECUPERADO] {nome_original}.abnf")
                    contador = 1
                    while os.path.exists(caminho_seguro):
                        caminho_seguro = os.path.join(desktop, f"[RECUPERADO] {nome_original}_{contador}.abnf")
                        contador += 1
                    try:
                        shutil.copy2(arq_info['recovery_file_path'], caminho_seguro)
                        outros_recuperados.append(os.path.basename(caminho_seguro))
                    except Exception as e:
                        print(f"Erro ao salvar arquivo recuperado na área de trabalho: {e}")
                    gerenciador_recuperacao.limpar_recuperacao_pelo_caminho_direto(arq_info['recovery_file_path'])
            
            acao_inicial = 'abrir_recuperado'
            dados_iniciais = caminho_primeiro
            
            if outros_recuperados:
                msg = (f"O projeto '{primeiro_para_abrir.get('original_name')}' foi aberto para edição.\n\n"
                       "Os seguintes projetos recuperados foram salvos na sua Área de Trabalho:\n- " +
                       "\n- ".join(outros_recuperados))
                QMessageBox.information(None, "Projetos Recuperados", msg)

        # Inicia a janela principal
        win = ABNTHelperApp()

        if acao_inicial == 'novo':
            win.iniciar_novo_projeto_com_modelo(dados_iniciais)
        elif acao_inicial == 'abrir':
            win.carregar_projeto_pelo_caminho(dados_iniciais)
        elif acao_inicial == 'abrir_recuperado':
            win.carregar_projeto_pelo_caminho(dados_iniciais, is_recovery=True)

        # Mostra a janela principal maximizada
        win.showMaximized()
        app.exec()

        # Verifica se o loop deve continuar (voltar à tela inicial) ou terminar
        if not win.wants_to_restart:
            break
            
    sys.exit(0)