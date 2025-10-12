import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import cv2


def adaptive_contrast_enhancement(image_np, k1=0.5, k2=0.5, window_size=11):
    """
    Implements ACE:
    E(r,c) = k1 * [m_I / σ_l(r,c)] * [I(r,c) - m_l(r,c) + k2 * m_l(r,c)]
    """
    I = image_np.astype(np.float32) / 255.0
    m_I = np.mean(I)

    kernel = np.ones((window_size, window_size), np.float32) / (window_size**2)
    m_l = cv2.filter2D(I, -1, kernel)
    local_sq_mean = cv2.filter2D(I**2, -1, kernel)
    sigma_l = np.sqrt(np.maximum(local_sq_mean - m_l**2, 1e-6))

    
    E = k1 * (m_I / sigma_l) * (I - m_l + k2 * m_l)

    
    E = np.clip(E, 0, 1)
    return (E * 255).astype(np.uint8)


class ACE_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Adaptive Contrast Enhancement (ACE)")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")

        self.image = None
        self.result = None
        self.original_photo = None
        self.result_photo = None

        
        self.k1_var = tk.DoubleVar(value=0.5)
        self.k2_var = tk.DoubleVar(value=0.5)
        self.window_var = tk.IntVar(value=9)

        
        self.build_ui()

    def build_ui(self):
        
        param_frame = tk.LabelFrame(self.root, text="ACE Parameters", padx=10, pady=10, bg="#f0f0f0")
        param_frame.pack(pady=10)

        tk.Label(param_frame, text="k1 (Local Gain):", bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        tk.Scale(param_frame, from_=0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, length=200,
                 variable=self.k1_var).grid(row=0, column=1)

        tk.Label(param_frame, text="k2 (Local Mean Factor):", bg="#f0f0f0").grid(row=1, column=0, sticky="w")
        tk.Scale(param_frame, from_=0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, length=200,
                 variable=self.k2_var).grid(row=1, column=1)

        tk.Label(param_frame, text="Window Size (odd):", bg="#f0f0f0").grid(row=2, column=0, sticky="w")
        tk.Scale(param_frame, from_=1, to=21, resolution=2, orient=tk.HORIZONTAL, length=200,
                 variable=self.window_var).grid(row=2, column=1)

        
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Load Image", command=self.load_image, width=15, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Apply ACE", command=self.apply_ace, width=15, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Save Result", command=self.save_result, width=15, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=10)

        
        img_frame = tk.Frame(self.root, bg="#f0f0f0")
        img_frame.pack(pady=10)

        tk.Label(img_frame, text="Original Image", bg="#f0f0f0", font=("Arial", 12, "bold")).grid(row=0, column=0)
        tk.Label(img_frame, text="Enhanced Image (ACE)", bg="#f0f0f0", font=("Arial", 12, "bold")).grid(row=0, column=1)

        self.original_label = tk.Label(img_frame, bg="gray")
        self.original_label.grid(row=1, column=0, padx=20, pady=10)
        self.result_label = tk.Label(img_frame, bg="gray")
        self.result_label.grid(row=1, column=1, padx=20, pady=10)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.bmp")])
        if path:
            img = Image.open(path).convert('L')
            self.image = np.array(img)
            self.display_image(img, self.original_label, is_result=False)

    def display_image(self, img_pil, label, is_result):
        
        w, h = img_pil.size
        max_size = 500
        if w > max_size or h > max_size:
            scale = min(max_size / w, max_size / h)
            img_pil = img_pil.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(img_pil)
        label.config(image=photo)
        label.image = photo  

        if is_result:
            self.result_photo = photo
        else:
            self.original_photo = photo

    def apply_ace(self):
        if self.image is None:
            return

        k1 = self.k1_var.get()
        k2 = self.k2_var.get()
        window_size = self.window_var.get()
        if window_size % 2 == 0:
            window_size += 1  

        enhanced = adaptive_contrast_enhancement(self.image, k1, k2, window_size)
        self.result = enhanced
        result_pil = Image.fromarray(enhanced)
        self.display_image(result_pil, self.result_label, is_result=True)

    def save_result(self):
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG Image", "*.png"), ("JPEG", "*.jpg")])
        if path:
            Image.fromarray(self.result).save(path)


if __name__ == "__main__":
    root = tk.Tk()
    app = ACE_GUI(root)
    root.mainloop()
