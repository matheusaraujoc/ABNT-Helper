# aba_conteudo.py
# Descrição: Componente de UI com a correção do bug de manipulação da árvore.

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QWidget, QLabel, QTextEdit, QPushButton, 
                               QVBoxLayout, QHBoxLayout, QMessageBox, 
                               QTreeWidget, QTreeWidgetItem, QInputDialog)

from documento import Capitulo

class AbaConteudo(QWidget):
    """
    Este widget encapsula toda a funcionalidade da aba de conteúdo,
    incluindo a árvore de tópicos, os botões e o editor de texto.
    """
    def __init__(self, documento, parent=None):
        super().__init__(parent)
        
        self.documento = documento
        self._carregando_capitulo = False

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)

        # Painel Esquerdo: Árvore de Tópicos e Botões
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(350)

        left_layout.addWidget(QLabel("Estrutura do Documento (dê um duplo clique para editar)"))
        self.arvore_capitulos = QTreeWidget()
        self.arvore_capitulos.setHeaderLabel("Tópicos")
        self.arvore_capitulos.currentItemChanged.connect(self._carregar_capitulo_no_editor)
        self.arvore_capitulos.itemChanged.connect(self._renomear_capitulo)
        self._popular_arvore()
        left_layout.addWidget(self.arvore_capitulos)

        btn_layout = QHBoxLayout()
        btn_add_topico = QPushButton("Novo Tópico")
        btn_add_sub = QPushButton("Novo Subtópico")
        btn_del = QPushButton("Remover")
        btn_layout.addWidget(btn_add_topico)
        btn_layout.addWidget(btn_add_sub)
        btn_layout.addWidget(btn_del)
        btn_add_topico.clicked.connect(self._adicionar_topico_principal)
        btn_add_sub.clicked.connect(self._adicionar_subtopico)
        btn_del.clicked.connect(self._remover_topico)
        left_layout.addLayout(btn_layout)

        # Painel Direito: Editor de Texto
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.label_capitulo_atual = QLabel("Selecione um tópico para editar")
        self.editor_capitulo = QTextEdit()
        self.editor_capitulo.textChanged.connect(self._salvar_conteudo_capitulo)
        right_layout.addWidget(self.label_capitulo_atual)
        right_layout.addWidget(self.editor_capitulo)

        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        if self.arvore_capitulos.topLevelItemCount() > 0:
            self.arvore_capitulos.setCurrentItem(self.arvore_capitulos.topLevelItem(0))
            
    def _popular_arvore(self):
        self.arvore_capitulos.blockSignals(True)
        self.arvore_capitulos.clear()
        
        def adicionar_filhos_recursivo(no_pai_modelo, no_pai_widget):
            for filho_modelo in no_pai_modelo.filhos:
                item_widget = QTreeWidgetItem([filho_modelo.titulo])
                item_widget.setData(0, QtCore.Qt.ItemDataRole.UserRole, filho_modelo)
                item_widget.setFlags(item_widget.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                
                if no_pai_widget is self.arvore_capitulos:
                    no_pai_widget.addTopLevelItem(item_widget)
                else:
                    no_pai_widget.addChild(item_widget)
                
                adicionar_filhos_recursivo(filho_modelo, item_widget)
        
        adicionar_filhos_recursivo(self.documento.estrutura_textual, self.arvore_capitulos)
        self.arvore_capitulos.expandAll()
        self.arvore_capitulos.blockSignals(False)

    # --- ## ALTERADO: Lógica de adição incremental ## ---
    @QtCore.Slot()
    def _adicionar_topico_principal(self):
        novo_capitulo = Capitulo(titulo="Novo Tópico")
        self.documento.estrutura_textual.adicionar_filho(novo_capitulo)
        
        # Adiciona o item diretamente na UI sem reconstruir tudo
        item_widget = QTreeWidgetItem([novo_capitulo.titulo])
        item_widget.setData(0, QtCore.Qt.ItemDataRole.UserRole, novo_capitulo)
        item_widget.setFlags(item_widget.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        self.arvore_capitulos.addTopLevelItem(item_widget)
        self.arvore_capitulos.setCurrentItem(item_widget)

    # --- ## ALTERADO: Lógica de adição incremental ## ---
    @QtCore.Slot()
    def _adicionar_subtopico(self):
        item_pai_widget = self.arvore_capitulos.currentItem()
        if not item_pai_widget:
            QMessageBox.warning(self, "Atenção", "Selecione um tópico para adicionar um subtópico.")
            return
            
        no_pai_modelo = item_pai_widget.data(0, QtCore.Qt.ItemDataRole.UserRole)
        novo_subtopico = Capitulo(titulo="Novo Subtópico")
        no_pai_modelo.adicionar_filho(novo_subtopico)

        # Adiciona o item diretamente na UI sem reconstruir tudo
        item_filho_widget = QTreeWidgetItem([novo_subtopico.titulo])
        item_filho_widget.setData(0, QtCore.Qt.ItemDataRole.UserRole, novo_subtopico)
        item_filho_widget.setFlags(item_filho_widget.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        item_pai_widget.addChild(item_filho_widget)
        
        # Expande o pai para mostrar o novo filho
        self.arvore_capitulos.expandItem(item_pai_widget)
        self.arvore_capitulos.setCurrentItem(item_filho_widget)

    @QtCore.Slot(QTreeWidgetItem, int)
    def _renomear_capitulo(self, item, column):
        no_modelo = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if no_modelo and no_modelo.titulo != item.text(column):
            no_modelo.titulo = item.text(column)
            if self.arvore_capitulos.currentItem() is item:
                self.label_capitulo_atual.setText(f"Editando: {no_modelo.titulo}")

    # --- ## ALTERADO: Lógica de remoção incremental ## ---
    @QtCore.Slot()
    def _remover_topico(self):
        item_selecionado = self.arvore_capitulos.currentItem()
        if not item_selecionado: return

        resposta = QMessageBox.question(self, "Confirmar", "Remover este tópico e todos os seus subtópicos?")
        if resposta == QMessageBox.StandardButton.Yes:
            no_modelo = item_selecionado.data(0, QtCore.Qt.ItemDataRole.UserRole)
            no_pai_modelo = no_modelo.pai
            
            # Remove do modelo de dados
            if no_pai_modelo:
                no_pai_modelo.filhos.remove(no_modelo)
            
            # Remove da UI sem reconstruir tudo
            item_pai_widget = item_selecionado.parent()
            if item_pai_widget:
                item_pai_widget.removeChild(item_selecionado)
            else:
                index = self.arvore_capitulos.indexOfTopLevelItem(item_selecionado)
                self.arvore_capitulos.takeTopLevelItem(index)

    @QtCore.Slot(QTreeWidgetItem)
    def _carregar_capitulo_no_editor(self, item_atual, item_anterior):
        if not item_atual:
            self.editor_capitulo.clear()
            self.editor_capitulo.setEnabled(False)
            self.label_capitulo_atual.setText("Selecione um tópico")
            return
        
        self._carregando_capitulo = True
        no_modelo = item_atual.data(0, QtCore.Qt.ItemDataRole.UserRole)
        self.label_capitulo_atual.setText(f"Editando: {no_modelo.titulo}")
        self.editor_capitulo.setPlainText(no_modelo.conteudo)
        self.editor_capitulo.setEnabled(True)
        self._carregando_capitulo = False

    @QtCore.Slot()
    def _salvar_conteudo_capitulo(self):
        if self._carregando_capitulo: return
        
        item_atual = self.arvore_capitulos.currentItem()
        if item_atual:
            no_modelo = item_atual.data(0, QtCore.Qt.ItemDataRole.UserRole)
            no_modelo.conteudo = self.editor_capitulo.toPlainText()
    
    def sincronizar_conteudo_pendente(self):
        """Método público para garantir que o último texto editado seja salvo no modelo."""
        self._salvar_conteudo_capitulo()