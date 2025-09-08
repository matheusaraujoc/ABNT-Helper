# dialogo_tabela.py
# Descrição: Janela de diálogo para a criação e edição detalhada de tabelas.

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QDialog, QWidget, QLabel, QLineEdit, 
                               QPushButton, QVBoxLayout, QHBoxLayout, 
                               QTableWidget, QTableWidgetItem, QDialogButtonBox)

from documento import Tabela

class TabelaDialog(QDialog):
    def __init__(self, tabela: Tabela = None, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Tabela ABNT")
        self.setMinimumSize(600, 400)

        # Se nenhuma tabela for passada, cria uma nova
        self.tabela = tabela if tabela else Tabela(dados=[["Cabeçalho 1", "Cabeçalho 2"], ["Dado 1", "Dado 2"]])

        self.layout = QVBoxLayout(self)

        # Campos de Título e Fonte
        self.titulo_input = QLineEdit(self.tabela.titulo)
        self.fonte_input = QLineEdit(self.tabela.fonte)
        
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Título (sem a palavra 'Tabela X'):", self.titulo_input)
        form_layout.addRow("Fonte:", self.fonte_input)
        self.layout.addLayout(form_layout)

        # Grade da Tabela
        self.table_widget = QTableWidget()
        self.popular_tabela_widget()
        self.layout.addWidget(self.table_widget)

        # Botões de controle da grade
        btn_layout = QHBoxLayout()
        btn_add_linha = QPushButton("Adicionar Linha")
        btn_del_linha = QPushButton("Remover Linha")
        btn_add_col = QPushButton("Adicionar Coluna")
        btn_del_col = QPushButton("Remover Coluna")
        btn_layout.addWidget(btn_add_linha)
        btn_layout.addWidget(btn_del_linha)
        btn_layout.addWidget(btn_add_col)
        btn_layout.addWidget(btn_del_col)
        btn_add_linha.clicked.connect(self.adicionar_linha)
        btn_del_linha.clicked.connect(self.remover_linha)
        btn_add_col.clicked.connect(self.adicionar_coluna)
        btn_del_col.clicked.connect(self.remover_coluna)
        self.layout.addLayout(btn_layout)

        # Botões OK / Cancelar
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def popular_tabela_widget(self):
        dados = self.tabela.dados
        if not dados:
            return
        
        num_rows = len(dados)
        num_cols = len(dados[0])
        self.table_widget.setRowCount(num_rows)
        self.table_widget.setColumnCount(num_cols)
        
        for i, row_data in enumerate(dados):
            for j, cell_data in enumerate(row_data):
                self.table_widget.setItem(i, j, QTableWidgetItem(cell_data))

    def adicionar_linha(self):
        self.table_widget.insertRow(self.table_widget.rowCount())

    def remover_linha(self):
        row = self.table_widget.currentRow()
        if row != -1:
            self.table_widget.removeRow(row)

    def adicionar_coluna(self):
        self.table_widget.insertColumn(self.table_widget.columnCount())

    def remover_coluna(self):
        col = self.table_widget.currentColumn()
        if col != -1:
            self.table_widget.removeColumn(col)
            
    def get_dados_tabela(self) -> Tabela:
        """Coleta os dados da UI e retorna um objeto Tabela atualizado."""
        self.tabela.titulo = self.titulo_input.text()
        self.tabela.fonte = self.fonte_input.text()
        
        num_rows = self.table_widget.rowCount()
        num_cols = self.table_widget.columnCount()
        novos_dados = []
        for i in range(num_rows):
            row_data = []
            for j in range(num_cols):
                item = self.table_widget.item(i, j)
                row_data.append(item.text() if item else "")
            novos_dados.append(row_data)
        
        self.tabela.dados = novos_dados
        return self.tabela