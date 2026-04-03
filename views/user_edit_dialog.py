import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QLinearGradient, QFont
from PyQt5.QtCore import QRectF
from services.ad_service import AdService
from utils.resource_helper import get_resource_path


class UserEditDialog(QDialog):
    def __init__(self, ad_service, user=None, reset_password=False, default_ou=None):
        super().__init__()
        self.ad_service = ad_service
        self.user = user or {}
        self.reset_password = reset_password
        self.is_create = user is None
        self.default_ou = default_ou
        self.inputs = {}
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
        if self.reset_password:
            self.setWindowTitle('🔑 重置密码')
        elif self.is_create:
            self.setWindowTitle('➕ 创建用户')
        else:
            self.setWindowTitle('✏ 编辑用户')

        self.setFixedSize(420, 550)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        # Username
        layout.addLayout(self._create_row('👤 用户名:', self._create_input('username')))
        if not self.is_create:
            self.inputs['username'].setEnabled(False)
            self.inputs['username'].setStyleSheet('background-color: #313244; color: #6c7086;')

        # DisplayName
        layout.addLayout(self._create_row('显示名称:', self._create_input('display_name')))

        # LastName
        layout.addLayout(self._create_row('姓氏:', self._create_input('last_name')))

        # FirstName
        layout.addLayout(self._create_row('名字:', self._create_input('first_name')))

        # Email
        layout.addLayout(self._create_row('📧 邮箱:', self._create_input('email')))

        # Department
        layout.addLayout(self._create_row('🏢 部门:', self._create_input('department')))

        # Title
        layout.addLayout(self._create_row('📋 职位:', self._create_input('title')))

        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(280)
        self.password_input.setPlaceholderText('输入密码')
        if self.reset_password or self.is_create:
            layout.addLayout(self._create_row('🔒 密码:', self.password_input))
        else:
            self.password_input.setEnabled(False)

        # Confirm Password
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setFixedWidth(280)
        self.confirm_input.setPlaceholderText('再次输入密码')
        if self.reset_password or self.is_create:
            layout.addLayout(self._create_row('🔒 确认密码:', self.confirm_input))
        else:
            self.confirm_input.setEnabled(False)

        # Enabled
        self.enabled_check = QCheckBox('✓ 启用账户')
        self.enabled_check.setChecked(self.user.get('enabled', True))
        if not self.reset_password:
            layout.addWidget(self.enabled_check)

        layout.addStretch()

        # Error label
        self.error_label = QLabel('')
        self.error_label.setObjectName('errorLabel')
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton('💾 保存')
        self.save_btn.setObjectName('primaryBtn')
        self.save_btn.clicked.connect(self.do_save)
        self.save_btn.setDefault(True)
        self.save_btn.setMinimumWidth(100)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Fill existing data for edit mode
        if self.user and not self.is_create:
            self._set_value('username', self.user.get('username', ''))
            self._set_value('display_name', self.user.get('display_name', ''))
            self._set_value('first_name', self.user.get('first_name', ''))
            self._set_value('last_name', self.user.get('last_name', ''))
            self._set_value('email', self.user.get('email', ''))
            self._set_value('department', self.user.get('department', ''))
            self._set_value('title', self.user.get('title', ''))

    def _create_row(self, label_text, input_widget, small=False):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName('dialogLabel')
        label.setFixedWidth(80 if not small else 60)
        layout.addWidget(label)
        layout.addWidget(input_widget)
        return layout

    def _create_input(self, name):
        input_widget = QLineEdit()
        input_widget.setFixedWidth(280)
        self.inputs[name] = input_widget
        return input_widget

    def _set_value(self, name, value):
        if name in self.inputs:
            self.inputs[name].setText(value)

    def _get_value(self, name):
        if name in self.inputs:
            return self.inputs[name].text().strip()
        return ''

    def do_save(self):
        self.error_label.setText('')

        username = self._get_value('username')
        display_name = self._get_value('display_name')
        first_name = self._get_value('first_name')
        last_name = self._get_value('last_name')
        email = self._get_value('email')
        department = self._get_value('department')
        title = self._get_value('title')
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        enabled = self.enabled_check.isChecked()

        # Validation
        if self.is_create and not username:
            self.error_label.setText('❌ 用户名为必填项')
            return
        if (self.is_create or self.reset_password) and not password:
            self.error_label.setText('❌ 密码为必填项')
            return
        if password and password != confirm:
            self.error_label.setText('❌ 两次密码不一致')
            return

        user_data = {
            'username': username,
            'display_name': display_name,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'department': department,
            'title': title,
            'enabled': enabled
        }

        try:
            if self.reset_password:
                original_username = self.user.get('username')
                user_dn = self.user.get('dn')
                self.ad_service.reset_password(original_username, password, user_dn)
            elif self.is_create:
                user_data['password'] = password
                self.ad_service.create_user(user_data, self.default_ou)
            else:
                original_username = self.user.get('username')
                user_dn = self.user.get('dn')
                self.ad_service.update_user(original_username, user_data, user_dn)
            self.accept()
        except Exception as ex:
            self.error_label.setText(f'❌ {ex}')