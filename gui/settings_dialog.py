import os
import json
from PyQt5.QtWidgets import (
    QDialog, QComboBox, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QInputDialog, QDialogButtonBox
)
from gui.plugins.camerafeatures import CameraFeaturesWidget
from config.config_manager import ConfigManager

class SettingsDialog(QDialog):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("Camera Configuraties")
        # Stel de afmetingen in volgens specificatie
        self.resize(1000, 900)

        # Default-config pad bepalen
        base_dir = os.path.normpath(
            r"C:\OneDrive\Vioprint\OneDrive - Vioprint\Sam\AI camera\baumer project\baumer_project\resources\BaseCameraConfig"
        )
        self.default_path = os.path.join(base_dir, "default_config.json")

        # Configuration selector
        self.combo = QComboBox()
        # Profielen uit JSON-map
        profiles = [f[:-5] for f in os.listdir(base_dir) if f.endswith('.json')]
        self.combo.addItems(profiles)

        # Buttons
        btn_new = QPushButton("Nieuw")
        btn_delete = QPushButton("Verwijder")
        btn_edit = QPushButton("Bewerk")
        btn_ok = QPushButton("OK")

        # Layouts
        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Configuratie:"))
        row1.addWidget(self.combo)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(btn_new)
        row2.addWidget(btn_delete)
        row2.addWidget(btn_edit)
        row2.addStretch()
        row2.addWidget(btn_ok)
        layout.addLayout(row2)

        # Connecties
        btn_ok.clicked.connect(self.accept)
        btn_delete.clicked.connect(self.on_delete)
        btn_new.clicked.connect(self.on_new)
        btn_edit.clicked.connect(self.on_edit)

    def on_delete(self):
        name = self.selected_name()
        if name:
            path = os.path.join(os.path.dirname(self.default_path), f"{name}.json")
            if os.path.exists(path):
                os.remove(path)
            self._refresh_list()

    def on_new(self):
        name, ok = QInputDialog.getText(self, "Nieuw Configuratie", "Naam configuratie:")
        if not ok or not name:
            return
        # Laad default instellingen
        with open(self.default_path, 'r') as f:
            default_settings = json.load(f)
        # Open feature editor
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Bewerk: {name}")
        dialog.resize(1000, 900)
        dlg_layout = QVBoxLayout(dialog)
        feat_w = CameraFeaturesWidget(None, default_settings)
        dlg_layout.addWidget(feat_w)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlg_layout.addWidget(buttons)
        if dialog.exec_() == QDialog.Accepted:
            settings = feat_w.get_settings()
            out_path = os.path.join(os.path.dirname(self.default_path), f"{name}.json")
            with open(out_path, 'w') as f:
                json.dump(settings, f, indent=2)
            self._refresh_list()
            self.combo.setCurrentText(name)

    def on_edit(self):
        name = self.selected_name()
        if not name:
            return
        path = os.path.join(os.path.dirname(self.default_path), f"{name}.json")
        with open(path, 'r') as f:
            settings = json.load(f)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Bewerk: {name}")
        dialog.resize(1000, 900)
        dlg_layout = QVBoxLayout(dialog)
        feat_w = CameraFeaturesWidget(None, settings)
        dlg_layout.addWidget(feat_w)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlg_layout.addWidget(buttons)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = feat_w.get_settings()
            with open(path, 'w') as f:
                json.dump(new_settings, f, indent=2)
            self._refresh_list()
            self.combo.setCurrentText(name)

    def _refresh_list(self):
        base = os.path.dirname(self.default_path)
        profiles = [f[:-5] for f in os.listdir(base) if f.endswith('.json')]
        self.combo.clear()
        self.combo.addItems(profiles)

    def selected_name(self) -> str:
        return self.combo.currentText()

    def selected_settings(self) -> dict:
        name = self.selected_name()
        path = os.path.join(os.path.dirname(self.default_path), f"{name}.json")
        with open(path, 'r') as f:
            return json.load(f)
