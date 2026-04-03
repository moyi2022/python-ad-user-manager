import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from views.login_dialog import LoginDialog
from views.main_window import MainWindow
from services.log_service import LogService

def main():
    LogService.log('Application started')

    app = QApplication(sys.argv)
    app.setStyle('Windows')

    # Login dialog
    login = LoginDialog()
    if login.exec_() == LoginDialog.Accepted:
        ad_service = login.ad_service
        main_window = MainWindow(ad_service)
        main_window.show()
        sys.exit(app.exec_())
    else:
        LogService.log('Application closed by user')
        sys.exit(0)

if __name__ == '__main__':
    main()
