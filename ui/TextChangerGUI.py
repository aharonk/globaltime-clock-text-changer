import ipaddress
import os.path
import sys

from PyQt6.QtCore import Qt, QSettings, QThread
from PyQt6.QtWidgets import *

import directory
from db.db import DBConn
from ui.Dialogs import SimpleTextDialog, YesNoDialog, FloatDialog
from ui.MainWindow import Ui_MainWindow
from ui.ScriptRunner import ScriptWorker


def launch_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # Setup
        self.db = DBConn()
        self.IP_states_on_load = {}
        self.vals_on_load = ()

        self.IP_list.insertItems(0, self.db.select_all_ips())
        self.scripts.insertItems(0, self.db.select_all_scripts())

        self.settings = QSettings(directory.get_path(True) + "/settings.ini", QSettings.Format.IniFormat)
        self.settings.setFallbacksEnabled(False)
        self.actionLog_Runs.setChecked(self.settings.value("log_runs", False, bool))
        self.actionAutosave.setChecked(self.settings.value("autosave", True, bool))
        self.actionRemember_last_script.setChecked(self.settings.value("remember_last_script", True, bool))
        self.default_timeout = self.settings.value("default_timeout", 10.0, float)
        self.clock_timeout.setValue(self.default_timeout)

        # Add IP
        self.add_IP_button.clicked.connect(self.add_IP)
        self.IP_to_add.returnPressed.connect(self.add_IP)

        # Delete IP
        self.delete_IPs_button.clicked.connect(self.delete_IPs)

        # Save Script
        self.save_script_button.clicked.connect(self.save_script)

        # Run Script
        self.run_script_button.clicked.connect(self.threaded_run)

        # Export Script to bat
        self.create_bat_button.clicked.connect(self.create_bat)

        # Delete Script
        self.delete_script_button.clicked.connect(self.delete_script)

        # Select IP
        self.scripts.itemPressed.connect(self.load_or_unload_script)

        # Change Default Timeout
        self.actionSet_default_timeout.triggered.connect(self.set_default_timeout)

    def load_or_unload_script(self, item: QListWidgetItem):
        if item.isSelected():
            self.load_script(item)
        else:
            self.unload_script()

    def get_added_and_removed_IPs(self):
        added_IPs, removed_IPs = [], []
        for row in range(self.IP_list.count()):
            current_item = self.IP_list.item(row)
            if self.IP_states_on_load[current_item.text()]["selected"]:
                if not current_item.isSelected():
                    removed_IPs.append(current_item.text())
                elif current_item.isSelected() and self.IP_states_on_load[current_item.text()]["re-added"]:
                    added_IPs.append(current_item.text())
            elif current_item.isSelected():
                added_IPs.append(current_item.text())
        return added_IPs, removed_IPs

    # Actions
    def add_IP(self):
        try:
            ipaddress.ip_address(self.IP_to_add.text())
            if self.db.insert_ip(self.IP_to_add.text()):
                self.IP_list.addItem(self.IP_to_add.text())
                if self.IP_to_add.text() in self.IP_states_on_load:
                    self.IP_states_on_load.update({self.IP_to_add.text(): {"selected": False, "re-added": True}})
                else:
                    self.IP_states_on_load.update({self.IP_to_add.text(): {"selected": False, "re-added": False}})
                self.IP_to_add.clear()
            else:
                SimpleTextDialog("Duplicate Address!", f"{self.IP_to_add.text()} is already in your list.").exec()
        except ValueError:
            SimpleTextDialog("Invalid Address!", f"{self.IP_to_add.text()} is not a valid IP address.").exec()

    def delete_IPs(self):
        if self.IP_list.selectedItems() and YesNoDialog(
                "Delete Addresses",
                "Are you sure you want to delete the selected addresses?\nNo script will be able to use them.").exec():
            addresses = []
            for ip in self.IP_list.selectedItems():
                addresses.append(ip.text())
                self.IP_list.takeItem(self.IP_list.row(ip))
            self.db.delete_ips(addresses)

    def save_script(self, autosave=False, added_IPs=None, removed_IPs=None):
        name = self.script_name.text()

        if name == "":
            if autosave:
                name = "Autosave"
            else:
                SimpleTextDialog("Missing Name!", f"You need to name your script.").exec()
                return

        same_named_script = self.scripts.findItems(name, Qt.MatchFlag.MatchExactly)
        if (not autosave) and len(same_named_script) > 0:
            if YesNoDialog("Update Script", f'Are you sure you want to update {name}?').exec():
                self.db.update_script(name, self.message.text(), self.clock_timeout.value())
            else:
                return
        else:
            self.db.insert_script(name, self.message.text(), self.clock_timeout.value())
            self.scripts.addItem(name)

        if not (added_IPs or removed_IPs):
            added_IPs, removed_IPs = self.get_added_and_removed_IPs()

        if added_IPs:
            self.IP_states_on_load.update({address: {"selected": True, "re-added": False} for address in added_IPs})
            self.db.insert_IPs_to_script(name, added_IPs)
        if removed_IPs:
            self.IP_states_on_load.update({address: {"selected": False, "re-added": False} for address in removed_IPs})
            self.db.remove_IPs_from_script(name, removed_IPs)

        selected_script = self.scripts.findItems(name, Qt.MatchFlag.MatchExactly)[0]
        if not selected_script.isSelected() and self.scripts.currentItem():
            self.scripts.currentItem().setSelected(False)
            selected_script.setSelected(True)

    def load_script(self, item: QListWidgetItem):
        script = self.db.select_script(item.text())
        self.script_name.setText(script[0])
        self.message.setText(script[1])
        self.clock_timeout.setValue(script[2])

        self.vals_on_load = script[:3]
        self.IP_states_on_load = {}
        for i in range(self.IP_list.count()):
            address = self.IP_list.item(i).text()
            selected = address in script[3]
            self.IP_list.item(i).setSelected(selected)
            self.IP_states_on_load.update({address: {"selected": selected, "re-added": False}})

    def unload_script(self):
        self.script_name.setText("")
        self.message.setText("")
        self.clock_timeout.setValue(self.default_timeout)
        self.IP_states_on_load = {}
        self.vals_on_load = ()

    def threaded_run(self):
        if not self.vals_on_load:
            SimpleTextDialog("Select Script", "You need to select a script to run it.").exec()
            return

        self.thread = QThread()
        self.worker = ScriptWorker(self)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.run_script_button.setEnabled(False)
        self.thread.finished.connect(lambda: self.run_script_button.setEnabled(True))
        self.thread.finished.connect(lambda: SimpleTextDialog("Run Results", self.worker.get_result_message()).exec())

    def create_bat(self):
        if not self.vals_on_load:
            SimpleTextDialog("Select Script", "You need a selected script to create a .bat.").exec()
            return

        dir_path = directory.get_path(False) + f"/batches/"
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
        with open(dir_path + f"{self.script_name.text()}.bat", 'w+') as file:
            file.write(
                f"@echo off\n{directory.get_path(False)}/{'main.exe ' if directory.is_exe() else 'main.py '}")
            if self.actionGenerate_static_batch_file.isChecked():
                file.write(f"-m \"{self.message.text()}\" -t {self.clock_timeout.value()} -a "
                           f"{' '.join([ip.text() for ip in self.IP_list.selectedItems()])}")
            else:
                file.write(f"-s {self.script_name.text()}")
            file.write(f"{'' if self.actionLog_Runs.isChecked() else ' -n'}\npause")
        SimpleTextDialog("Exported Script", "Your .bat was created.").exec()

    def delete_script(self):
        if self.scripts.selectedItems() and YesNoDialog("Delete Script",
                                                        "Are you sure you want to delete the selected script?").exec():
            self.db.delete_script(self.scripts.takeItem(self.scripts.currentRow()).text())

    def set_default_timeout(self):
        dialog = FloatDialog("Default Timeout per Clock", self.default_timeout)
        if dialog.exec():
            self.default_timeout = dialog.get_value()
            self.clock_timeout.setValue(self.default_timeout)

    # Autosave
    def closeEvent(self, a0):
        self.settings.setValue("log_runs", self.actionLog_Runs.isChecked())
        self.settings.setValue("autosave", self.actionAutosave.isChecked())
        self.settings.setValue("remember_last_script", self.actionRemember_last_script.isChecked())
        self.settings.setValue("default_timeout", self.default_timeout)

        # Autosave if the following are all true:
        # - Autosave is checked and the name and message aren't both blank (or the message is blank and the name is
        #   "Autosave")
        # - Name, message, timeout, or included IPs have changed
        if self.actionAutosave.isChecked() and not (
                self.script_name.text() in ("", "Autosave") and self.message.text() == ""):
            new_vals = (self.script_name.text(), self.message.text(), self.clock_timeout.value())
            added_IPs, removed_IPs = self.get_added_and_removed_IPs()

            if self.vals_on_load != new_vals or added_IPs or removed_IPs:
                self.save_script(True, added_IPs, removed_IPs)
        a0.accept()
