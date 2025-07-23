import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2, json, os
import numpy as np

class PointEntry:
    def __init__(self, parent, name):
        self.name = name
        self.var = tk.BooleanVar(value=True)
        self.cb = tk.Checkbutton(parent, text=name, variable=self.var, anchor="w")
        self.cb.pack(fill="x", padx=5, pady=2)
    def is_checked(self): return self.var.get()
    def set_text(self, text): self.cb.config(text=text)

class InspectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Point Inspector with Dynamic ROI")

        self.orig = None
        self.img = None
        self.photo = None
        self.points = {}
        self.adjusted_points = {}
        self.img_h = 0
        self.black_entries = []
        self.white_entries = []
        self.folder = None
        self.files = []
        self.idx = 0
        self.running = False

        self.base_y_line = None
        self.roi_coords = None
        self.current_y_line = None

        left = tk.Frame(self); left.pack(side="left", padx=5, pady=5)
        mid  = tk.Frame(self); mid.pack(side="left", padx=5, pady=5)
        right= tk.Frame(self); right.pack(side="left", padx=5, pady=5, fill="y")

        self.canvas = tk.Canvas(left, bg="black", cursor="cross")
        self.canvas.pack()

        btns = tk.Frame(mid); btns.pack(pady=5)
        tk.Button(btns, text="Load Image",   command=self.load_image).grid(row=0,column=0,sticky="ew", pady=2)
        tk.Button(btns, text="Load Points",  command=self.load_points).grid(row=1,column=0,sticky="ew", pady=2)
        tk.Button(btns, text="Set ROI",      command=self.activate_roi_mode).grid(row=2,column=0,sticky="ew", pady=2)
        tk.Button(btns, text="Inspect",      command=self.inspect).grid(row=3,column=0,sticky="ew", pady=2)
        tk.Button(btns, text="Browse Folder",command=self.browse_folder).grid(row=4,column=0,sticky="ew", pady=(10,2))
        tk.Button(btns, text="Start DB",     command=self.start_db).grid(row=5,column=0,sticky="ew", pady=2)
        tk.Button(btns, text="Stop DB",      command=self.stop_db).grid(row=6,column=0,sticky="ew", pady=2)

        self.message_label = tk.Label(mid, text="Status: Klaar", width=30, height=2, bg="lightgray")
        self.message_label.pack(pady=(20, 0))

        tk.Label(right, text="Black Min/Max").pack()
        self.black_min = tk.Spinbox(right, from_=0, to=255, width=5)
        self.black_min.pack()
        self.black_max = tk.Spinbox(right, from_=0, to=255, width=5)
        self.black_max.pack()
        tk.Label(right, text="White Min/Max").pack(pady=(10,0))
        self.white_min = tk.Spinbox(right, from_=0, to=255, width=5)
        self.white_min.pack()
        self.white_max = tk.Spinbox(right, from_=0, to=255, width=5)
        self.white_max.pack()

        tk.Label(right, text="Black Points").pack(pady=(10,0))
        self.frm_black = tk.Frame(right, bd=1, relief="sunken")
        self.frm_black.pack(fill="both", expand=True)
        tk.Label(right, text="White Points").pack(pady=(10,0))
        self.frm_white = tk.Frame(right, bd=1, relief="sunken")
        self.frm_white.pack(fill="both", expand=True)

        self.roi_mode = False
        self.roi_start = None
        self.roi_rect = None
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff")])
        if not path: return
        g = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if g is None:
            messagebox.showerror("Error", "Could not load image.")
            return
        self.orig = g.copy()
        self.img = self._apply_filter(g.copy())
        self.img_h = g.shape[0]
        self._show(self.img)
        self.points.clear()
        for e in self.black_entries: e.cb.destroy()
        for e in self.white_entries: e.cb.destroy()
        self.black_entries.clear()
        self.white_entries.clear()
        self.message_label.config(text="Status: Afbeelding geladen", bg="lightgray")

    def _apply_filter(self, img):
        img = img.astype(np.float32)
        rows, cols = img.shape
        mask = np.ones_like(img, dtype=np.float32)
        y = np.linspace(0, 1, rows)
        mask *= 1 - 0.6 * (y ** 4)[:, None]
        img *= mask
        img_uint8 = np.clip(img, 0, 255).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img_contrast = clahe.apply(img_uint8)
        blur = cv2.GaussianBlur(img_contrast, (0, 0), sigmaX=2)
        return cv2.addWeighted(img_contrast, 1.5, blur, -0.5, 0)

    def activate_roi_mode(self):
        self.roi_mode = True

    def on_mouse_down(self, event):
        if not self.roi_mode: return
        self.roi_start = (event.x, event.y)
        if self.roi_rect:
            self.canvas.delete(self.roi_rect)
        self.roi_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red")

    def on_mouse_drag(self, event):
        if self.roi_rect and self.roi_mode:
            self.canvas.coords(self.roi_rect, self.roi_start[0], self.roi_start[1], event.x, event.y)

    def on_mouse_up(self, event):
        if not self.roi_mode: return
        x1, y1 = self.roi_start
        x2, y2 = event.x, event.y
        x1, x2 = sorted([int(x1), int(x2)])
        y1, y2 = sorted([int(y1), int(y2)])
        self.roi_coords = (x1, y1, x2, y2)
        roi = self.img[y1:y2, x1:x2]
        row_means = np.mean(roi, axis=1)
        self.base_y_line = y1 + int(np.argmin(row_means))
        self.current_y_line = self.base_y_line
        self.roi_mode = False
        self._show(self.img)
        self._redraw_all()
        self.canvas.create_line(x1, self.base_y_line, x2, self.base_y_line, fill="cyan", width=2)
        self.message_label.config(text="ROI en referentielijn ingesteld", bg="lightgray")

    def load_points(self):
        if self.img is None:
            self.message_label.config(text="Laad eerst een afbeelding", bg="red")
            return
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        with open(path, 'r') as f:
            pts = json.load(f)
        self.points = {k: (x, self.img_h - y) for k, (x, y) in pts.items()}
        self.adjusted_points = self.points.copy()
        for name, (x, y0) in self.points.items():
            if name.startswith('W'):
                pe = PointEntry(self.frm_black, name)
                self.black_entries.append(pe)
            else:
                pe = PointEntry(self.frm_white, name)
                self.white_entries.append(pe)
        self._redraw_all()
        self.message_label.config(text="Inspectiepunten geladen", bg="lightgray")

    def inspect(self):
        if self.img is None or not self.points or self.base_y_line is None:
            self.message_label.config(text="Load image, points en ROI", bg="red")
            return
        bmin, bmax = int(self.black_min.get()), int(self.black_max.get())
        wmin, wmax = int(self.white_min.get()), int(self.white_max.get())
        all_ok = True
        self._show(self.img)

        x1, y1, x2, y2 = self.roi_coords
        roi = self.img[y1:y2, x1:x2]
        row_means = np.mean(roi, axis=1)
        self.current_y_line = y1 + int(np.argmin(row_means))
        delta_y = self.current_y_line - self.base_y_line
        self.canvas.create_line(x1, self.current_y_line, x2, self.current_y_line, fill="cyan", width=2)

        self.adjusted_points = {name: (x, y + delta_y) for name, (x, y) in self.points.items()}
        for name, (x, y) in self.adjusted_points.items():
            r = 5
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill='yellow')
            self.canvas.create_text(x + r + 2, y, text=name, anchor='w', fill='white')

        for pe in self.black_entries:
            if not pe.is_checked(): continue
            x, y = self.adjusted_points[pe.name]
            v = int(self.img[y, x]); ok = (bmin <= v <= bmax)
            pe.set_text(f"{pe.name}: {v} {'✓' if ok else '✗'}")
            all_ok &= ok
        for pe in self.white_entries:
            if not pe.is_checked(): continue
            x, y = self.adjusted_points[pe.name]
            v = int(self.img[y, x]); ok = (wmin <= v <= wmax)
            pe.set_text(f"{pe.name}: {v} {'✓' if ok else '✗'}")
            all_ok &= ok

        color = 'green' if all_ok else 'red'
        w, h = self.img.shape[1], self.img.shape[0]
        self.canvas.create_rectangle(2, 2, w - 2, h - 2, outline=color, width=4)
        self.message_label.config(text="Inspectie geslaagd" if all_ok else "Inspectie mislukt", bg=color)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        self.folder = folder
        self.files = [os.path.join(folder,f) for f in os.listdir(folder)
                      if f.lower().endswith(('png','jpg','jpeg','bmp','tif','tiff'))]
        self.idx = 0

    def start_db(self):
        if not self.files:
            self.message_label.config(text="Geen folder geladen", bg="red")
            return
        self.running = True
        self._run_loop()

    def stop_db(self):
        self.running = False
        self.message_label.config(text="Loop gestopt", bg="lightgray")

    def _run_loop(self):
        if not self.running or self.idx >= len(self.files):
            self.running = False
            return
        path = self.files[self.idx]; self.idx += 1
        g = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        self.orig = g.copy(); self.img = self._apply_filter(g.copy()); self.img_h = g.shape[0]
        self._show(self.img)
        self.inspect()
        self.after(1000, self._run_loop)

    def _redraw_all(self):
        for name, (x, y) in self.points.items():
            r = 5
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill='yellow')
            self.canvas.create_text(x + r + 2, y, text=name, anchor='w', fill='white')

    def _show(self, gray):
        h, w = gray.shape
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.photo = img
        self.canvas.config(width=w, height=h)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)

if __name__=='__main__':
    app = InspectApp()
    app.mainloop()
