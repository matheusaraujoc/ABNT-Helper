# aba_conteudo.py
# Descrição: Versão definitiva com a lógica de "arrastar e soltar" corrigida
# e a sincronização com o modelo de dados garantida.

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import (QWidget, QLabel, QTextEdit, QPushButton, QListWidget,
                               QVBoxLayout, QHBoxLayout, QMessageBox, 
                               QTreeWidget, QTreeWidgetItem, QInputDialog, QAbstractItemView)

from documento import Capitulo
from dialogo_tabela import TabelaDialog

# --- ## NOVO: Subclasse de QTreeWidget para controle total do Drag and Drop ## ---
class ArvoreConteudo(QTreeWidget):
    """
    Uma subclasse de QTreeWidget que emite um sinal personalizado após uma
    operação de arrastar e soltar ser concluída. Isso garante que a
    sincronização do modelo de dados ocorra de forma confiável.
    """
    # Sinal personalizado que será emitido após a estrutura ser alterada
    estruturaAlterada = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurações do Drag and Drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def dropEvent(self, event: QtGui.QDropEvent):
        """
        Sobrescreve o evento 'drop' padrão.
        """
        # 1. Deixa a implementação padrão do Qt fazer a movimentação visual do item.
        super().dropEvent(event)
        
        # 2. Emite nosso sinal personalizado para notificar a aplicação que a
        #    estrutura mudou e precisa ser sincronizada com o modelo de dados.
        self.estruturaAlterada.emit()
# --- FIM DA NOVA CLASSE ---

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

        left_layout.addWidget(QLabel("Estrutura do Documento (clique e arraste para reordenar)"))
        
        # --- ## ALTERADO: Usa nossa nova classe ArvoreConteudo ## ---
        self.arvore_capitulos = ArvoreConteudo() 
        self.arvore_capitulos.setHeaderLabel("Tópicos")
        
        # Conecta o novo sinal personalizado ao nosso método de sincronização
        self.arvore_capitulos.estruturaAlterada.connect(self._sincronizar_modelo_com_arvore)
        
        self.arvore_capitulos.currentItemChanged.connect(self._carregar_capitulo_no_editor)
        self.arvore_capitulos.itemChanged.connect(self._renomear_capitulo)
        self._popular_arvore()
        left_layout.addWidget(self.arvore_capitulos)

        # O restante do _build_ui permanece o mesmo
        btn_layout = QHBoxLayout()
        btn_add_topico = QPushButton("Novo Tópico"); btn_add_sub = QPushButton("Novo Subtópico")
        btn_del = QPushButton("Remover"); btn_layout.addWidget(btn_add_topico)
        btn_layout.addWidget(btn_add_sub); btn_layout.addWidget(btn_del)
        btn_add_topico.clicked.connect(self._adicionar_topico_principal)
        btn_add_sub.clicked.connect(self._adicionar_subtopico)
        btn_del.clicked.connect(self._remover_topico)
        left_layout.addLayout(btn_layout); layout.addWidget(left_panel)
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.label_capitulo_atual = QLabel("Selecione um tópico para editar")
        self.editor_capitulo = QTextEdit()
        self.editor_capitulo.textChanged.connect(self._salvar_conteudo_capitulo)
        self.label_tabelas = QLabel("Tabelas neste Tópico:")
        self.lista_tabelas = QListWidget(); self.lista_tabelas.setMaximumHeight(150)
        tabelas_btn_layout = QHBoxLayout()
        btn_add_tabela = QPushButton("Adicionar Tabela"); btn_edit_tabela = QPushButton("Editar Tabela")
        btn_del_tabela = QPushButton("Remover Tabela"); tabelas_btn_layout.addWidget(btn_add_tabela)
        tabelas_btn_layout.addWidget(btn_edit_tabela); tabelas_btn_layout.addWidget(btn_del_tabela)
        btn_add_tabela.clicked.connect(self._adicionar_tabela)
        btn_edit_tabela.clicked.connect(self._editar_tabela)
        btn_del_tabela.clicked.connect(self._remover_tabela)
        right_layout.addWidget(self.label_capitulo_atual); right_layout.addWidget(self.editor_capitulo, 3)
        right_layout.addWidget(self.label_tabelas); right_layout.addWidget(self.lista_tabelas, 1)
        right_layout.addLayout(tabelas_btn_layout); layout.addWidget(right_panel)
        if self.arvore_capitulos.topLevelItemCount() > 0:
            self.arvore_capitulos.setCurrentItem(self.arvore_capitulos.topLevelItem(0))

    # --- O método de sincronização está correto e agora será chamado de forma confiável ---
    @QtCore.Slot()
    def _sincronizar_modelo_com_arvore(self):
        self.documento.estrutura_textual.filhos.clear()
        def percorrer_arvore_ui(parent_item_widget, parent_node_modelo):
            for i in range(parent_item_widget.childCount()):
                child_item_widget = parent_item_widget.child(i)
                child_node_modelo = child_item_widget.data(0, QtCore.Qt.ItemDataRole.UserRole)
                child_node_modelo.filhos.clear()
                parent_node_modelo.adicionar_filho(child_node_modelo)
                percorrer_arvore_ui(child_item_widget, child_node_modelo)
        root_widget = self.arvore_capitulos.invisibleRootItem()
        percorrer_arvore_ui(root_widget, self.documento.estrutura_textual)
        print("Modelo de dados sincronizado com a nova ordem da árvore.")

    # O restante do arquivo não precisa de alterações
    @QtCore.Slot()
    def _adicionar_topico_principal(self):
        novo_capitulo = Capitulo(titulo="Novo Tópico")
        self.documento.estrutura_textual.adicionar_filho(novo_capitulo)
        item_widget = QTreeWidgetItem([novo_capitulo.titulo])
        item_widget.setData(0, QtCore.Qt.ItemDataRole.UserRole, novo_capitulo)
        item_widget.setFlags(item_widget.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        self.arvore_capitulos.addTopLevelItem(item_widget)
        self.arvore_capitulos.setCurrentItem(item_widget)

    @QtCore.Slot()
    def _adicionar_subtopico(self):
        item_pai_widget = self.arvore_capitulos.currentItem()
        if not item_pai_widget:
            QMessageBox.warning(self, "Atenção", "Selecione um tópico para adicionar um subtópico.")
            return
        no_pai_modelo = item_pai_widget.data(0, QtCore.Qt.ItemDataRole.UserRole)
        novo_subtopico = Capitulo(titulo="Novo Subtópico")
        no_pai_modelo.adicionar_filho(novo_subtopico)
        item_filho_widget = QTreeWidgetItem([novo_subtopico.titulo])
        item_filho_widget.setData(0, QtCore.Qt.ItemDataRole.UserRole, novo_subtopico)
        item_filho_widget.setFlags(item_filho_widget.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        item_pai_widget.addChild(item_filho_widget)
        self.arvore_capitulos.expandItem(item_pai_widget)
        self.arvore_capitulos.setCurrentItem(item_filho_widget)

    @QtCore.Slot()
    def _remover_topico(self):
        item_selecionado = self.arvore_capitulos.currentItem()
        if not item_selecionado: return
        resposta = QMessageBox.question(self, "Confirmar", "Remover este tópico e todos os seus subtópicos?")
        if resposta == QMessageBox.StandardButton.Yes:
            no_modelo = item_selecionado.data(0, QtCore.Qt.ItemDataRole.UserRole)
            no_pai_modelo = no_modelo.pai
            if no_pai_modelo:
                no_pai_modelo.filhos.remove(no_modelo)
            item_pai_widget = item_selecionado.parent()
            if item_pai_widget:
                item_pai_widget.removeChild(item_selecionado)
            else:
                index = self.arvore_capitulos.indexOfTopLevelItem(item_selecionado)
                self.arvore_capitulos.takeTopLevelItem(index)

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

    def _get_capitulo_selecionado(self) -> Capitulo | None:
        item = self.arvore_capitulos.currentItem()
        if item:
            return item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        return None

    @QtCore.Slot(QTreeWidgetItem)
    def _carregar_capitulo_no_editor(self, item_atual, item_anterior):
        capitulo = self._get_capitulo_selecionado()
        if not capitulo:
            self.editor_capitulo.clear(); self.editor_capitulo.setEnabled(False)
            self.lista_tabelas.clear(); self.label_capitulo_atual.setText("Selecione um tópico")
            return
        self._carregando_capitulo = True
        self.label_capitulo_atual.setText(f"Editando: {capitulo.titulo}")
        self.editor_capitulo.setPlainText(capitulo.conteudo)
        self.editor_capitulo.setEnabled(True)
        self.lista_tabelas.clear()
        for i, tabela in enumerate(capitulo.tabelas):
            self.lista_tabelas.addItem(f"Tabela {i+1}: {tabela.titulo}")
        self._carregando_capitulo = False

    @QtCore.Slot()
    def _salvar_conteudo_capitulo(self):
        if self._carregando_capitulo: return
        capitulo = self._get_capitulo_selecionado()
        if capitulo:
            capitulo.conteudo = self.editor_capitulo.toPlainText()
            
    @QtCore.Slot()
    def _adicionar_tabela(self):
        capitulo = self._get_capitulo_selecionado()
        if not capitulo:
            QMessageBox.warning(self, "Atenção", "Selecione um tópico para adicionar uma tabela.")
            return
        dialog = TabelaDialog(parent=self)
        if dialog.exec():
            nova_tabela = dialog.get_dados_tabela()
            capitulo.tabelas.append(nova_tabela)
            self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)

    @QtCore.Slot()
    def _editar_tabela(self):
        capitulo = self._get_capitulo_selecionado()
        linha_selecionada = self.lista_tabelas.currentRow()
        if not capitulo or linha_selecionada == -1:
            QMessageBox.warning(self, "Atenção", "Selecione uma tabela para editar.")
            return
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
        if not capitulo or linha_selecionada == -1:
            QMessageBox.warning(self, "Atenção", "Selecione uma tabela para remover.")
            return
        if QMessageBox.question(self, "Confirmar", "Remover esta tabela?") == QMessageBox.StandardButton.Yes:
            del capitulo.tabelas[linha_selecionada]
            self._carregar_capitulo_no_editor(self.arvore_capitulos.currentItem(), None)
            
    @QtCore.Slot(QTreeWidgetItem, int)
    def _renomear_capitulo(self, item, column):
        no_modelo = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if no_modelo and no_modelo.titulo != item.text(column):
            no_modelo.titulo = item.text(column)
            if self.arvore_capitulos.currentItem() is item:
                self.label_capitulo_atual.setText(f"Editando: {no_modelo.titulo}")
                
    def sincronizar_conteudo_pendente(self):
        self._salvar_conteudo_capitulo()