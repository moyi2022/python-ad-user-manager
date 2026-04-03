import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QLinearGradient, QFont
from PyQt5.QtCore import QRectF
from utils.resource_helper import get_resource_path


class SettingsDialog(QDialog):
    def __init__(self, settings_service):
        super().__init__()
        self.settings = settings_service
        self._load_stylesheet()
        self._set_window_icon()
        self.init_ui()

    def _load_stylesheet(self):
        """加载 QSS 样式表"""
        style_path = get_resource_path('resources/style.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def _set_window_icon(self):
        """设置窗口图标"""
        icon_path = get_resource_path('resources/icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            return

        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, 64, 64)
        gradient.setColorAt(0, QColor(66, 165, 245))
        gradient.setColorAt(1, QColor(156, 39, 176))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 60, 60, 10, 10)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(22, 14, 20, 20)
        painter.drawRoundedRect(16, 36, 32, 22, 10, 10)
        painter.setPen(QColor(255, 255, 255))
        font = QFont('Arial', 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 46, 64, 20), Qt.AlignCenter, 'AD')
        painter.end()
        self.setWindowIcon(QIcon(pixmap))

    def init_ui(self):
        self.setWindowTitle('⚙ 设置')
        self.setFixedSize(400, 180)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel('⚙ 应用设置')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #89b4fa;')
        layout.addWidget(title_label)

        # Page size
        page_layout = QHBoxLayout()
        page_label = QLabel('每页记录数:')
        page_label.setObjectName('dialogLabel')
        page_label.setFixedWidth(90)
        page_layout.addWidget(page_label)
        self.page_size_input = QLineEdit()
        self.page_size_input.setText(str(self.settings.get('page_size', 25)))
        self.page_size_input.setFixedWidth(100)
        self.page_size_input.setPlaceholderText('25')
        page_layout.addWidget(self.page_size_input)
        page_layout.addStretch()
        layout.addLayout(page_layout)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton('💾 保存')
        self.save_btn.setObjectName('primaryBtn')
        self.save_btn.clicked.connect(self.do_save)
        self.save_btn.setMinimumWidth(100)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def do_save(self):
        try:
            page_size = int(self.page_size_input.text())
            if page_size > 0:
                self.settings.set('page_size', page_size)
                self.settings.save()
                self.accept()
                return
            else:
                QMessageBox.warning(self, '输入错误', '每页记录数必须大于0')
                return
        except ValueError:
            QMessageBox.warning(self, '输入错误', '请输入有效的数字')