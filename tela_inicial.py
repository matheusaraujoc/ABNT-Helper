# tela_inicial.py
# Descrição: Janela de diálogo inicial para boas-vindas, gerenciamento de
# projetos recentes e criação de novos projetos a partir de modelos.

import os
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import (QDialog, QWidget, QLabel, QPushButton, QVBoxLayout,
                               QHBoxLayout, QListWidget, QListWidgetItem,
                               QFileDialog, QMessageBox, QScrollArea, QSizePolicy) # Adicionado QSizePolicy

import gerenciador_config
from modelos_trabalho import get_nomes_modelos

class ProjetoRecenteItem(QWidget):
    """Widget customizado para exibir um item na lista de projetos recentes."""
    def __init__(self, nome, caminho, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        nome_label = QLabel(f"<b>{nome}</b>")
        caminho_label = QLabel(caminho)
        caminho_label.setStyleSheet("color: gray;")
        caminho_label.setWordWrap(True) # Permite que o caminho quebre a linha se for muito longo
        
        layout.addWidget(nome_label)
        layout.addWidget(caminho_label)
        self.setLayout(layout)

class TelaInicial(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bem-vindo ao ABNT Helper")
        # CORREÇÃO 1: Aumentar a largura mínima da janela para dar mais espaço
        self.setMinimumSize(950, 550)
        
        # CORREÇÃO 2: Adicionar a propriedade 'white-space' para permitir quebra de linha nos botões
        self.setStyleSheet("""
            QDialog { background-color: #f0f0f0; }
            QPushButton { 
                background-color: #0078d4; color: white; border: none; 
                padding: 10px; border-radius: 5px; font-size: 14px;
            }
            QPushButton:hover { background-color: #005a9e; }
            #BtnAbrir { 
                background-color: #e0e0e0; color: black;
                text-align: left; /* Alinha o texto à esquerda para melhor leitura */
                padding-left: 15px;
                white-space: normal; /* ESSA É A PROPRIEDADE MÁGICA */
            }
            #BtnAbrir:hover { background-color: #c8c8c8; }
            QListWidget { border: 1px solid #ccc; background-color: white; }
        """)

        self.resultado = (None, None) 

        main_layout = QHBoxLayout(self)

        # --- Painel Esquerdo (Ações) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(250)

        titulo_label = QLabel("ABNT Helper")
        titulo_label.setFont(QtGui.QFont("Segoe UI", 24, QtGui.QFont.Weight.Bold))
        
        btn_novo = QPushButton("Novo Projeto")
        btn_novo.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon))
        btn_novo.clicked.connect(self.on_novo_projeto)

        btn_abrir = QPushButton("Abrir Outro...")
        btn_abrir.setObjectName("BtnAbrir")
        btn_abrir.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon))
        btn_abrir.clicked.connect(self.on_abrir_projeto)

        left_layout.addWidget(titulo_label)
        left_layout.addSpacing(20)
        left_layout.addWidget(btn_novo)
        left_layout.addWidget(btn_abrir)
        left_layout.addStretch()

        # --- Painel Central (Projetos Recentes) ---
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        recentes_label = QLabel("Projetos Recentes")
        recentes_label.setFont(QtGui.QFont("Segoe UI", 16))
        
        self.lista_recentes = QListWidget()
        self.lista_recentes.itemDoubleClicked.connect(self.on_item_recente_clicado)
        self.popular_projetos_recentes()
        
        center_layout.addWidget(recentes_label)
        center_layout.addWidget(self.lista_recentes)

        # --- Painel Direito (Modelos) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        # CORREÇÃO 3: Aumentar a largura do painel de modelos
        right_panel.setFixedWidth(300) 
        
        modelos_label = QLabel("Iniciar com um Modelo")
        modelos_label.setFont(QtGui.QFont("Segoe UI", 16))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.modelos_layout = QVBoxLayout(scroll_content)
        self.modelos_layout.setSpacing(10)
        
        for nome_modelo in get_nomes_modelos():
            btn = QPushButton(nome_modelo)
            btn.setObjectName("BtnAbrir")
            # Faz o botão crescer na altura conforme necessário
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn.clicked.connect(lambda checked=False, m=nome_modelo: self.on_novo_com_modelo(m))
            self.modelos_layout.addWidget(btn)
        
        self.modelos_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        right_layout.addWidget(modelos_label)
        right_layout.addWidget(scroll_area)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel, 1)
        main_layout.addWidget(right_panel)
    
    def popular_projetos_recentes(self):
        self.lista_recentes.clear()
        projetos = gerenciador_config.get_projetos_recentes()
        for proj in projetos:
            item = QListWidgetItem(self.lista_recentes)
            item_widget = ProjetoRecenteItem(proj["name"], proj["path"])
            item.setSizeHint(item_widget.sizeHint())
            item.setData(QtCore.Qt.ItemDataRole.UserRole, proj["path"])
            self.lista_recentes.addItem(item)
            self.lista_recentes.setItemWidget(item, item_widget)

    def on_novo_projeto(self):
        modelo_padrao = get_nomes_modelos()[0] if get_nomes_modelos() else "Trabalho Acadêmico"
        self.resultado = ("novo", modelo_padrao)
        self.accept()
        
    def on_novo_com_modelo(self, nome_modelo):
        self.resultado = ("novo", nome_modelo)
        self.accept()

    def on_abrir_projeto(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Carregar Projeto", "", "Arquivo ABNF (*.abnf)")
        if caminho:
            self.resultado = ("abrir", caminho)
            self.accept()

    def on_item_recente_clicado(self, item):
        caminho = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if os.path.exists(caminho):
            self.resultado = ("abrir", caminho)
            self.accept()
        else:
            QMessageBox.warning(self, "Arquivo não encontrado",
                f"O arquivo do projeto não foi encontrado no caminho:\n\n{caminho}\n\nEle pode ter sido movido ou excluído.")
            gerenciador_config.remover_projeto_recente(caminho)
            self.popular_projetos_recentes()

    def get_resultado(self):
        return self.resultado