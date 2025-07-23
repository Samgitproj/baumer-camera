import os
import neoapi
import numpy as np
import threading

class CameraWrapper:
    def __init__(self, gentl_path=r"C:\virt omgeving\AI camera\gentl_producer"):
        self.gentl_path = gentl_path
        self.cam = None
        self.running = False

    def connect(self):
        # Zorg dat de GenTL-producer gevonden wordt
        os.environ['GENICAM_GENTL64_PATH'] = self.gentl_path
        self.cam = neoapi.Cam()
        self.cam.Connect()
        print("Connected to camera via NeoAPI")

    def disconnect(self):
        if self.cam:
            try:
                self.cam.Disconnect()
                print("Disconnected from camera")
            except Exception:
                pass
            finally:
                self.cam = None

    def set_param(self, name, value):
        """Live instellen van een GenICam-feature (bv. ExposureTime, Gain)."""
        try:
            self.cam.SetFeature(name, value)
            print(f"Set {name} to {value}")
        except Exception as e:
            print(f"Error setting {name}: {e}")

    def get_param(self, name):
        """Ophalen van een GenICam-feature (bv. Line0 voor sensorstatus)."""
        try:
            feature = self.cam.GetFeature(name)
            return feature.GetValue()
        except Exception as e:
            print(f"Error getting {name}: {e}")
            return None

    def grab_image(self):
        """
        Neem één enkele opname (poll tot niet-leeg) en return een NumPy-array.
        """
        img = self.cam.GetImage()
        while hasattr(img, 'IsEmpty') and img.IsEmpty():
            try:
                self.cam.ClearImages()
            except Exception:
                pass
            img = self.cam.GetImage()

        try:
            arr = img.GetNPArray()
        except Exception:
            arr = img.GetData()
        return arr

    def fire_software_trigger(self):
        """
        Voer een software-trigger uit via GenICam-feature 'TriggerSoftware'.
        Werkt alleen als de camera op Software-Trigger staat.
        """
        if not self.cam:
            raise RuntimeError("Camera niet verbonden")

        try:
            cmd = self.cam.GetFeature("TriggerSoftware")
            cmd.Execute()
            print("Software-trigger uitgevoerd")
        except neoapi.GenICamException as e:
            raise RuntimeError(f"Software-trigger mislukt (GenICam): {e}")
        except AttributeError:
            raise RuntimeError("Feature 'TriggerSoftware' niet gevonden op deze camera")
        except Exception as e:
            raise RuntimeError(f"Onverwachte fout tijdens SW-trigger: {e}")
