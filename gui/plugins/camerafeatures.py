from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, QPushButton
)
from PyQt5.QtCore import Qt
import os
import json

# Constants to clamp integer ranges to 32-bit signed limits
INT_MIN = -2147483648
INT_MAX = 2147483647

class CameraFeaturesWidget(QTreeWidget):
    """
    Widget to display and edit camera features based on a JSON schema.
    Schema is loaded from resources/BaseCameraConfig/default_config.json.
    Initial values can be provided via `settings` dict.
    """
    def __init__(self, xml_path_unused=None, settings=None):
        super().__init__()
        self.setColumnCount(3)
        self.setHeaderLabels(["Parameter", "Type", "Value"])
        self.settings = settings or {}

        # Load JSON schema
        schema_path = os.path.normpath(
            os.path.join(
                os.path.dirname(__file__), '..', '..',
                'resources', 'BaseCameraConfig', 'default_config.json'
            )
        )
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        self.build_tree(schema)
        self.resizeColumnToContents(0)
        self.setColumnWidth(2, 150)

    def build_tree(self, schema):
        """Build the tree from the JSON schema dict."""
        for cat in schema.get('categories', []):
            cat_name = cat.get('name', '')
            parent = QTreeWidgetItem(self, [cat_name, '', ''])
            parent.setFlags(parent.flags() & ~Qt.ItemIsEditable)

            for feat in cat.get('features', []):
                name = feat.get('name', '')
                ftype = feat.get('type', 'String')
                default_val = feat.get('default')
                child = QTreeWidgetItem(parent, [name, ftype, ''])
                child.setFlags(child.flags() & ~Qt.ItemIsEditable)

                init_val = self.settings.get(name, default_val)

                # Enumeration
                if ftype == 'Enumeration':
                    entries = feat.get('entries', [])
                    combo = QComboBox()
                    combo.addItems(entries)
                    if init_val in entries:
                        combo.setCurrentText(init_val)
                    combo.currentTextChanged.connect(
                        lambda val, n=name: self.settings.__setitem__(n, val)
                    )
                    self.setItemWidget(child, 2, combo)

                # Integer with clamped range
                elif ftype == 'Integer':
                    mn = int(feat.get('min', 0))
                    mx = int(feat.get('max', 0))
                    # Clamp to 32-bit signed int limits
                    mn = max(mn, INT_MIN)
                    mx = min(mx, INT_MAX)
                    inc = int(feat.get('inc', 1))
                    spin = QSpinBox()
                    spin.setRange(mn, mx)
                    spin.setSingleStep(inc)
                    try:
                        spin.setValue(int(init_val) if init_val is not None else mn)
                    except OverflowError:
                        spin.setValue(mn)
                    spin.valueChanged.connect(
                        lambda v, n=name: self.settings.__setitem__(n, v)
                    )
                    self.setItemWidget(child, 2, spin)

                # Float
                elif ftype == 'Float':
                    mn = float(feat.get('min', 0.0))
                    mx = float(feat.get('max', 0.0))
                    inc = float(feat.get('inc', 1.0))
                    dspin = QDoubleSpinBox()
                    dspin.setRange(mn, mx)
                    dspin.setSingleStep(inc)
                    dspin.setValue(float(init_val) if init_val is not None else mn)
                    dspin.valueChanged.connect(
                        lambda v, n=name: self.settings.__setitem__(n, v)
                    )
                    self.setItemWidget(child, 2, dspin)

                # Boolean
                elif ftype == 'Boolean':
                    cb = QCheckBox()
                    cb.setChecked(bool(init_val))
                    cb.stateChanged.connect(
                        lambda st, n=name: self.settings.__setitem__(n, st == Qt.Checked)
                    )
                    self.setItemWidget(child, 2, cb)

                # Command
                elif ftype == 'Command':
                    btn = QPushButton(f"Execute {name}")
                    btn.clicked.connect(lambda _, n=name: self.settings.__setitem__(n, True))
                    self.setItemWidget(child, 2, btn)

                # Default text
                else:
                    le = QLineEdit(str(init_val) if init_val is not None else '')
                    le.textChanged.connect(
                        lambda txt, n=name: self.settings.__setitem__(n, txt)
                    )
                    self.setItemWidget(child, 2, le)

    def get_settings(self):
        """Return current settings dict after user edits."""
        return self.settings
