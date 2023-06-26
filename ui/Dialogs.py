from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QDoubleSpinBox


def build_dialog(dialog: QDialog, title, btns: QDialogButtonBox.StandardButton, content):
    dialog.setWindowTitle(title)

    icon = QIcon()
    icon.addPixmap(QPixmap("ui\\assets/icon.jpg"), QIcon.Mode.Normal, QIcon.State.Off)
    dialog.setWindowIcon(icon)

    dialog.buttonBox = QDialogButtonBox(btns)
    dialog.buttonBox.accepted.connect(dialog.accept)
    if bin(btns.value).count('1') > 1:
        dialog.buttonBox.rejected.connect(dialog.reject)

    dialog.layout = QVBoxLayout()
    dialog.layout.addWidget(content)
    dialog.layout.addWidget(dialog.buttonBox)
    dialog.setLayout(dialog.layout)


class SimpleTextDialog(QDialog):
    def __init__(self, title, message):
        super().__init__()
        build_dialog(self, title, QDialogButtonBox.StandardButton.Ok, QLabel(message))


class YesNoDialog(QDialog):
    def __init__(self, title, message):
        super().__init__()
        build_dialog(self, title, QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No,
                     QLabel(message))


class FloatDialog(QDialog):
    def __init__(self, title, old_default):
        super().__init__()
        self.value = QDoubleSpinBox()
        self.value.setValue(old_default)
        build_dialog(self, title, QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                     self.value)

    def get_value(self):
        return self.value.value()
