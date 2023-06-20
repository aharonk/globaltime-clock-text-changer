from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class SimpleTextDialog(QDialog):
    def __init__(self, title, message):
        super().__init__()

        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.StandardButton.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()

        self.layout.addWidget(QLabel(message))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class YesNoDialog(QDialog):
    def __init__(self, title, message):
        super().__init__()

        self.setWindowTitle(title)
        QBtn = QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()

        self.layout.addWidget(QLabel(message))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
