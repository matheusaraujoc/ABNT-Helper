# DialogoFormula.py
import os
import tempfile
# NENHUMA IMPORTAÇÃO EXTERNA PARA CONVERSÃO!

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
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
        self._temp_svg_path = None

        layout = QVBoxLayout(self)
        
        form_layout = QtWidgets.QFormLayout()
        self.legenda_input = QLineEdit(self.formula.legenda)
        form_layout.addRow("Legenda (sem a palavra 'Equação X'):", self.legenda_input)
        layout.addLayout(form_layout)
        
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.web_view.page().profile().downloadRequested.connect(self._handle_automatic_download)
        
        path = os.path.join(os.path.dirname(__file__), "latex_renderer.html")
        self.web_view.setUrl(QtCore.QUrl.fromLocalFile(os.path.abspath(path)))
        self.web_view.loadFinished.connect(self._on_load_finished)
        layout.addWidget(self.web_view)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.trigger_save_process)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def trigger_save_process(self):
        if not self.legenda_input.text().strip():
            QMessageBox.warning(self, "Dados Incompletos", "A legenda da fórmula é obrigatória.")
            return

        def on_latex_code_received(latex_code):
            self.formula.codigo_latex = latex_code
            self.web_view.page().runJavaScript("window.prepareAndTriggerDownload();")
        
        self.web_view.page().runJavaScript("window.getEditorContent();", on_latex_code_received)

    @QtCore.Slot(QWebEngineDownloadRequest)
    def _handle_automatic_download(self, download_request: QWebEngineDownloadRequest):
        try:
            temp_dir = tempfile.gettempdir()
            pasta_formulas = os.path.join(temp_dir, "_abnthelper_formulas_svg_temp")
            os.makedirs(pasta_formulas, exist_ok=True)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".svg", dir=pasta_formulas)
            self._temp_svg_path = temp_file.name
            temp_file.close()

            download_request.setDownloadFileName(self._temp_svg_path)
            download_request.accept()
            download_request.stateChanged.connect(self._on_download_state_changed)
        except Exception as e:
            print(f"Erro ao preparar salvamento automático: {e}")
            download_request.cancel()

    def _converter_svg_para_png(self, svg_path: str) -> str | None:
        """Converte um arquivo SVG para PNG usando o renderizador nativo do PySide6."""
        try:
            pasta_saida = "_formulas_processadas"
            os.makedirs(pasta_saida, exist_ok=True)
            
            nome_base, _ = os.path.splitext(os.path.basename(svg_path))
            caminho_png = os.path.join(pasta_saida, f"{nome_base}.png")

            # Carrega o arquivo SVG usando o renderizador do Qt
            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                raise IOError("Arquivo SVG inválido ou não pôde ser lido.")

            # Cria uma imagem em branco (QImage) com o tamanho do SVG e fundo transparente
            image = QImage(renderer.defaultSize(), QImage.Format_ARGB32)
            image.fill(QtCore.Qt.GlobalColor.transparent) # Define o fundo como transparente

            # Cria um "pintor" para desenhar o SVG na imagem em branco
            painter = QPainter(image)
            renderer.render(painter)
            painter.end() # Finaliza a pintura

            # Salva a QImage resultante como um arquivo PNG
            if not image.save(caminho_png):
                raise IOError(f"Falha ao salvar o arquivo PNG em {caminho_png}")

            print(f"SVG '{svg_path}' convertido para PNG usando Qt em '{caminho_png}'")
            return caminho_png
            
        except Exception as e:
            print(f"Falha ao converter SVG para PNG com PySide6: {e}")
            QMessageBox.critical(self, "Erro de Conversão Nativa", f"Não foi possível converter a imagem da fórmula para PNG.\n\nDetalhes: {e}")
            return None

    @QtCore.Slot()
    def _on_download_state_changed(self, state: QWebEngineDownloadRequest.state):
        if state == QWebEngineDownloadRequest.DownloadCompleted:
            caminho_png_final = self._converter_svg_para_png(self._temp_svg_path)
            if caminho_png_final:
                self.formula.caminho_svg = self._temp_svg_path
                self.formula.caminho_processado_png = caminho_png_final
                super().accept()
        elif state == QWebEngineDownloadRequest.DownloadInterrupted:
            QMessageBox.warning(self, "Salvar Falhou", "O download do arquivo da fórmula foi interrompido.")

    def _on_load_finished(self, ok: bool):
        if not ok:
            QMessageBox.critical(self, "Erro", "Falha ao carregar o renderizador LaTeX.")
            return
            
        codigo_js_escapado = self.formula.codigo_latex.replace("\\", "\\\\").replace("\n", "\\n").replace("'", "\\'")
        js_code = f"window.setEditorContent('{codigo_js_escapado}');"
        self.web_view.page().runJavaScript(js_code)

    def get_dados_formula(self) -> Formula:
        self.formula.legenda = self.legenda_input.text()
        return self.formula