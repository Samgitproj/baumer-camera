import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import json
import cv2

class PointSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Point Selector")

        self.img = None
        self.tkimg = None
        self.points = []  # list of (name, x, y)

        # UI
        frm = tk.Frame(self)
        frm.pack(fill="x", pady=5)
        tk.Button(frm, text="Load Image", command=self.load_image).pack(side="left", padx=5)
        tk.Button(frm, text="Save Points", command=self.save_points).pack(side="left", padx=5)

        self.canvas = tk.Canvas(self, bg="black")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        right = tk.Frame(self)
        right.pack(side="right", fill="y", padx=5)
        tk.Label(right, text="Points:").pack()
        self.listbox = tk.Listbox(right, width=25)
        self.listbox.pack(fill="y", expand=True)

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images","*.png;*.jpg;*.bmp;*.tif;*.tiff")])
        if not path:
            return
        gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            messagebox.showerror("Error","Kon afbeelding niet laden.")
            return
        # convert to RGB for display
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        self.img = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.canvas.config(width=gray.shape[1], height=gray.shape[0])
        self.canvas.delete("all")
        self.canvas.create_image(0,0,anchor="nw",image=self.img)
        self.points.clear()
        self.listbox.delete(0, tk.END)

    def on_click(self, event):
        if not self.img:
            return
        x, y = event.x, event.y
        name = simpledialog.askstring("Point name", f"Naam voor punt @ ({x},{y}):")
        if not name:
            return
        # draw marker
        r = 4
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="yellow", outline="black")
        self.points.append({"name": name, "x": x, "y": y})
        self.listbox.insert(tk.END, f"{name}: ({x},{y})")

    def save_points(self):
        if not self.points:
            messagebox.showinfo("Info","Geen punten om op te slaan.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON","*.json")])
        if not path:
            return
        with open(path, "w") as f:
            json.dump(self.points, f, indent=2)
        messagebox.showinfo("Saved", f"Punten opgeslagen in:\n{path}")

if __name__ == "__main__":
    app = PointSelector()
    app.mainloop()
