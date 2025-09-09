# dialogs.py
# Descrição: Contém todas as classes de janelas de diálogo utilizadas pela aplicação.

import os
import shutil
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QDialog, QWidget, QLabel, QLineEdit, QComboBox,
                               QFormLayout, QVBoxLayout, QDialogButtonBox, QListWidget,
                               QListWidgetItem, QTableWidget, QTableWidgetItem, QMessageBox,
                               QPushButton, QHBoxLayout, QFileDialog, QDoubleSpinBox)

from referencia import Livro, Artigo, Site
from documento import Tabela, Figura

class DialogoFigura(QDialog):
    """
    Janela de diálogo para criar e editar um objeto Figura.
    """
    def __init__(self, figura: Figura = None, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Figura")
        self.setMinimumWidth(500)

        self.figura = figura if figura else Figura()

        # Guarda os caminhos para o processamento
        self.caminho_original_selecionado = self.figura.caminho_original
        self.caminho_processado_final = self.figura.caminho_processado

        # UI Setup
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.titulo_input = QLineEdit(self.figura.titulo)
        self.fonte_input = QLineEdit(self.figura.fonte)
        self.largura_input = QDoubleSpinBox()
        self.largura_input.setRange(1.0, 20.0)
        self.largura_input.setSuffix(" cm")
        self.largura_input.setValue(self.figura.largura_cm)
        
        self.caminho_label = QLabel(self.caminho_original_selecionado or "Nenhum arquivo selecionado.")
        self.caminho_label.setWordWrap(True)
        btn_selecionar_arquivo = QPushButton("Selecionar Imagem...")
        btn_selecionar_arquivo.clicked.connect(self._selecionar_arquivo)

        form_layout.addRow("Título (sem a palavra 'Figura X'):", self.titulo_input)
        form_layout.addRow("Fonte:", self.fonte_input)
        form_layout.addRow("Largura da Imagem:", self.largura_input)
        form_layout.addRow("Arquivo de Imagem:", btn_selecionar_arquivo)
        form_layout.addRow("", self.caminho_label)
        
        self.layout.addLayout(form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def _selecionar_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if caminho:
            self.caminho_original_selecionado = caminho
            self.caminho_label.setText(caminho)

    def accept(self):
        # Validação antes de fechar
        if not self.titulo_input.text().strip():
            QMessageBox.warning(self, "Dados Incompletos", "O título da figura é obrigatório.")
            return

        if not self.caminho_original_selecionado:
            QMessageBox.warning(self, "Dados Incompletos", "É necessário selecionar um arquivo de imagem.")
            return
            
        # Processa a imagem (copia para uma pasta local do projeto para portabilidade)
        try:
            imagens_dir = os.path.join(os.getcwd(), "imagens_processadas")
            os.makedirs(imagens_dir, exist_ok=True)
            
            nome_arquivo = os.path.basename(self.caminho_original_selecionado)
            # Evita sobreposição de nomes de arquivos
            nome_base, extensao = os.path.splitext(nome_arquivo)
            caminho_destino = os.path.join(imagens_dir, nome_arquivo)
            
            contador = 1
            while os.path.exists(caminho_destino):
                caminho_destino = os.path.join(imagens_dir, f"{nome_base}_{contador}{extensao}")
                contador += 1

            shutil.copy2(self.caminho_original_selecionado, caminho_destino)
            self.caminho_processado_final = caminho_destino
            
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Processar Imagem", f"Não foi possível copiar a imagem:\n{e}")
            return

        super().accept()

    def get_dados_figura(self) -> Figura:
        self.figura.titulo = self.titulo_input.text().strip()
        self.figura.fonte = self.fonte_input.text().strip()
        self.figura.largura_cm = self.largura_input.value()
        self.figura.caminho_original = self.caminho_original_selecionado
        self.figura.caminho_processado = self.caminho_processado_final
        return self.figura

class TabelaDialog(QDialog):
    def __init__(self, tabela: Tabela = None, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Tabela ABNT")
        # ... (Restante da classe TabelaDialog inalterada)
        self.setMinimumSize(600, 400)
        self.tabela = tabela if tabela else Tabela(dados=[["Cabeçalho 1", "Cabeçalho 2"], ["Dado 1", "Dado 2"]])
        self.layout = QVBoxLayout(self)
        self.titulo_input = QLineEdit(self.tabela.titulo)
        self.fonte_input = QLineEdit(self.tabela.fonte)
        self.estilo_borda_combo = QComboBox()
        self.estilo_borda_combo.addItems(["ABNT (Padrão)", "Grade Completa"])
        if self.tabela.estilo_borda == 'grade':
            self.estilo_borda_combo.setCurrentIndex(1)
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Título (sem a palavra 'Tabela X'):", self.titulo_input)
        form_layout.addRow("Fonte:", self.fonte_input)
        form_layout.addRow("Estilo da Borda:", self.estilo_borda_combo)
        self.layout.addLayout(form_layout)
        self.table_widget = QTableWidget()
        self.popular_tabela_widget()
        self.layout.addWidget(self.table_widget)
        btn_layout = QHBoxLayout()
        btn_add_linha = QPushButton("Adicionar Linha"); btn_del_linha = QPushButton("Remover Linha")
        btn_add_col = QPushButton("Adicionar Coluna"); btn_del_col = QPushButton("Remover Coluna")
        btn_layout.addWidget(btn_add_linha); btn_layout.addWidget(btn_del_linha)
        btn_layout.addWidget(btn_add_col); btn_layout.addWidget(btn_del_col)
        btn_add_linha.clicked.connect(self.adicionar_linha); btn_del_linha.clicked.connect(self.remover_linha)
        btn_add_col.clicked.connect(self.adicionar_coluna); btn_del_col.clicked.connect(self.remover_coluna)
        self.layout.addLayout(btn_layout)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def accept(self):
        if not self.titulo_input.text().strip():
            QMessageBox.warning(self, "Título Obrigatório", "O título da tabela não pode estar vazio.")
            return
        super().accept()

    def popular_tabela_widget(self):
        dados = self.tabela.dados
        if not dados: return
        num_rows = len(dados); num_cols = len(dados[0])
        self.table_widget.setRowCount(num_rows); self.table_widget.setColumnCount(num_cols)
        for i, row_data in enumerate(dados):
            for j, cell_data in enumerate(row_data):
                self.table_widget.setItem(i, j, QTableWidgetItem(cell_data))

    def adicionar_linha(self): self.table_widget.insertRow(self.table_widget.rowCount())
    def remover_linha(self):
        row = self.table_widget.currentRow()
        if row != -1: self.table_widget.removeRow(row)
    def adicionar_coluna(self): self.table_widget.insertColumn(self.table_widget.columnCount())
    def remover_coluna(self):
        col = self.table_widget.currentColumn()
        if col != -1: self.table_widget.removeColumn(col)
    def get_dados_tabela(self) -> Tabela:
        self.tabela.titulo = self.titulo_input.text()
        self.tabela.fonte = self.fonte_input.text()
        self.tabela.estilo_borda = 'abnt' if self.estilo_borda_combo.currentIndex() == 0 else 'grade'
        num_rows = self.table_widget.rowCount(); num_cols = self.table_widget.columnCount()
        novos_dados = []
        for i in range(num_rows):
            row_data = []
            for j in range(num_cols):
                item = self.table_widget.item(i, j)
                row_data.append(item.text() if item else "")
            novos_dados.append(row_data)
        self.tabela.dados = novos_dados
        return self.tabela

class ReferenciaDialog(QDialog):
    def __init__(self, ref=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Referência")
        # ... (Restante da classe ReferenciaDialog inalterada) ...
        self.layout = QVBoxLayout(self); self.form_layout = QFormLayout()
        self.tipo_combo = QComboBox(); self.tipo_combo.addItems(["Livro", "Artigo", "Site"])
        self.autores_input = QLineEdit(); self.autores_input.setPlaceholderText("Autor 1; Autor 2")
        self.titulo_input = QLineEdit(); self.ano_input = QLineEdit()
        self.campos_livro = { "Local": QLineEdit(), "Editora": QLineEdit() }
        self.campos_artigo = { "Revista": QLineEdit(), "Volume": QLineEdit(), "Pág. Inicial": QLineEdit(), "Pág. Final": QLineEdit() }
        self.campos_site = { "URL": QLineEdit(), "Data de Acesso": QLineEdit("dd/mm/aaaa") }
        self.layout.addWidget(QLabel("Tipo de Referência:")); self.layout.addWidget(self.tipo_combo)
        self.layout.addLayout(self.form_layout); self.form_layout.addRow("Autores:", self.autores_input)
        self.form_layout.addRow("Título:", self.titulo_input); self.form_layout.addRow("Ano:", self.ano_input)
        for label, widget in self.campos_livro.items(): self.form_layout.addRow(label, widget)
        for label, widget in self.campos_artigo.items(): self.form_layout.addRow(label, widget)
        for label, widget in self.campos_site.items(): self.form_layout.addRow(label, widget)
        self.tipo_combo.currentTextChanged.connect(self.update_form_visibility)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept); self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        if ref: self._popular_campos(ref)
        else: self.update_form_visibility(self.tipo_combo.currentText())

    def _popular_campos(self, ref):
        self.tipo_combo.setCurrentText(ref.tipo); self.autores_input.setText(ref.autores)
        self.titulo_input.setText(ref.titulo); self.ano_input.setText(str(ref.ano))
        if isinstance(ref, Livro): self.campos_livro["Local"].setText(ref.local); self.campos_livro["Editora"].setText(ref.editora)
        elif isinstance(ref, Artigo):
            self.campos_artigo["Revista"].setText(ref.revista); self.campos_artigo["Volume"].setText(ref.volume)
            self.campos_artigo["Pág. Inicial"].setText(str(ref.pagina_inicial)); self.campos_artigo["Pág. Final"].setText(str(ref.pagina_final))
        elif isinstance(ref, Site): self.campos_site["URL"].setText(ref.url); self.campos_site["Data de Acesso"].setText(ref.data_acesso)
        self.update_form_visibility(ref.tipo)

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
            specific_data = { "local": self.campos_livro["Local"].text(), "editora": self.campos_livro["Editora"].text()}; return Livro(**common_data, **specific_data)
        elif tipo == "Artigo":
            try: pg_ini, pg_fim = int(self.campos_artigo["Pág. Inicial"].text() or 0), int(self.campos_artigo["Pág. Final"].text() or 0)
            except ValueError: pg_ini, pg_fim = 0, 0
            specific_data = { "revista": self.campos_artigo["Revista"].text(), "volume": self.campos_artigo["Volume"].text(), "pagina_inicial": pg_ini, "pagina_final": pg_fim }; return Artigo(**common_data, **specific_data)
        elif tipo == "Site":
            specific_data = { "url": self.campos_site["URL"].text(), "data_acesso": self.campos_site["Data de Acesso"].text()}; return Site(**common_data, **specific_data)
        return None