from PyQt6.QtCore import QObject, pyqtSignal

from coip import multicast


class ScriptWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, gui):
        self.gui = gui
        super().__init__()

    def run(self):
        self.result_message = multicast.multicast([ip.text() for ip in self.gui.IP_list.selectedItems()],
                                                  self.gui.message.text(), self.gui.clock_timeout.value(),
                                                  self.gui.actionLog_Runs.isChecked())
        self.finished.emit()

    def get_result_message(self):
        return self.result_message
