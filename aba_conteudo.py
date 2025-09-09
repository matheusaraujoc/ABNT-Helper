# aba_conteudo.py
# Descrição: Versão com a busca aprimorada para filtrar por títulos e conteúdo dos capítulos.

import re
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import (QWidget, QLabel, QTextEdit, QPushButton, QListWidget, QCheckBox,
                               QVBoxLayout, QHBoxLayout, QMessageBox, QTreeWidget,
                               QTreeWidgetItem, QInputDialog, QAbstractItemView, QLineEdit)

from documento import Capitulo, Tabela, Figura
from dialogs import TabelaDialog, DialogoFigura

class ArvoreConteudo(QTreeWidget):
    estruturaAlterada = QtCore.Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDropIndicatorShown(True)
        
    def dropEvent(self, event: QtGui.QDropEvent):
        if self.dragDropMode() == QAbstractItemView.DragDropMode.InternalMove:
            super().dropEvent(event)
            self.estruturaAlterada.emit()
        else:
            event.ignore()

class AbaConteudo(QWidget):
    def __init__(self, documento, parent=None):
        super().__init__(parent)
        self.documento = documento
        self._carregando_capitulo = False
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(350)

        left_layout.addWidget(QLabel("Estrutura do Documento"))

        self.busca_arvore_input = QLineEdit()
        # ALTERADO: Placeholder reflete a nova capacidade de busca
        self.busca_arvore_input.setPlaceholderText("Filtrar tópicos e conteúdos...")
        self.busca_arvore_input.textChanged.connect(self._filtrar_arvore)
        left_layout.addWidget(self.busca_arvore_input)
        
        self.chk_reorganizar = QCheckBox("Habilitar Reorganização (Arrastar e Soltar)")
        self.chk_reorganizar.stateChanged.connect(self._alternar_modo_arrastar)
        left_layout.addWidget(self.chk_reorganizar)

        self.arvore_capitulos = ArvoreConteudo()
        self.arvore_capitulos.setHeaderLabel("Tópicos")
        self.arvore_capitulos.estruturaAlterada.connect(self._sincronizar_modelo_com_arvore)
        self.arvore_capitulos.currentItemChanged.connect(self._carregar_capitulo_no_editor)
        self.arvore_capitulos.itemChanged.connect(self._renomear_capitulo)
        
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
        layout.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.label_capitulo_atual = QLabel("Selecione um tópico para editar")
        self.editor_capitulo = QTextEdit()
        self.editor_capitulo.textChanged.connect(self._salvar_conteudo_capitulo)
        
        self.lista_tabelas = QListWidget()
        self.lista_figuras = QListWidget()

        elementos_layout = QHBoxLayout()
        tabelas_widget = QWidget()
        tabelas_v_layout = QVBoxLayout(tabelas_widget)
        tabelas_v_layout.addWidget(QLabel("Banco de Tabelas do Tópico:"))
        tabelas_v_layout.addWidget(self.lista_tabelas)
        tabelas_btn_layout = QHBoxLayout()
        btn_add_tabela = QPushButton("Criar Tabela")
        btn_edit_tabela = QPushButton("Editar Tabela")
        btn_del_tabela = QPushButton("Remover Tabela")
        tabelas_btn_layout.addWidget(btn_add_tabela); tabelas_btn_layout.addWidget(btn_edit_tabela); tabelas_btn_layout.addWidget(btn_del_tabela)
        tabelas_v_layout.addLayout(tabelas_btn_layout)
        btn_ins_tabela = QPushButton("Inserir no Texto")
        tabelas_v_layout.addWidget(btn_ins_tabela)
        
        btn_add_tabela.clicked.connect(self._adicionar_tabela); btn_edit_tabela.clicked.connect(self._editar_tabela); btn_del_tabela.clicked.connect(self._remover_tabela)
        btn_ins_tabela.clicked.connect(self._inserir_marcador_tabela)
        
        figuras_widget = QWidget()
        figuras_v_layout = QVBoxLayout(figuras_widget)
        figuras_v_layout.addWidget(QLabel("Banco de Figuras do Tópico:"))
        figuras_v_layout.addWidget(self.lista_figuras)
        figuras_btn_layout = QHBoxLayout()
        btn_add_figura = QPushButton("Criar Figura"); btn_edit_figura = QPushButton("Editar Figura"); btn_del_figura = QPushButton("Remover Figura")
        figuras_btn_layout.addWidget(btn_add_figura); figuras_btn_layout.addWidget(btn_edit_figura); figuras_btn_layout.addWidget(btn_del_figura)
        figuras_v_layout.addLayout(figuras_btn_layout)
        btn_ins_figura = QPushButton("Inserir no Texto")
        figuras_v_layout.addWidget(btn_ins_figura)
        
        btn_add_figura.clicked.connect(self._adicionar_figura); btn_edit_figura.clicked.connect(self._editar_figura); btn_del_figura.clicked.connect(self._remover_figura)
        btn_ins_figura.clicked.connect(self._inserir_marcador_figura)
        
        elementos_layout.addWidget(tabelas_widget); elementos_layout.addWidget(figuras_widget)

        right_layout.addWidget(self.label_capitulo_atual)
        right_layout.addWidget(self.editor_capitulo, 2)
        right_layout.addLayout(elementos_layout, 1)
        layout.addWidget(right_panel)
        
        self._popular_arvore()
        if self.arvore_capitulos.topLevelItemCount() > 0:
            self.arvore_capitulos.setCurrentItem(self.arvore_capitulos.topLevelItem(0))

    @QtCore.Slot(str)
    def _filtrar_arvore(self, texto_busca):
        texto_busca = texto_busca.lower()
        
        def visitar_item(item):
            capitulo_modelo = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            
            # --- LÓGICA DE BUSCA APRIMORADA ---
            # 1. Verifica se o título corresponde
            titulo_corresponde = texto_busca in item.text(0).lower()
            
            # 2. Verifica se o conteúdo do capítulo corresponde
            conteudo_corresponde = False
            if capitulo_modelo and capitulo_modelo.conteudo:
                conteudo_corresponde = texto_busca in capitulo_modelo.conteudo.lower()
            
            item_corresponde = titulo_corresponde or conteudo_corresponde
            # --- FIM DA LÓGICA DE BUSCA ---

            algum_filho_corresponde = False
            for i in range(item.childCount()):
                if visitar_item(item.child(i)):
                    algum_filho_corresponde = True
            
            deve_ficar_visivel = item_corresponde or algum_filho_corresponde
            item.setHidden(not deve_ficar_visivel)
            
            if algum_filho_corresponde:
                item.setExpanded(True)
                
            return deve_ficar_visivel

        root = self.arvore_capitulos.invisibleRootItem()
        for i in range(root.childCount()):
            visitar_item(root.child(i))

    @QtCore.Slot(int)
    def _alternar_modo_arrastar(self, state):
        if state == QtCore.Qt.CheckState.Checked.value:
            self.arvore_capitulos.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            self.arvore_capitulos.setHeaderLabel("Tópicos (Modo Reorganizar)")
        else:
            self.arvore_capitulos.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
            self.arvore_capitulos.setHeaderLabel("Tópicos")
            
    @QtCore.Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _carregar_capitulo_no_editor(self, item_atual, item_anterior):
        capitulo = self._get_capitulo_selecionado()
        if not capitulo:
            self.editor_capitulo.clear()
            self.editor_capitulo.setEnabled(False)
            self.lista_tabelas.clear()
            self.lista_figuras.clear()
            self.label_capitulo_atual.setText("Selecione um tópico")
            return
        
        self._carregando_capitulo = True
        self.label_capitulo_atual.setText(f"Editando: {capitulo.titulo}")
        self.editor_capitulo.setPlainText(capitulo.conteudo)
        self.editor_capitulo.setEnabled(True)
        self.lista_tabelas.clear()
        for tabela in capitulo.tabelas:
            self.lista_tabelas.addItem(tabela.titulo)
        self.lista_figuras.clear()
        for figura in capitulo.figuras:
            self.lista_figuras.addItem(figura.titulo)
        self._carregando_capitulo = False
        
    @QtCore.Slot()
    def _adicionar_tabela(self):
        capitulo = self._get_capitulo_selecionado()
        if not capitulo:
            QMessageBox.warning(self, "Atenção", "Selecione um tópico para criar uma tabela.")
            return
        dialog = TabelaDialog(parent=self)
        if dialog.exec():
            nova_tabela = dialog.get_dados_tabela()
            capitulo.tabelas.append(nova_tabela)
            self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)

    @QtCore.Slot()
    def _adicionar_figura(self):
        capitulo = self._get_capitulo_selecionado()
        if not capitulo:
            QMessageBox.warning(self, "Atenção", "Selecione um tópico para criar uma figura.")
            return
        dialog = DialogoFigura(parent=self)
        if dialog.exec():
            nova_figura = dialog.get_dados_figura()
            if nova_figura and nova_figura.caminho_processado:
                capitulo.figuras.append(nova_figura)
                self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)
            else:
                QMessageBox.critical(self, "Erro", "A imagem não foi selecionada ou não pôde ser processada.")
    
    @QtCore.Slot()
    def _inserir_marcador_tabela(self):
        item_selecionado = self.lista_tabelas.currentItem()
        if not item_selecionado:
            QMessageBox.warning(self, "Atenção", "Selecione uma tabela do banco para inserir.")
            return
        titulo_tabela = item_selecionado.text()
        marcador = f"\n{{{{Tabela:{titulo_tabela}}}}}\n"
        self.editor_capitulo.insertPlainText(marcador)

    @QtCore.Slot()
    def _inserir_marcador_figura(self):
        item_selecionado = self.lista_figuras.currentItem()
        if not item_selecionado:
            QMessageBox.warning(self, "Atenção", "Selecione uma figura do banco para inserir.")
            return
        titulo_figura = item_selecionado.text()
        marcador = f"\n{{{{Figura:{titulo_figura}}}}}\n"
        self.editor_capitulo.insertPlainText(marcador)

    def _get_capitulo_selecionado(self) -> Capitulo | None:
        item = self.arvore_capitulos.currentItem()
        return item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item else None

    @QtCore.Slot()
    def _salvar_conteudo_capitulo(self):
        if self._carregando_capitulo: return
        capitulo = self._get_capitulo_selecionado()
        if capitulo:
            capitulo.conteudo = self.editor_capitulo.toPlainText()

    @QtCore.Slot()
    def _editar_tabela(self):
        capitulo = self._get_capitulo_selecionado()
        linha_selecionada = self.lista_tabelas.currentRow()
        if not capitulo or linha_selecionada == -1: return
        tabela_para_editar = capitulo.tabelas[linha_selecionada]
        dialog = TabelaDialog(tabela=tabela_para_editar, parent=self)
        if dialog.exec():
            tabela_atualizada = dialog.get_dados_tabela()
            capitulo.tabelas[linha_selecionada] = tabela_atualizada
            self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)

    @QtCore.Slot()
    def _remover_tabela(self):
        capitulo = self._get_capitulo_selecionado()
        linha_selecionada = self.lista_tabelas.currentRow()
        if not capitulo or linha_selecionada == -1: return
        if QMessageBox.question(self, "Confirmar", "Remover esta tabela do banco?") == QMessageBox.StandardButton.Yes:
            del capitulo.tabelas[linha_selecionada]
            self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)
            
    @QtCore.Slot()
    def _editar_figura(self):
        capitulo = self._get_capitulo_selecionado()
        linha_selecionada = self.lista_figuras.currentRow()
        if not capitulo or linha_selecionada == -1: return
        figura_para_editar = capitulo.figuras[linha_selecionada]
        dialog = DialogoFigura(figura=figura_para_editar, parent=self)
        if dialog.exec():
            figura_atualizada = dialog.get_dados_figura()
            if figura_atualizada and figura_atualizada.caminho_processado:
                capitulo.figuras[linha_selecionada] = figura_atualizada
                self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)
    
    @QtCore.Slot()
    def _remover_figura(self):
        capitulo = self._get_capitulo_selecionado()
        linha_selecionada = self.lista_figuras.currentRow()
        if not capitulo or linha_selecionada == -1: return
        if QMessageBox.question(self, "Confirmar", "Remover esta figura do banco?") == QMessageBox.StandardButton.Yes:
            del capitulo.figuras[linha_selecionada]
            self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)
    
    def _popular_arvore(self):
        self.arvore_capitulos.blockSignals(True)
        self.arvore_capitulos.clear()
        def adicionar_filhos_recursivo(no_pai_modelo, no_pai_widget):
            for filho_modelo in no_pai_modelo.filhos:
                item_widget = QTreeWidgetItem([filho_modelo.titulo])
                item_widget.setData(0, QtCore.Qt.ItemDataRole.UserRole, filho_modelo)
                item_widget.setFlags(item_widget.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                if not filho_modelo.is_template_item and filho_modelo.pai == self.documento.estrutura_textual:
                    font = item_widget.font(0); font.setItalic(True)
                    item_widget.setFont(0, font)
                    item_widget.setForeground(0, QtGui.QColor('dimgray'))
                    item_widget.setToolTip(0, "Este é um capítulo personalizado (não pertence ao modelo padrão).")
                if no_pai_widget is self.arvore_capitulos:
                    no_pai_widget.addTopLevelItem(item_widget)
                else:
                    no_pai_widget.addChild(item_widget)
                adicionar_filhos_recursivo(filho_modelo, item_widget)
        adicionar_filhos_recursivo(self.documento.estrutura_textual, self.arvore_capitulos)
        self.arvore_capitulos.expandAll()
        self.arvore_capitulos.blockSignals(False)

    @QtCore.Slot()
    def _adicionar_topico_principal(self):
        novo_capitulo = Capitulo(titulo="Novo Tópico")
        self.documento.estrutura_textual.adicionar_filho(novo_capitulo)
        self._popular_arvore()

    @QtCore.Slot()
    def _adicionar_subtopico(self):
        item_pai_widget = self.arvore_capitulos.currentItem()
        if not item_pai_widget:
            QMessageBox.warning(self, "Atenção", "Selecione um tópico para adicionar um subtópico.")
            return
        no_pai_modelo = item_pai_widget.data(0, QtCore.Qt.ItemDataRole.UserRole)
        novo_subtopico = Capitulo(titulo="Novo Subtópico")
        no_pai_modelo.adicionar_filho(novo_subtopico)
        self._popular_arvore()
        item_pai_widget.setExpanded(True)
        
    @QtCore.Slot()
    def _remover_topico(self):
        item_selecionado = self.arvore_capitulos.currentItem()
        if not item_selecionado: return
        no_modelo = item_selecionado.data(0, QtCore.Qt.ItemDataRole.UserRole)
        mensagem = f"Remover o tópico '{no_modelo.titulo}'?"
        if no_modelo.filhos:
            mensagem = f"Remover o tópico '{no_modelo.titulo}' e todos os seus subtópicos?"
        resposta = QMessageBox.question(self, "Confirmar Remoção", mensagem,
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resposta == QMessageBox.StandardButton.Yes:
            no_pai_modelo = no_modelo.pai
            if no_pai_modelo:
                no_pai_modelo.filhos.remove(no_modelo)
                self._popular_arvore()
            
    @QtCore.Slot(QTreeWidgetItem, int)
    def _renomear_capitulo(self, item, column):
        no_modelo = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if no_modelo and no_modelo.titulo != item.text(column):
            no_modelo.titulo = item.text(column)
            if self.arvore_capitulos.currentItem() is item:
                self.label_capitulo_atual.setText(f"Editando: {no_modelo.titulo}")
                
    def sincronizar_conteudo_pendente(self):
        self._salvar_conteudo_capitulo()
        
    @QtCore.Slot()
    def _sincronizar_modelo_com_arvore(self):
        nova_raiz = Capitulo(titulo="Raiz do Documento")
        def percorrer_arvore_ui(parent_item_widget, parent_node_modelo):
            for i in range(parent_item_widget.childCount()):
                child_item_widget = parent_item_widget.child(i)
                child_node_modelo = child_item_widget.data(0, QtCore.Qt.ItemDataRole.UserRole)
                child_node_modelo.filhos.clear() 
                parent_node_modelo.adicionar_filho(child_node_modelo)
                percorrer_arvore_ui(child_item_widget, child_node_modelo)
        root_widget = self.arvore_capitulos.invisibleRootItem()
        percorrer_arvore_ui(root_widget, nova_raiz)
        self.documento.estrutura_textual.filhos = nova_raiz.filhos