# main_app.py
# Descrição: Aplicação principal, agora atuando como um "montador" da interface.

import sys
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
                               QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, 
                               QMessageBox, QTabWidget, QComboBox, 
                               QDialog, QFormLayout, QDialogButtonBox)

from documento import DocumentoABNT, Autor
from gerador_docx import GeradorDOCX
from referencia import Livro, Artigo, Site
from aba_conteudo import AbaConteudo  # <-- Importa nosso novo componente

# A classe ReferenciaDialog continua a mesma e pode ficar aqui ou ser movida
# para seu próprio arquivo (ex: dialogs.py) no futuro.
class ReferenciaDialog(QDialog):
    # (código sem alterações)
    def __init__(self, ref=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Referência")
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Livro", "Artigo", "Site"])
        
        self.autores_input = QLineEdit()
        self.autores_input.setPlaceholderText("Autor 1; Autor 2")
        self.titulo_input = QLineEdit()
        self.ano_input = QLineEdit()

        self.campos_livro = { "Local": QLineEdit(), "Editora": QLineEdit() }
        self.campos_artigo = { "Revista": QLineEdit(), "Volume": QLineEdit(), "Pág. Inicial": QLineEdit(), "Pág. Final": QLineEdit() }
        self.campos_site = { "URL": QLineEdit(), "Data de Acesso": QLineEdit("dd/mm/aaaa") }
        
        self.layout.addWidget(QLabel("Tipo de Referência:"))
        self.layout.addWidget(self.tipo_combo)
        self.layout.addLayout(self.form_layout)
        
        self.form_layout.addRow("Autores:", self.autores_input)
        self.form_layout.addRow("Título:", self.titulo_input)
        self.form_layout.addRow("Ano:", self.ano_input)

        for label, widget in self.campos_livro.items(): self.form_layout.addRow(label, widget)
        for label, widget in self.campos_artigo.items(): self.form_layout.addRow(label, widget)
        for label, widget in self.campos_site.items(): self.form_layout.addRow(label, widget)
            
        self.tipo_combo.currentTextChanged.connect(self.update_form_visibility)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        self.update_form_visibility(self.tipo_combo.currentText())

    def update_form_visibility(self, tipo):
        all_specific_fields = {**self.campos_livro, **self.campos_artigo, **self.campos_site}
        for widget in all_specific_fields.values():
            label = self.form_layout.labelForField(widget)
            if label: label.setVisible(False)
            widget.setVisible(False)

        fields_to_show = {}
        if tipo == "Livro": fields_to_show = self.campos_livro
        elif tipo == "Artigo": fields_to_show = self.campos_artigo
        elif tipo == "Site": fields_to_show = self.campos_site
            
        for widget in fields_to_show.values():
            label = self.form_layout.labelForField(widget)
            if label: label.setVisible(True)
            widget.setVisible(True)

    def get_data(self):
        tipo = self.tipo_combo.currentText()
        try: ano_val = int(self.ano_input.text()) if self.ano_input.text().isdigit() else 0
        except ValueError: ano_val = 0
        common_data = { "autores": self.autores_input.text(), "titulo": self.titulo_input.text(), "ano": ano_val }
        if tipo == "Livro":
            specific_data = {k.lower(): w.text() for k, w in self.campos_livro.items()}
            return Livro(**common_data, **specific_data)
        elif tipo == "Artigo":
            try: pg_ini, pg_fim = int(self.campos_artigo["Pág. Inicial"].text() or 0), int(self.campos_artigo["Pág. Final"].text() or 0)
            except ValueError: pg_ini, pg_fim = 0, 0
            specific_data = { "revista": self.campos_artigo["Revista"].text(), "volume": self.campos_artigo["Volume"].text(), "pagina_inicial": pg_ini, "pagina_final": pg_fim }
            return Artigo(**common_data, **specific_data)
        elif tipo == "Site":
            specific_data = {k.lower().replace(' de ', '_'): w.text() for k, w in self.campos_site.items()}
            return Site(**common_data, **specific_data)
        return None

class ABNTHelperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ABNT Helper - Editor de Estrutura')
        self.setGeometry(100, 100, 950, 750)
        self.documento = DocumentoABNT()
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- ## ALTERADO: A aba de conteúdo agora é um componente externo ## ---
        self.aba_conteudo = AbaConteudo(self.documento) # Cria a instância do componente
        
        self.tabs.addTab(self._criar_aba_geral(), "Geral e Pré-Textual")
        self.tabs.addTab(self.aba_conteudo, "Conteúdo Textual (Estrutura)") # Adiciona o componente
        self.tabs.addTab(self._criar_aba_referencias(), "Referências")
        
        self.generate_btn = QPushButton("Gerar Documento .docx")
        self.generate_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.generate_btn.clicked.connect(self._gerar_documento)
        main_layout.addWidget(self.generate_btn)

    def _criar_aba_geral(self):
        # (código sem alterações)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<h3>Configurações do Documento</h3>"))
        form_layout1 = QFormLayout()
        self.cfg_tipo = QComboBox()
        self.cfg_tipo.addItems(["Trabalho de Conclusão de Curso (TCC)", "Artigo Científico", "Dissertação de Mestrado", "Tese de Doutorado"])
        form_layout1.addRow("Tipo de Trabalho:", self.cfg_tipo)
        self.cfg_instituicao = QLineEdit(self.documento.configuracoes.instituicao)
        self.cfg_curso = QLineEdit(self.documento.configuracoes.curso)
        self.cfg_cidade = QLineEdit(self.documento.configuracoes.cidade)
        self.cfg_ano = QLineEdit(str(self.documento.configuracoes.ano))
        form_layout1.addRow("Instituição:", self.cfg_instituicao)
        form_layout1.addRow("Curso:", self.cfg_curso)
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
        # (código sem alterações)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("<h3>Gerenciador de Referências</h3>"))
        self.lista_referencias = QtWidgets.QListWidget()
        layout.addWidget(self.lista_referencias)
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Adicionar Referência")
        btn_add.clicked.connect(self._adicionar_referencia)
        btn_del = QPushButton("Remover Selecionada")
        btn_del.clicked.connect(self._remover_referencia)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        layout.addLayout(btn_layout)
        return widget

    @QtCore.Slot()
    def _adicionar_referencia(self):
        # (código sem alterações)
        dialog = ReferenciaDialog(self)
        if dialog.exec():
            nova_ref = dialog.get_data()
            if nova_ref:
                self.documento.referencias.append(nova_ref)
                self.lista_referencias.addItem(nova_ref.formatar().replace('**', ''))

    @QtCore.Slot()
    def _remover_referencia(self):
        # (código sem alterações)
        linha = self.lista_referencias.currentRow()
        if linha == -1: return
        if QMessageBox.question(self, "Confirmar", "Remover esta referência?") == QMessageBox.Yes:
            self.lista_referencias.takeItem(linha)
            del self.documento.referencias[linha]

    def _sincronizar_modelo_com_ui(self):
        # (código sem alterações)
        cfg = self.documento.configuracoes
        cfg.tipo_trabalho = self.cfg_tipo.currentText()
        cfg.instituicao = self.cfg_instituicao.text()
        cfg.curso = self.cfg_curso.text()
        cfg.cidade = self.cfg_cidade.text()
        cfg.ano = int(self.cfg_ano.text())
        self.documento.titulo = self.titulo_input.text()
        self.documento.autores = [Autor(n.strip()) for n in self.autores_input.toPlainText().splitlines() if n.strip()]
        self.documento.orientador = self.orientador_input.text()
        self.documento.resumo = self.resumo_input.toPlainText()
        self.documento.palavras_chave = self.keywords_input.text()

    @QtCore.Slot()
    def _gerar_documento(self):
        # --- ## ALTERADO: Garante que o último texto editado seja salvo ## ---
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
            QMessageBox.information(self, "Sucesso", f"Documento gerado com sucesso em:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Geração", f"Ocorreu um erro: {e}\n\nVerifique se os campos numéricos (como Ano) estão preenchidos corretamente.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ABNTHelperApp()
    win.show()
    sys.exit(app.exec())