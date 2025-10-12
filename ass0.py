import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Spatial Frequency and Color Channel Visualization")
        self.original_image = None
        self.tk_image = None
        self.canvas_width = 800
        self.canvas_height = 600

        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="gray")
        self.canvas.pack(pady=10)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        
        self.open_button = tk.Button(button_frame, text="1. Open Image", command=self.open_image)
        self.open_button.pack(side=tk.LEFT, padx=10)

        
        self.rgb_button = tk.Button(button_frame, text="2. Show RGB Channels", command=self.show_rgb_channels, state=tk.DISABLED)
        self.rgb_button.pack(side=tk.LEFT, padx=10)

        
        self.reduce_button = tk.Button(button_frame, text="3. Reduce Spatial Resolution", command=self.reduce_resolution, state=tk.DISABLED)
        self.reduce_button.pack(side=tk.LEFT, padx=10)

    def open_image(self):
        
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if not file_path:
            return

        try:
            self.original_image = Image.open(file_path)
            self.display_image(self.original_image)
            
            self.rgb_button.config(state=tk.NORMAL)
            self.reduce_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def display_image(self, image_to_display):
        # Scale the image to fit within the canvas while maintaining aspect ratio
        img_width, img_height = image_to_display.size
        ratio = min(self.canvas_width / img_width, self.canvas_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)

        resized_image = image_to_display.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        
        self.canvas.delete("all")
        self.canvas.create_image(self.canvas_width / 2, self.canvas_height / 2, image=self.tk_image, anchor=tk.CENTER)

    def show_rgb_channels(self):

        if not self.original_image:
            messagebox.showwarning("Warning", "Please open an image first.")
            return

        
        bands = self.original_image.split()
        if len(bands) < 3:
            messagebox.showwarning("Warning", "The loaded image does not have RGB channels.")
            return
        
        red_band = bands[0]
        green_band = bands[1]
        blue_band = bands[2]

        blank_band = Image.new('L', self.original_image.size)
        
        red_image = Image.merge("RGB", (red_band, blank_band, blank_band))
        green_image = Image.merge("RGB", (blank_band, green_band, blank_band))
        blue_image = Image.merge("RGB", (blank_band, blank_band, blue_band))

        
        self.display_channel(red_image, "Red Channel")
        self.display_channel(green_image, "Green Channel")
        self.display_channel(blue_image, "Blue Channel")

    def display_channel(self, channel_image, title):
        
        channel_window = tk.Toplevel(self.root)
        channel_window.title(title)
        
        img_width, img_height = channel_image.size
        ratio = min(self.canvas_width / img_width, self.canvas_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        resized_image = channel_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        tk_img = ImageTk.PhotoImage(resized_image)

        channel_canvas = tk.Canvas(channel_window, width=self.canvas_width, height=self.canvas_height, bg="gray")
        channel_canvas.pack()
        channel_canvas.create_image(self.canvas_width / 2, self.canvas_height / 2, image=tk_img, anchor=tk.CENTER)

        channel_canvas.image = tk_img

    def reduce_resolution(self):
        if not self.original_image:
            messagebox.showwarning("Warning", "Please open an image first.")
            return
        
        try:
            scale_percent = simpledialog.askinteger(
                "Reduce Resolution",
                "Enter a reduction percentage:",
                minvalue=1,
                maxvalue=100
            )
            if scale_percent is None:
                return

            reduction_factor = scale_percent / 100.0
            new_width = int(self.original_image.width * reduction_factor)
            new_height = int(self.original_image.height * reduction_factor)

            if new_width <= 0 or new_height <= 0:
                messagebox.showerror("Error", "Invalid reduction percentage.")
                return

            # Downsample the image to a smaller size
            low_res_image = self.original_image.resize((new_width, new_height), Image.Resampling.BOX)
            
            # Upsample back to original size using nearest neighbor
            restored_image = low_res_image.resize(self.original_image.size, Image.Resampling.NEAREST)

            self.display_image(restored_image)

        except (ValueError, TypeError):
            messagebox.showerror("Error", "Invalid input. Please enter a valid number.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()
