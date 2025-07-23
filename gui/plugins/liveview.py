from PyQt5.QtWidgets import (
    QAction, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from cameras.camera_wrapper import CameraWrapper
import threading
import time

class LiveViewWidget(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.cam = CameraWrapper()
        self.settings = settings or {}
        self.live_on = False
        
        # Monitor flag for sensor thread
        self._monitor_sensor = False

        # Image display
        self.lbl = QLabel("No Image")
        self.lbl.setAlignment(Qt.AlignCenter)

        # Controls
        self.btn_connect = QPushButton("Connect")
        self.btn_snap    = QPushButton("Trigger Snap")
        self.btn_live    = QPushButton("Start Live")
        self.chk_flash   = QCheckBox("Enable Flash")
        self.spin_exp    = QSpinBox()
        self.spin_exp.setPrefix("Exposure: ")
        self.spin_exp.setRange(1, 100000)
        self.spin_gain   = QSpinBox()
        self.spin_gain.setPrefix("Gain: ")
        self.spin_gain.setRange(0, 100)

        # Init UI from config settings
        if "ExposureTime" in self.settings:
            self.spin_exp.setValue(int(self.settings["ExposureTime"]))
        if "Gain" in self.settings:
            self.spin_gain.setValue(int(self.settings["Gain"]))
        if "FlashEnable" in self.settings:
            self.chk_flash.setChecked(bool(self.settings["FlashEnable"]))

        # Layout setup
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.btn_connect)
        controls_layout.addWidget(self.btn_snap)
        controls_layout.addWidget(self.btn_live)
        controls_layout.addWidget(self.chk_flash)
        controls_layout.addWidget(self.spin_exp)
        controls_layout.addWidget(self.spin_gain)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.lbl)
        main_layout.addLayout(controls_layout)

        # Connections
        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_snap.clicked.connect(self.on_snap)
        self.btn_live.clicked.connect(self.on_live)

        # Start sensor-monitor thread
        self._monitor_sensor = True
        sensor_thread = threading.Thread(target=self._sensor_monitor, daemon=True)
        sensor_thread.start()

    def on_connect(self):
        self.cam.connect()
        try:
            # Initialize controls from camera
            self.spin_exp.setValue(int(self.cam.get_param("ExposureTime") or 0))
            self.spin_gain.setValue(int(self.cam.get_param("Gain") or 0))
            self.chk_flash.setChecked(bool(self.cam.get_param("FlashEnable") or False))
        except Exception:
            pass

    def on_snap(self):
        # Ensure connection
        if not self.cam.cam:
            self.cam.connect()
        # Apply full config (incl. flash)
        self.apply_settings()
        # Grab and display image
        img = self.cam.grab_image()
        self.show_image(img)
        # Disconnect after snap
        self.cam.disconnect()

    def on_live(self):
        if not self.live_on:
            self.on_connect()
            self.apply_settings()
            self.cam.start_continuous(self.show_image)
            self.btn_live.setText("Stop Live")
            self.live_on = True
        else:
            self.cam.stop_continuous()
            self.btn_live.setText("Start Live")
            self.live_on = False

    def apply_settings(self):
        """Push every parameter from the loaded configuration to the camera."""
        for name, value in self.settings.items():
            self.cam.set_param(name, value)

    def show_image(self, arr):
        # Convert NumPy array to QPixmap and display
        h, w = arr.shape[:2]
        fmt = QImage.Format_Grayscale8 if arr.ndim == 2 or (arr.ndim == 3 and arr.shape[2] == 1) else QImage.Format_RGB888
        img = QImage(arr.data, w, h, arr.strides[0], fmt)
        pix = QPixmap.fromImage(img)
        self.lbl.setPixmap(pix)

    def _sensor_monitor(self):
        """Monitor Line0 en trigger automatisch on_snap() bij hoog signaal."""
        while self._monitor_sensor:
            try:
                state = self.cam.get_param("Line0")
                if state:
                    self.on_snap()
                    # Debounce
                    time.sleep(1.0)
            except Exception:
                pass
            time.sleep(0.05)

    def closeEvent(self, event):
        # Stop sensor monitor and live streaming
        self._monitor_sensor = False
        if self.live_on:
            self.cam.stop_continuous()
        super().closeEvent(event)


def register_plugin(app):
    action = QAction("Live View", app)
    app.menuModules.addAction(action)
    action.triggered.connect(lambda:
        app.show_plugin_widget(LiveViewWidget(app.settings))
    )
