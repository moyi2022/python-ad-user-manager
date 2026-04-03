import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLineEdit, QLabel, QHeaderView,
                             QMessageBox, QFileDialog, QCheckBox, QAbstractItemView, QSplitter,
                             QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from services.ad_service import AdService
from services.settings_service import SettingsService
from services.export_service import ExportService
from services.log_service import LogService
from .user_edit_dialog import UserEditDialog
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, ad_service):
        super().__init__()
        self.ad_service = ad_service
        self.settings = SettingsService()
        self.export_service = ExportService()
        self._set_window_icon()
        self.all_users = []
        self.filtered_users = []
        self.selected_users = set()
        self.current_page = 1
        self.page_size = self.settings.get('page_size', 25)
        self.current_ou = None
        self._load_stylesheet()
        self.init_ui()
        self.load_ous()
        self.load_users()

    def _load_stylesheet(self):
        """加载 QSS 样式表"""
        style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'style.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def _set_window_icon(self):
        """设置窗口图标"""
        from PyQt5.QtGui import QPainter, QBrush, QColor, QLinearGradient, QFont
        from PyQt5.QtCore import QRectF, Qt

        # 尝试从文件加载图标
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
        self.setWindowTitle('AD 用户管理器')
        self.resize(self.settings.get('window_width', 1000), self.settings.get('window_height', 700))

        central_widget = QWidget()
        central_widget.setObjectName('centralWidget')
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Status bar
        status_bar = QWidget()
        status_bar.setObjectName('statusBar')
        status_bar.setFixedHeight(32)
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 4, 10, 4)
        self.status_label = QLabel('状态: <b>已连接</b> | 域: jtw.local | 用户: ' + self.settings.get('saved_username', ''))
        self.status_label.setObjectName('statusLabel')
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.settings_btn = QPushButton('⚙ 设置')
        self.settings_btn.clicked.connect(self.open_settings)
        status_layout.addWidget(self.settings_btn)
        self.logout_btn = QPushButton('🚪 退出')
        self.logout_btn.clicked.connect(self.close)
        status_layout.addWidget(self.logout_btn)
        status_bar.setLayout(status_layout)
        layout.addWidget(status_bar)

        # Main content with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - OU Tree
        self.ou_tree = QTreeWidget()
        self.ou_tree.setHeaderLabel('📁 目录结构')
        self.ou_tree.setMinimumWidth(220)
        self.ou_tree.setMaximumWidth(320)
        self.ou_tree.itemClicked.connect(self.on_ou_clicked)

        # Root item for domain
        self.root_item = QTreeWidgetItem(self.ou_tree, ['🌐 jtw.local (全部用户)'])
        self.root_item.setData(0, Qt.UserRole, None)
        self.ou_tree.addTopLevelItem(self.root_item)

        splitter.addWidget(self.ou_tree)

        # Right panel - User list
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setObjectName('toolbar')
        toolbar.setFixedHeight(52)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍 搜索用户名、显示名称...')
        self.search_input.textChanged.connect(self.on_search)
        self.search_input.setFixedWidth(200)
        toolbar_layout.addWidget(self.search_input)

        self.refresh_btn = QPushButton('🔄 刷新')
        self.refresh_btn.clicked.connect(self.load_users)
        toolbar_layout.addWidget(self.refresh_btn)

        self.create_btn = QPushButton('➕ 新建')
        self.create_btn.setObjectName('successBtn')
        self.create_btn.clicked.connect(self.create_user)
        toolbar_layout.addWidget(self.create_btn)

        self.edit_btn = QPushButton('✏ 编辑')
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_user)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton('🗑 删除')
        self.delete_btn.setObjectName('dangerBtn')
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_users)
        toolbar_layout.addWidget(self.delete_btn)

        self.reset_btn = QPushButton('🔑 重置密码')
        self.reset_btn.setEnabled(False)
        self.reset_btn.clicked.connect(self.reset_password)
        toolbar_layout.addWidget(self.reset_btn)

        toolbar_layout.addStretch()

        self.import_btn = QPushButton('📥 导入')
        self.import_btn.clicked.connect(self.import_csv)
        toolbar_layout.addWidget(self.import_btn)

        self.export_btn = QPushButton('📤 导出')
        self.export_btn.clicked.connect(self.export_csv)
        toolbar_layout.addWidget(self.export_btn)

        toolbar.setLayout(toolbar_layout)
        right_layout.addWidget(toolbar)

        # User table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['用户名', '显示名称', '部门', '职位', '邮箱', '状态', ''])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)  # 状态列固定
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # 复选框列固定
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 150)
        self.table.setColumnWidth(6, 50)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)
        right_layout.addWidget(self.table)

        # Pagination
        pagination = QWidget()
        pagination.setObjectName('pagination')
        pagination.setFixedHeight(36)
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(10, 6, 10, 6)

        self.total_label = QLabel('总计: 0')
        self.total_label.setObjectName('totalLabel')
        pagination_layout.addWidget(self.total_label)

        pagination_layout.addStretch()

        self.prev_btn = QPushButton('◀ 上一页')
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel('1 / 1')
        self.page_label.setObjectName('pageLabel')
        pagination_layout.addWidget(self.page_label)

        self.next_btn = QPushButton('下一页 ▶')
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)

        pagination.setLayout(pagination_layout)
        right_layout.addWidget(pagination)

        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([260, 740])

        layout.addWidget(splitter)
        central_widget.setLayout(layout)

    def load_ous(self):
        """加载 OU 目录树"""
        try:
            ous = self.ad_service.get_ous()
            self.ou_tree.setUpdatesEnabled(False)

            # 按层级组织 OU - key 是 parent DN
            ou_dict = {}
            for ou in ous:
                dn = ou.get('dn', '')
                name = ou.get('name', '')

                # 获取父 DN
                parts = dn.split(',')
                if len(parts) > 1:
                    parent_dn = ','.join(parts[1:])
                else:
                    parent_dn = ''

                if parent_dn not in ou_dict:
                    ou_dict[parent_dn] = []
                ou['children'] = []
                ou_dict[parent_dn].append(ou)

            def add_ou_to_tree(parent_item, parent_dn):
                children = ou_dict.get(parent_dn, [])
                for ou in children:
                    child_item = QTreeWidgetItem(parent_item, [f'📂 {ou["name"]}'])
                    child_item.setData(0, Qt.UserRole, ou['dn'])
                    parent_item.addChild(child_item)
                    add_ou_to_tree(child_item, ou['dn'])

            # 添加子节点 - 根节点的 DN 是 DC=jtw,DC=local
            domain_dn = 'DC=jtw,DC=local'
            add_ou_to_tree(self.root_item, domain_dn)

            self.ou_tree.setUpdatesEnabled(True)
            self.root_item.setExpanded(True)

            LogService.log(f'Loaded OU tree with {len(ous)} items')

        except Exception as ex:
            QMessageBox.warning(self, '警告', f'加载目录树失败: {ex}')

    def on_ou_clicked(self, item, column):
        """OU 点击事件"""
        ou_dn = item.data(0, Qt.UserRole)
        self.current_ou = ou_dn
        self.current_page = 1
        # 更新状态栏显示当前 OU
        ou_name = item.text(0).replace('📂 ', '').replace('🌐 ', '')
        self.status_label.setText(f'状态: <b>加载中...</b> | 目录: {ou_name}')
        self.load_users()

    def load_users(self):
        try:
            self.all_users = self.ad_service.get_all_users(self.current_ou)
            self.apply_filter()
            # 显示用户数量
            ou_name = '全部用户' if self.current_ou is None else self.current_ou.split(',')[0].replace('OU=', '').replace('CN=', '')
            self.status_label.setText(f'状态: <b>已连接</b> | 目录: {ou_name} | 用户: {len(self.all_users)}')
        except Exception as ex:
            QMessageBox.critical(self, '错误', f'加载用户列表失败: {ex}')

    def apply_filter(self):
        search_text = self.search_input.text().strip().lower()
        if search_text:
            self.filtered_users = [
                u for u in self.all_users
                if search_text in u.get('username', '').lower()
                or search_text in u.get('display_name', '').lower()
                or search_text in u.get('department', '').lower()
            ]
        else:
            self.filtered_users = self.all_users.copy()
        self.current_page = 1
        self.render_page()

    def render_page(self):
        total_pages = max(1, (len(self.filtered_users) + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, total_pages)

        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_users = self.filtered_users[start:end]

        self.table.setRowCount(len(page_users))
        for row, user in enumerate(page_users):
            self.table.setItem(row, 0, QTableWidgetItem(user.get('username', '')))
            self.table.setItem(row, 1, QTableWidgetItem(user.get('display_name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(user.get('department', '')))
            self.table.setItem(row, 3, QTableWidgetItem(user.get('title', '')))
            self.table.setItem(row, 4, QTableWidgetItem(user.get('email', '')))

            # 状态列 - 使用更直观的显示
            status_item = QTableWidgetItem('✓ 启用' if user.get('enabled') else '✗ 禁用')
            status_item.setForeground(Qt.green if user.get('enabled') else Qt.red)
            self.table.setItem(row, 5, status_item)

            checkbox = QCheckBox()
            checkbox.setChecked(user.get('username') in self.selected_users)
            checkbox.stateChanged.connect(lambda state, u=user: self.toggle_user_selection(u, state))
            self.table.setCellWidget(row, 6, checkbox)

        self.total_label.setText(f'📊 总计: {len(self.filtered_users)} / {len(self.all_users)}')
        self.page_label.setText(f'{self.current_page} / {total_pages}')
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        self.update_button_states()

    def toggle_user_selection(self, user, state):
        username = user.get('username')
        if state == Qt.Checked:
            self.selected_users.add(username)
        else:
            self.selected_users.discard(username)
        self.update_button_states()

    def on_selection_changed(self):
        self.update_button_states()

    def on_table_double_click(self, row, column):
        """双击表格行打开编辑对话框"""
        # 从当前页面获取用户
        start = (self.current_page - 1) * self.page_size
        user_index = start + row
        if 0 <= user_index < len(self.filtered_users):
            user = self.filtered_users[user_index]
            dialog = UserEditDialog(self.ad_service, user)
            if dialog.exec_():
                QMessageBox.information(self, '成功', f'用户 "{user.get("username")}" 更新成功！')
                self.load_users()

    def update_button_states(self):
        has_selection = len(self.selected_users) > 0
        has_single = len(self.selected_users) == 1
        self.edit_btn.setEnabled(has_single)
        self.delete_btn.setEnabled(has_selection)
        self.reset_btn.setEnabled(has_selection)

    def on_search(self, text):
        self.apply_filter()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        total_pages = max(1, (len(self.filtered_users) + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.render_page()

    def create_user(self):
        dialog = UserEditDialog(self.ad_service, None, False, self.current_ou)
        if dialog.exec_():
            new_username = dialog._get_value('username')
            self.load_users()
            QMessageBox.information(self, '成功', f'用户 "{new_username}" 创建成功！')

    def edit_user(self):
        if len(self.selected_users) != 1:
            return
        username = list(self.selected_users)[0]
        user = next((u for u in self.all_users if u.get('username') == username), None)
        if user:
            dialog = UserEditDialog(self.ad_service, user)
            if dialog.exec_():
                QMessageBox.information(self, '成功', f'用户 "{username}" 更新成功！')
                self.load_users()

    def delete_users(self):
        if not self.selected_users:
            return
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除选中的 {len(self.selected_users)} 个用户吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            usernames = list(self.selected_users)
            success = 0
            fail_list = []
            for uname in usernames:
                try:
                    user = next((u for u in self.all_users if u.get('username') == uname), None)
                    user_dn = user.get('dn') if user else None
                    self.ad_service.delete_user(uname, user_dn)
                    success += 1
                except Exception as ex:
                    fail_list.append(f'{uname}: {ex}')
            self.selected_users.clear()
            self.load_users()
            if success > 0 and not fail_list:
                QMessageBox.information(self, '成功', f'删除成功，共 {success} 个用户')
            elif success > 0 and fail_list:
                QMessageBox.warning(self, '部分成功',
                    f'成功删除 {success} 个用户\n失败 {len(fail_list)} 个:\n' + '\n'.join(fail_list[:5]))
            else:
                QMessageBox.critical(self, '删除失败',
                    f'所有删除操作失败，共 {len(fail_list)} 个:\n' + '\n'.join(fail_list[:5]))

    def reset_password(self):
        if len(self.selected_users) == 0:
            return
        if len(self.selected_users) == 1:
            username = list(self.selected_users)[0]
            user = next((u for u in self.all_users if u.get('username') == username), None)
            if user:
                dialog = UserEditDialog(self.ad_service, user, reset_password=True)
                if dialog.exec_():
                    QMessageBox.information(self, '成功', f'用户 "{username}" 密码重置成功！')
        else:
            dialog = UserEditDialog(self.ad_service, None, reset_password=True)
            if dialog.exec_():
                password = dialog.password_input.text()
                success = 0
                fail_list = []
                for uname in list(self.selected_users):
                    usr = next((u for u in self.all_users if u.get('username') == uname), None)
                    user_dn = usr.get('dn') if usr else None
                    try:
                        self.ad_service.reset_password(uname, password, user_dn)
                        success += 1
                    except Exception as ex:
                        fail_list.append(f'{uname}: {ex}')
                if success > 0 and not fail_list:
                    QMessageBox.information(self, '成功', f'成功重置 {success} 个用户密码！')
                elif success > 0 and fail_list:
                    QMessageBox.warning(self, '部分成功',
                        f'成功重置 {success} 个用户密码\n失败 {len(fail_list)} 个:\n' + '\n'.join(fail_list[:5]))
                else:
                    QMessageBox.critical(self, '操作失败',
                        f'所有密码重置操作失败，共 {len(fail_list)} 个:\n' + '\n'.join(fail_list[:5]))

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '导入 CSV', '', 'CSV Files (*.csv)')
        if file_path:
            try:
                users = self.export_service.import_from_csv(file_path)
                if not users:
                    QMessageBox.warning(self, '提示', 'CSV 文件中没有有效数据')
                    return

                success = 0
                fail_list = []
                for user in users:
                    try:
                        self.ad_service.create_user(user, self.current_ou)
                        success += 1
                    except Exception as ex:
                        fail_list.append(f'{user.get("username")}: {ex}')

                self.load_users()
                if success > 0 and not fail_list:
                    QMessageBox.information(self, '成功', f'导入完成，成功 {success} 个')
                elif success > 0 and fail_list:
                    QMessageBox.warning(self, '部分成功',
                        f'成功导入 {success} 个用户\n失败 {len(fail_list)} 个:\n' + '\n'.join(fail_list[:5]))
                else:
                    QMessageBox.critical(self, '导入失败',
                        f'所有导入操作失败，共 {len(fail_list)} 个:\n' + '\n'.join(fail_list[:5]))
            except Exception as ex:
                QMessageBox.critical(self, '错误', f'导入失败: {ex}')

    def export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, '导出 CSV', 'users.csv', 'CSV Files (*.csv)')
        if file_path:
            try:
                self.export_service.export_to_csv(self.all_users, file_path)
                QMessageBox.information(self, '成功', f'已导出 {len(self.all_users)} 个用户')
            except Exception as ex:
                QMessageBox.critical(self, '错误', f'导出失败: {ex}')

    def open_settings(self):
        dialog = SettingsDialog(self.settings)
        if dialog.exec_():
            self.page_size = self.settings.get('page_size', 25)
            self.render_page()

    def closeEvent(self, event):
        self.settings.set('window_width', self.width())
        self.settings.set('window_height', self.height())
        self.settings.save()
        self.ad_service.disconnect()
        event.accept()