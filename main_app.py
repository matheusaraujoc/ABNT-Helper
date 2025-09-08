# main_app.py
# Descrição: Aplicação principal com a interface gráfica finalizada e corrigida.

import sys
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
                               QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, 
                               QMessageBox, QTabWidget, QComboBox, QListWidget, 
                               QInputDialog, QDialog, QFormLayout, QDialogButtonBox)

from documento import DocumentoABNT, Autor, Capitulo
from gerador_docx import GeradorDOCX
from referencia import Livro, Artigo, Site

class ReferenciaDialog(QDialog):
    """Dialog para adicionar ou editar uma referência."""
    def __init__(self, ref=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Referência")
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # --- ## CORREÇÃO 1: LÓGICA DO FORMULÁRIO DINÂMICO ## ---
        # A lógica foi refeita para OCULTAR/EXIBIR campos em vez de DELETÁ-LOS.
        
        # 1. Criar TODOS os widgets de uma vez.
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Livro", "Artigo", "Site"])
        
        self.autores_input = QLineEdit()
        self.autores_input.setPlaceholderText("Autor 1; Autor 2")
        self.titulo_input = QLineEdit()
        self.ano_input = QLineEdit()

        self.campos_livro = {
            "Local": QLineEdit(),
            "Editora": QLineEdit()
        }
        self.campos_artigo = {
            "Revista": QLineEdit(),
            "Volume": QLineEdit(),
            "Pág. Inicial": QLineEdit(),
            "Pág. Final": QLineEdit()
        }
        self.campos_site = {
            "URL": QLineEdit(),
            "Data de Acesso": QLineEdit("dd/mm/aaaa")
        }
        
        # 2. Adicionar TODOS os widgets ao layout.
        self.layout.addWidget(QLabel("Tipo de Referência:"))
        self.layout.addWidget(self.tipo_combo)
        self.layout.addLayout(self.form_layout)
        
        self.form_layout.addRow("Autores:", self.autores_input)
        self.form_layout.addRow("Título:", self.titulo_input)
        self.form_layout.addRow("Ano:", self.ano_input)

        for label, widget in self.campos_livro.items():
            self.form_layout.addRow(label, widget)
        for label, widget in self.campos_artigo.items():
            self.form_layout.addRow(label, widget)
        for label, widget in self.campos_site.items():
            self.form_layout.addRow(label, widget)
            
        # 3. Conectar o ComboBox para mostrar/ocultar os widgets corretos.
        self.tipo_combo.currentTextChanged.connect(self.update_form_visibility)
        
        # Botões
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        # 4. Chamar a função de visibilidade para o estado inicial.
        self.update_form_visibility(self.tipo_combo.currentText())

    def update_form_visibility(self, tipo):
        """Oculta ou exibe os campos específicos de cada tipo de referência."""
        # Oculta todos os campos específicos
        all_specific_fields = {**self.campos_livro, **self.campos_artigo, **self.campos_site}
        for widget in all_specific_fields.values():
            # Pega o label associado ao widget e o oculta também
            label = self.form_layout.labelForField(widget)
            if label:
                label.setVisible(False)
            widget.setVisible(False)

        # Exibe apenas os campos do tipo selecionado
        fields_to_show = {}
        if tipo == "Livro":
            fields_to_show = self.campos_livro
        elif tipo == "Artigo":
            fields_to_show = self.campos_artigo
        elif tipo == "Site":
            fields_to_show = self.campos_site
            
        for widget in fields_to_show.values():
            label = self.form_layout.labelForField(widget)
            if label:
                label.setVisible(True)
            widget.setVisible(True)
    # --- FIM DA CORREÇÃO 1 ---

    def get_data(self):
        tipo = self.tipo_combo.currentText()
        try:
            ano_val = int(self.ano_input.text()) if self.ano_input.text().isdigit() else 0
        except ValueError:
            ano_val = 0

        common_data = {
            "autores": self.autores_input.text(),
            "titulo": self.titulo_input.text(),
            "ano": ano_val
        }

        if tipo == "Livro":
            specific_data = {k.lower(): w.text() for k, w in self.campos_livro.items()}
            return Livro(**common_data, **specific_data)
        elif tipo == "Artigo":
            try:
                pg_ini = int(self.campos_artigo["Pág. Inicial"].text() or 0)
                pg_fim = int(self.campos_artigo["Pág. Final"].text() or 0)
            except ValueError:
                pg_ini, pg_fim = 0, 0
            specific_data = {
                "revista": self.campos_artigo["Revista"].text(),
                "volume": self.campos_artigo["Volume"].text(),
                "pagina_inicial": pg_ini,
                "pagina_final": pg_fim
            }
            return Artigo(**common_data, **specific_data)
        elif tipo == "Site":
            specific_data = {k.lower().replace(' de ', '_'): w.text() for k, w in self.campos_site.items()}
            return Site(**common_data, **specific_data)
        return None

class ABNTHelperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ABNT Helper Final - Editor de Alta Fidelidade')
        self.setGeometry(100, 100, 950, 750)
        self.documento = DocumentoABNT()
        self._build_ui()
        self._carregando_capitulo = False

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.tabs.addTab(self._criar_aba_geral(), "Geral e Pré-Textual")
        self.tabs.addTab(self._criar_aba_conteudo(), "Conteúdo Textual")
        self.tabs.addTab(self._criar_aba_referencias(), "Referências")
        
        self.generate_btn = QPushButton("Gerar Documento .docx")
        self.generate_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        self.generate_btn.clicked.connect(self._gerar_documento)
        main_layout.addWidget(self.generate_btn)

    def _criar_aba_geral(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("<h3>Configurações do Documento</h3>"))
        form_layout1 = QFormLayout()
        
        # --- ## CORREÇÃO 2: REINSERÇÃO DO CAMPO "TIPO DE TRABALHO" ## ---
        self.cfg_tipo = QComboBox()
        self.cfg_tipo.addItems(["Trabalho de Conclusão de Curso (TCC)", "Artigo Científico", "Dissertação de Mestrado", "Tese de Doutorado"])
        form_layout1.addRow("Tipo de Trabalho:", self.cfg_tipo)
        # --- FIM DA CORREÇÃO 2 ---

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

    def _criar_aba_conteudo(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(300)

        left_layout.addWidget(QLabel("Estrutura do Documento"))
        self.lista_capitulos = QListWidget()
        self.lista_capitulos.addItems([c.titulo for c in self.documento.capitulos])
        self.lista_capitulos.currentItemChanged.connect(self._carregar_capitulo_no_editor)
        left_layout.addWidget(self.lista_capitulos)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Adicionar")
        btn_add.clicked.connect(self._adicionar_capitulo)
        btn_rename = QPushButton("Renomear")
        btn_rename.clicked.connect(self._renomear_capitulo)
        btn_del = QPushButton("Remover")
        btn_del.clicked.connect(self._remover_capitulo)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_rename)
        btn_layout.addWidget(btn_del)
        left_layout.addLayout(btn_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.label_capitulo_atual = QLabel("Selecione um capítulo para editar")
        self.editor_capitulo = QTextEdit()
        self.editor_capitulo.textChanged.connect(self._salvar_conteudo_capitulo)
        right_layout.addWidget(self.label_capitulo_atual)
        right_layout.addWidget(self.editor_capitulo)

        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        if self.lista_capitulos.count() > 0:
            self.lista_capitulos.setCurrentRow(0)
            
        return widget

    def _criar_aba_referencias(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("<h3>Gerenciador de Referências</h3>"))
        self.lista_referencias = QListWidget()
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

    # Métodos para gerenciar capítulos (sem alterações)
    @QtCore.Slot()
    def _adicionar_capitulo(self):
        titulo, ok = QInputDialog.getText(self, "Novo Capítulo", "Digite o título:")
        if ok and titulo:
            self.documento.capitulos.append(Capitulo(titulo=titulo))
            self.lista_capitulos.addItem(titulo)
            self.lista_capitulos.setCurrentRow(self.lista_capitulos.count() - 1)

    @QtCore.Slot()
    def _renomear_capitulo(self):
        item = self.lista_capitulos.currentItem()
        if not item: return
        linha = self.lista_capitulos.currentRow()
        
        novo_titulo, ok = QInputDialog.getText(self, "Renomear Capítulo", "Novo título:", text=item.text())
        if ok and novo_titulo:
            self.documento.capitulos[linha].titulo = novo_titulo
            item.setText(novo_titulo)

    @QtCore.Slot()
    def _remover_capitulo(self):
        linha = self.lista_capitulos.currentRow()
        if linha == -1: return
        
        if QMessageBox.question(self, "Confirmar", "Remover este capítulo?") == QMessageBox.Yes:
            self.lista_capitulos.takeItem(linha)
            del self.documento.capitulos[linha]

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def _carregar_capitulo_no_editor(self, item_atual, item_anterior):
        if not item_atual:
            self.editor_capitulo.clear()
            self.editor_capitulo.setEnabled(False)
            self.label_capitulo_atual.setText("Selecione um capítulo")
            return
        
        self._carregando_capitulo = True
        linha = self.lista_capitulos.row(item_atual)
        self.label_capitulo_atual.setText(f"Editando: {self.documento.capitulos[linha].titulo}")
        self.editor_capitulo.setPlainText(self.documento.capitulos[linha].conteudo)
        self.editor_capitulo.setEnabled(True)
        self._carregando_capitulo = False

    @QtCore.Slot()
    def _salvar_conteudo_capitulo(self):
        if self._carregando_capitulo: return
        linha = self.lista_capitulos.currentRow()
        if linha != -1:
            self.documento.capitulos[linha].conteudo = self.editor_capitulo.toPlainText()

    # Métodos para gerenciar referências (sem alterações)
    @QtCore.Slot()
    def _adicionar_referencia(self):
        dialog = ReferenciaDialog(self)
        if dialog.exec():
            nova_ref = dialog.get_data()
            if nova_ref:
                self.documento.referencias.append(nova_ref)
                self.lista_referencias.addItem(nova_ref.formatar().replace('**', ''))

    @QtCore.Slot()
    def _remover_referencia(self):
        linha = self.lista_referencias.currentRow()
        if linha == -1: return
        if QMessageBox.question(self, "Confirmar", "Remover esta referência?") == QMessageBox.Yes:
            self.lista_referencias.takeItem(linha)
            del self.documento.referencias[linha]

    # Sincronização e Geração
    def _sincronizar_modelo_com_ui(self):
        """Coleta todos os dados da UI e atualiza o objeto self.documento."""
        cfg = self.documento.configuracoes
        cfg.tipo_trabalho = self.cfg_tipo.currentText() # Adicionado
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