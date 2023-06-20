import ipaddress
import sys

from PyQt6.QtWidgets import *

import CoIP
from MainWindow import Ui_MainWindow
from Dialogs import SimpleTextDialog, YesNoDialog


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # Add IP
        self.add_IP_button.clicked.connect(self.add_IP)
        self.IP_to_add.returnPressed.connect(self.add_IP)

        # Delete IP
        self.delete_IPs_button.clicked.connect(self.delete_ips)

        # Save Script
        self.save_script_button.clicked.connect(self.save_script)

        # Load Script
        self.load_script_button.clicked.connect(self.load_script)

        # Run Script
        self.run_script_button.clicked.connect(self.run_script)

        # Delete Script
        self.delete_script_button.clicked.connect(self.delete_script)

    # Actions
    def add_IP(self):
        try:
            ipaddress.ip_address(self.IP_to_add.text())
            self.IP_list.addItem(self.IP_to_add.text())
            self.IP_to_add.clear()
        except ValueError:
            SimpleTextDialog("Invalid Address!", f"{self.IP_to_add.text()} is not a valid IP address.").exec()

    def delete_ips(self):
        if self.IP_list.selectedItems() and YesNoDialog(
                "Delete Addresses",
                "Are you sure you want to delete the selected addresses?\nNo script will be able to contact them.") \
                .exec():
            for ip in self.IP_list.selectedItems():
                self.IP_list.takeItem(self.IP_list.row(ip))

    def save_script(self):
        return  # todo

    def load_script(self):
        return  # todo

    def run_script(self):
        failed_ips = CoIP.multicast([ip.text() for ip in self.IP_list.selectedItems()], self.message.text(),
                                    float(self.clock_timeout.cleanText()), self.actionLog_Runs.isChecked())

        message = "Run Successful." if not failed_ips else (
                "The following addresses did not respond:\n" + ('\n'.join(failed_ips)))

        SimpleTextDialog("Run Complete", message).exec()

    def delete_script(self):
        if self.scripts.selectedItems() and YesNoDialog("Delete Script",
                                                        "Are you sure you want to delete the selected script?").exec():
            self.scripts.takeItem(self.IP_list.currentRow())

    # Settings
    def change_script_folder(self):
        return  # todo

    # Autosave
    def closeEvent(self, a0):
        if self.actionAutosave.isChecked():
            pass  # todo

        a0.accept()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
exit(app.exec())
