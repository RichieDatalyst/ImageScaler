import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np

def histogram_equalization(channel):

    hist, bins = np.histogram(channel.flatten(), 256, [0, 256])
    cdf = hist.cumsum()
    cdf_normalized = cdf * 255 / cdf[-1]  
    equalized = np.interp(channel.flatten(), bins[:-1], cdf_normalized)
    return equalized.reshape(channel.shape).astype(np.uint8)

def histogram_stretch(channel):
    min_val = np.min(channel)
    max_val = np.max(channel)
    if max_val == min_val:
        return channel.copy()
    stretched = (channel - min_val) * (255.0 / (max_val - min_val))
    return np.clip(stretched, 0, 255).astype(np.uint8)


def color_contrast_enhancement(image_np):
    hls = cv2.cvtColor(image_np, cv2.COLOR_RGB2HLS)
    h, l, s = cv2.split(hls)

    # Enhance S (Histogram Equalization)
    s_eq = histogram_equalization(s)

    # Enhance L (Histogram Stretching)
    l_stretched = histogram_stretch(l)

    # Merge channels back
    hls_enhanced = cv2.merge([h, l_stretched, s_eq])

    
    enhanced_rgb = cv2.cvtColor(hls_enhanced, cv2.COLOR_HLS2RGB)
    return enhanced_rgb

class ColorContrastApp:
    def __init__(self, master):
        self.master = master
        master.title("Color Contrast Enhancement (HSL Based)")

        self.original_image = None
        self.enhanced_image = None
        self.original_photo = None
        self.enhanced_photo = None

        
        button_frame = tk.Frame(master)
        button_frame.pack(pady=10)

        self.load_button = tk.Button(button_frame, text="Load Image", command=self.load_image)
        self.load_button.pack(side=tk.LEFT, padx=10)

        self.enhance_button = tk.Button(button_frame, text="Enhance Image", command=self.enhance_image, state=tk.DISABLED)
        self.enhance_button.pack(side=tk.LEFT, padx=10)

        
        self.image_frame = tk.Frame(master)
        self.image_frame.pack(pady=10)

        tk.Label(self.image_frame, text="Original Image").grid(row=0, column=0, padx=20)
        tk.Label(self.image_frame, text="Enhanced Image").grid(row=0, column=1, padx=20)

        self.original_label = tk.Label(self.image_frame, text="No Image Loaded", bg="gray")
        self.original_label.grid(row=1, column=0, padx=10, pady=5)

        self.enhanced_label = tk.Label(self.image_frame, text="No Image", bg="gray")
        self.enhanced_label.grid(row=1, column=1, padx=10, pady=5)



    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if not path:
            return

        try:
            img = Image.open(path).convert("RGB")
            self.original_image = np.array(img)
            display_img = self.resize_image_for_display(img)
            self.original_photo = ImageTk.PhotoImage(display_img)
            self.original_label.config(image=self.original_photo, text="")
            self.original_label.image = self.original_photo
            self.enhanced_label.config(image='', text="Ready to Enhance")
            self.enhance_button.config(state=tk.NORMAL)
        except Exception as e:
            self.original_label.config(text=f"Error loading image: {e}")

    def resize_image_for_display(self, img, max_width=500, max_height=500):
    
        w, h = img.size
        ratio = min(max_width / w, max_height / h)
        new_size = (int(w * ratio), int(h * ratio))
        return img.resize(new_size, Image.Resampling.LANCZOS)


    def enhance_image(self):
        if self.original_image is None:
            return

        try:
            enhanced = color_contrast_enhancement(self.original_image)
            self.enhanced_image = enhanced

            enhanced_pil = Image.fromarray(enhanced)
            display_img = self.resize_image_for_display(enhanced_pil)
            self.enhanced_photo = ImageTk.PhotoImage(display_img)
            self.enhanced_label.config(image=self.enhanced_photo, text="")
            self.enhanced_label.image = self.enhanced_photo

        except Exception as e:
            self.enhanced_label.config(text=f"Processing Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorContrastApp(root)
    root.mainloop()
