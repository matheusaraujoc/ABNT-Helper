# DialogoFormula.py
# VERSÃO FINAL COM AUTOMAÇÃO VIA INTERCEPTAÇÃO DE DOWNLOAD

import os
import tempfile
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QDialog, QWidget, QLabel, QLineEdit,
                               QVBoxLayout, QDialogButtonBox, QMessageBox)
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineDownloadRequest
from PySide6.QtWebEngineWidgets import QWebEngineView

from formula import Formula

class DialogoFormula(QDialog):
    def __init__(self, formula: Formula = None, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Fórmulas LaTeX")
        self.setMinimumSize(800, 600)

        self.formula = formula if formula else Formula()
        self.svg_gerado_path = None

        layout = QVBoxLayout(self)
        
        form_layout = QtWidgets.QFormLayout()
        self.legenda_input = QLineEdit(self.formula.legenda)
        form_layout.addRow("Legenda (sem a palavra 'Equação X'):", self.legenda_input)
        layout.addLayout(form_layout)
        
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        
        # O "ouvinte" de downloads, que é a parte confiável do sistema
        self.web_view.page().profile().downloadRequested.connect(self._handle_automatic_download)
        
        path = os.path.join(os.path.dirname(__file__), "latex_renderer.html")
        self.web_view.setUrl(QtCore.QUrl.fromLocalFile(os.path.abspath(path)))
        self.web_view.loadFinished.connect(self._on_load_finished)
        layout.addWidget(self.web_view)

        # Botões padrão "OK" e "Cancelar"
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.trigger_save_process)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def trigger_save_process(self):
        """
        Chamado pelo botão 'OK'. Apenas valida os campos e pede
        ao JavaScript para iniciar o download. Não espera por um retorno.
        """
        if not self.legenda_input.text().strip():
            QMessageBox.warning(self, "Dados Incompletos", "A legenda da fórmula é obrigatória.")
            return

        # Atualiza o código LaTeX no objeto antes de salvar
        def on_latex_code_received(latex_code):
            self.formula.codigo_latex = latex_code
            # Agora que temos o código, podemos pedir ao JS para preparar e baixar o SVG
            self.web_view.page().runJavaScript("window.prepareAndTriggerDownload();")
        
        self.web_view.page().runJavaScript("window.getEditorContent();", on_latex_code_received)

    @QtCore.Slot(QWebEngineDownloadRequest)
    def _handle_automatic_download(self, download_request: QWebEngineDownloadRequest):
        """
        Intercepta o download iniciado pelo JS. Salva o arquivo
        automaticamente em um local temporário.
        """
        try:
            temp_dir = tempfile.gettempdir()
            pasta_formulas = os.path.join(temp_dir, "_abnthelper_formulas_temp")
            os.makedirs(pasta_formulas, exist_ok=True)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".svg", dir=pasta_formulas)
            self.svg_gerado_path = temp_file.name
            temp_file.close() # Fecha o arquivo para que o WebEngine possa escrever nele

            download_request.setDownloadFileName(self.svg_gerado_path)
            download_request.accept()
            download_request.stateChanged.connect(self._on_download_state_changed)
        except Exception as e:
            print(f"Erro ao preparar salvamento automático: {e}")
            download_request.cancel()

    @QtCore.Slot()
    def _on_download_state_changed(self, state: QWebEngineDownloadRequest.state):
        if state == QWebEngineDownloadRequest.DownloadCompleted:
            # O arquivo foi salvo, agora podemos fechar o diálogo com sucesso.
            super().accept() # Usa o accept() da classe pai (QDialog)
        elif state == QWebEngineDownloadRequest.DownloadInterrupted:
            QMessageBox.warning(self, "Salvar Falhou", "O arquivo da fórmula não pôde ser salvo.")

    def _on_load_finished(self, ok: bool):
        if not ok:
            QMessageBox.critical(self, "Erro", "Falha ao carregar o renderizador LaTeX.")
            return
            
        codigo_js_escapado = self.formula.codigo_latex.replace("\\", "\\\\").replace("\n", "\\n").replace("'", "\\'")
        js_code = f"window.setEditorContent('{codigo_js_escapado}');"
        self.web_view.page().runJavaScript(js_code)

    def get_dados_formula(self) -> Formula:
        # O código LaTeX já foi atualizado no trigger_save_process
        self.formula.legenda = self.legenda_input.text()
        if self.svg_gerado_path:
            self.formula.caminho_imagem = self.svg_gerado_path
        return self.formula