import sys, os
# Zorg dat modules in project-root gevonden worden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import threading
import time
import datetime
import cv2
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QSpinBox, QDoubleSpinBox, QFileDialog, QMessageBox, QFrame, QDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage

from cameras.camera_wrapper import CameraWrapper
from config.config_manager import ConfigManager
from gui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cam = CameraWrapper()
        self.cfg = ConfigManager()
        try:
            self.cam.connect()
        except Exception as e:
            QMessageBox.warning(self, "Camera fout", f"Kon camera niet verbinden:\n{e}")

        self.recording = False
        self.save_dir = None
        self.setWindowTitle("Baumer Camera")

        # Centraal widget en layout
        central = QWidget()
        main_layout = QHBoxLayout(central)

        # Linker paneel voor camera instellingen
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        btn_settings = QPushButton("Camera instellingen")
        btn_settings.clicked.connect(self.open_settings_dialog)
        left_layout.addWidget(btn_settings)
        left_layout.addStretch(1)
        main_layout.addWidget(left_panel)

        # Linker marge voor centrering
        main_layout.addStretch(1)

        # Middenframe voor afbeelding (1300x970)
        self.img_frame = QFrame()
        self.img_frame.setFixedSize(1300, 970)
        frame_layout = QVBoxLayout(self.img_frame)
        self.img_label = QLabel("No Image")
        self.img_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.img_label)
        main_layout.addWidget(self.img_frame)

        # Rechter marge (voor centrering)
        main_layout.addStretch(1)

        # Rechter paneel voor alle andere controls
        controls = QWidget()
        ctrl_layout = QVBoxLayout(controls)
        ctrl_layout.setContentsMargins(10, 10, 10, 10)

        # Software trigger
        btn_sw = QPushButton("Trigger")
        btn_sw.clicked.connect(self.on_sw_trigger)
        ctrl_layout.addWidget(btn_sw)

        # Flash-cyclus
        self.btn_flash_start = QPushButton("Start Flash")
        self.btn_flash_start.clicked.connect(self.on_flash_start)
        ctrl_layout.addWidget(self.btn_flash_start)
        self.btn_flash_stop = QPushButton("Stop Flash")
        self.btn_flash_stop.clicked.connect(self.on_flash_stop)
        ctrl_layout.addWidget(self.btn_flash_stop)

        # Recording
        self.btn_rec_start = QPushButton("Start Recording")
        self.btn_rec_start.clicked.connect(self.on_start_recording)
        ctrl_layout.addWidget(self.btn_rec_start)
        self.btn_rec_stop = QPushButton("Stop Recording")
        self.btn_rec_stop.clicked.connect(self.on_stop_recording)
        ctrl_layout.addWidget(self.btn_rec_stop)

        # Exposure & Gain
        ctrl_layout.addWidget(QLabel("Exposure (µs):"))
        self.sb_exposure = QSpinBox()
        self.sb_exposure.setRange(1, 1_000_000)
        self.sb_exposure.valueChanged.connect(
            lambda v: self.cam.set_param("ExposureTime", v)
        )
        ctrl_layout.addWidget(self.sb_exposure)

        ctrl_layout.addWidget(QLabel("Gain:"))
        self.sb_gain = QDoubleSpinBox()
        self.sb_gain.setRange(0.0, 100.0)
        self.sb_gain.valueChanged.connect(
            lambda v: self.cam.set_param("Gain", v)
        )
        ctrl_layout.addWidget(self.sb_gain)

        ctrl_layout.addStretch(1)
        main_layout.addWidget(controls)

        self.setCentralWidget(central)

        # Timer voor flash-cyclus
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self._on_flash_cycle)

        # Sensor-monitor thread
        self._monitor_sensor = True
        t = threading.Thread(target=self._sensor_monitor, daemon=True)
        t.start()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.cfg)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.selected_settings()
            for param, val in settings.items():
                self.cam.set_param(param, val)

    def on_sw_trigger(self):
        try:
            self.cam.fire_software_trigger()
            frame = self.cam.grab_image()
            if frame is None:
                raise RuntimeError("Geen frame terug na trigger")
            self._show_image(frame)
            if self.recording:
                self._save_image(frame)
        except Exception as e:
            QMessageBox.warning(self, "Trigger Fout", str(e))

    def on_flash_start(self):
        self.flash_timer.start(200)

    def on_flash_stop(self):
        self.flash_timer.stop()

    def _on_flash_cycle(self):
        try:
            self.cam.fire_software_trigger()
            frame = self.cam.grab_image()
            if frame is not None:
                self._show_image(frame)
                if self.recording:
                    self._save_image(frame)
        except Exception as e:
            self.flash_timer.stop()
            QMessageBox.warning(self, "Flash Fout", str(e))

    def _show_image(self, arr):
        h, w = arr.shape[:2]
        fmt = QImage.Format_Grayscale8 if arr.ndim == 2 else QImage.Format_RGB888
        img = QImage(arr.data, w, h, arr.strides[0], fmt)
        pix = QPixmap.fromImage(img)
        self.img_label.setPixmap(pix)

    def _sensor_monitor(self):
        last = False
        while self._monitor_sensor:
            try:
                state = bool(self.cam.get_param("Line0"))
            except Exception:
                time.sleep(0.1)
                continue
            if state and not last:
                self.on_sw_trigger()
                time.sleep(0.5)
            last = state
            time.sleep(0.05)

    def on_start_recording(self):
        d = QFileDialog.getExistingDirectory(self, "Selecteer map")
        if d:
            self.save_dir = d
            self.recording = True
            QMessageBox.information(self, "Opname gestart", f"Opslaan in:\n{d}")

    def on_stop_recording(self):
        self.recording = False
        QMessageBox.information(self, "Opname gestopt", "Beëindigd")

    def _save_image(self, arr):
        if not self.save_dir:
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        fn = os.path.join(self.save_dir, f"image_{ts}.png")
        if arr.dtype != 'uint8':
            arr = arr.astype('uint8')
        if arr.ndim == 3 and arr.shape[2] == 1:
            arr = arr[:, :, 0]
        cv2.imwrite(fn, arr)

    def closeEvent(self, event):
        self._monitor_sensor = False
        try:
            self.cam.disconnect()
        except Exception:
            pass
        super().closeEvent(event)
