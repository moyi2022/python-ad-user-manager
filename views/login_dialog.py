import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from services.ad_service import AdService
from services.settings_service import SettingsService


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ad_service = AdService()
        self.settings = SettingsService()
        self._load_stylesheet()
        self._set_window_icon()
        self.init_ui()

    def _load_stylesheet(self):
        """加载 QSS 样式表"""
        style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'style.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def _set_window_icon(self):
        """设置窗口图标"""
        from PyQt5.QtGui import QPainter, QBrush, QColor, QLinearGradient, QFont
        from PyQt5.QtCore import QRectF

        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            return

        # 动态创建图标
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
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(22, 14, 20, 20)
        painter.drawRoundedRect(16, 36, 32, 22, 10, 10)

        painter.setPen(QColor(255, 255, 255))
        font = QFont('Arial', 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 46, 64, 20), Qt.AlignCenter, 'AD')

        painter.end()
        self.setWindowIcon(QIcon(pixmap))

    def init_ui(self):
        self.setWindowTitle('连接域控制器')
        self.setFixedSize(420, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        # 标题
        title_label = QLabel('🔐 AD 域用户管理')
        title_label.setObjectName('dialogTitle')
        title_label.setStyleSheet('font-size: 18px; font-weight: bold; color: #89b4fa;')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Domain
        domain_layout = QHBoxLayout()
        domain_label = QLabel('域:')
        domain_label.setObjectName('dialogLabel')
        domain_label.setFixedWidth(70)
        domain_layout.addWidget(domain_label)
        self.domain_input = QLineEdit()
        self.domain_input.setText('jtw.local')
        self.domain_input.setReadOnly(True)
        domain_layout.addWidget(self.domain_input)
        layout.addLayout(domain_layout)

        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel('用户名:')
        username_label.setObjectName('dialogLabel')
        username_label.setFixedWidth(70)
        username_layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setText(self.settings.get('saved_username', ''))
        self.username_input.setFocus()
        self.username_input.setPlaceholderText('输入域用户名')
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel('密码:')
        password_label.setObjectName('dialogLabel')
        password_label.setFixedWidth(70)
        password_layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText('输入密码')
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # Error message
        self.error_label = QLabel('')
        self.error_label.setObjectName('errorLabel')
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setMinimumWidth(80)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addSpacing(20)
        self.connect_btn = QPushButton('🔗 连接')
        self.connect_btn.setObjectName('primaryBtn')
        self.connect_btn.setDefault(True)
        self.connect_btn.clicked.connect(self.do_connect)
        self.connect_btn.setMinimumWidth(100)
        button_layout.addWidget(self.connect_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.password_input.returnPressed.connect(self.do_connect)

    def do_connect(self):
        self.error_label.setText('')
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self.error_label.setText('❌ 请输入用户名')
            return
        if not password:
            self.error_label.setText('❌ 请输入密码')
            return

        try:
            self.ad_service.connect(username, password)
            self.settings.set('saved_username', username)
            self.settings.save()
            self.accept()
        except Exception as ex:
            self.error_label.setText(f'❌ {ex}')