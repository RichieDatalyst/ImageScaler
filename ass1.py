import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def to_uint8(arr):
    a = np.asarray(arr)
    a = np.clip(a, 0, 255)
    return a.astype(np.uint8)

def load_gray(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise IOError("Could not read image.")
    return to_uint8(img)

def pil_from_np_gray(np_img, maxsize=(700,700)):
    pil = Image.fromarray(np_img)
    w,h = pil.size
    mw, mh = maxsize
    if w>mw or h>mh:
        scale = min(mw/w, mh/h)
        pil = pil.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return ImageTk.PhotoImage(pil)

def calc_hist(img):
    hist = cv2.calcHist([img],[0],None,[256],[0,256]).flatten()
    return hist

def plot_hist_on_axes(ax, img, title="Histogram"):
    ax.clear()
    hist = calc_hist(img)
    ax.plot(hist, color='black')
    ax.set_title(title)
    ax.set_xlim(0,255)
    ax.set_xlabel("Intensity")
    ax.set_ylabel("Frequency")

def cdf_from_hist(hist):
    pdf = hist.astype(np.float64) / (np.sum(hist) + 1e-12)
    cdf = np.cumsum(pdf)
    return cdf


def linear_stretch(img, dst_min=0, dst_max=255):
    arr = img.astype(np.float32)
    src_min = float(np.min(arr))
    src_max = float(np.max(arr))
    if src_max == src_min:
        return to_uint8(np.clip(arr, dst_min, dst_max))
    out = (arr - src_min) / (src_max - src_min) * (dst_max - dst_min) + dst_min
    return to_uint8(out)

def linear_map_custom(img, src_min, src_max, dst_min, dst_max):
    arr = img.astype(np.float32)
    if src_max == src_min:
        return to_uint8(np.clip(arr, dst_min, dst_max))
    out = (arr - src_min) / (src_max - src_min) * (dst_max - dst_min) + dst_min
    return to_uint8(out)

def shrink_map(img, dst_min, dst_max):
    return linear_stretch(img, dst_min, dst_max)

def slide(img, offset):
    return to_uint8(img.astype(np.int32) + int(offset))

def piecewise_linear(img, thresh, low_dst=(0,127), high_dst=(128,255)):
    arr = img.astype(np.float32)
    t = float(thresh)
    out = np.zeros_like(arr)
    src_min = float(np.min(arr))
    src_max = float(np.max(arr))
    # Lower segment mapping: [src_min, t] -> low_dst
    lo_src_lo = src_min
    lo_src_hi = min(t, src_max)  
    if lo_src_hi <= lo_src_lo:
        mask_low = arr <= t
        out[mask_low] = low_dst[0]
    else:
        mask_low = arr <= t
        out[mask_low] = (arr[mask_low] - lo_src_lo) / (lo_src_hi - lo_src_lo) * (low_dst[1] - low_dst[0]) + low_dst[0]
    # Upper segment mapping: (t, src_max] -> high_dst
    hi_src_lo = max(t+1, src_min)
    hi_src_hi = src_max
    mask_high = arr > t
    if hi_src_hi <= hi_src_lo:
        out[mask_high] = high_dst[1]
    else:
        out[mask_high] = (arr[mask_high] - hi_src_lo) / (hi_src_hi - hi_src_lo) * (high_dst[1] - high_dst[0]) + high_dst[0]
    return to_uint8(out)

def percentile_hist_stretch(img, low_pct=2.0, high_pct=98.0, out_min=0, out_max=255):
    flat = img.flatten().astype(np.float32)
    lo = np.percentile(flat, low_pct)
    hi = np.percentile(flat, high_pct)
    if hi == lo:
        return to_uint8(img)
    out = (img.astype(np.float32) - lo) / (hi - lo) * (out_max - out_min) + out_min
    return to_uint8(out)

def histogram_equalize(img):
    return cv2.equalizeHist(img)


def histogram_specification_map(src_img, target_img):
    
    hist_src = calc_hist(src_img)
    hist_tgt = calc_hist(target_img)
    cdf_src = cdf_from_hist(hist_src)
    cdf_tgt = cdf_from_hist(hist_tgt)
    mapping = np.zeros(256, dtype=np.uint8)
    # For each intensity level in source, find corresponding level in target
    for r in range(256):
        # Find the smallest s such that cdf_tgt[s] >= cdf_src[r]
        target_indices = np.where(cdf_tgt >= cdf_src[r])[0]
        if target_indices.size > 0:
            s = target_indices[0]
        else:
            s = 255
        mapping[r] = s
    return mapping

def apply_mapping(img, mapping):
    return mapping[img]

class GrayscaleApp:
    def __init__(self, master):
        self.master = master
        master.title("Grayscale Image Tools — Stretch/Shrink/Equalize/Specify")
        master.geometry("1200x760")

        # Notebook (tabs)
        self.nb = ttk.Notebook(master)
        self.nb.pack(fill=tk.BOTH, expand=True)

        
        self.orig_img = None      
        self.current_img = None   
        self.spec_src = None      
        self.spec_tgt = None      
        self.spec_result = None

        
        self.build_tab_stretch()
        self.build_tab_histeq()
        self.build_tab_spec()

    #Stretch / Shrink / Piecewise / Slide
    def build_tab_stretch(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Stretch / Shrink / Piecewise / Slide")

        left = tk.Frame(tab)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        
        bframe = tk.Frame(left)
        bframe.pack(fill=tk.X, pady=4)
        tk.Button(bframe, text="Load Image", command=self.load_image_single).pack(side=tk.LEFT, padx=4)
        tk.Button(bframe, text="Save Result", command=self.save_current_result).pack(side=tk.LEFT, padx=4)
        tk.Button(bframe, text="Reset", command=self.reset_single).pack(side=tk.LEFT, padx=4)

        # Linear Stretch
        lf = tk.LabelFrame(left, text="Linear Stretch (auto src range)", padx=6, pady=6)
        lf.pack(fill=tk.X, pady=4)
        tk.Label(lf, text="Dst min:").grid(row=0, column=0, sticky="w")
        self.ls_dstmin = tk.Entry(lf, width=6); self.ls_dstmin.insert(0,"0"); self.ls_dstmin.grid(row=0,column=1)
        tk.Label(lf, text="Dst max:").grid(row=0, column=2, sticky="w")
        self.ls_dstmax = tk.Entry(lf, width=6); self.ls_dstmax.insert(0,"255"); self.ls_dstmax.grid(row=0,column=3)
        tk.Button(lf, text="Apply Stretch", command=self.apply_linear_stretch).grid(row=0,column=4,padx=6)

        # Shrink
        sf = tk.LabelFrame(left, text="Shrink (map into smaller range)", padx=6, pady=6)
        sf.pack(fill=tk.X, pady=4)
        tk.Label(sf, text="Dst min:").grid(row=0,column=0); self.shr_dstmin = tk.Entry(sf,width=6); self.shr_dstmin.insert(0,"50"); self.shr_dstmin.grid(row=0,column=1)
        tk.Label(sf, text="Dst max:").grid(row=0,column=2); self.shr_dstmax = tk.Entry(sf,width=6); self.shr_dstmax.insert(0,"200"); self.shr_dstmax.grid(row=0,column=3)
        tk.Button(sf, text="Apply Shrink", command=self.apply_shrink).grid(row=0,column=4,padx=6)

        # Slide (offset)
        of = tk.LabelFrame(left, text="Slide / Offset", padx=6, pady=6)
        of.pack(fill=tk.X, pady=4)
        tk.Label(of, text="Offset (e.g. -50 .. +50):").grid(row=0,column=0); self.offset_entry = tk.Entry(of,width=6); self.offset_entry.insert(0,"0"); self.offset_entry.grid(row=0,column=1)
        tk.Button(of, text="Apply Offset", command=self.apply_offset).grid(row=0,column=2,padx=6)

        # Piecewise
        pf = tk.LabelFrame(left, text="Piecewise Linear Mapping", padx=6, pady=6)
        pf.pack(fill=tk.X, pady=4)
        tk.Label(pf, text="Threshold (0-255):").grid(row=0,column=0); self.pw_thresh = tk.Entry(pf,width=6); self.pw_thresh.insert(0,"128"); self.pw_thresh.grid(row=0,column=1)
        tk.Label(pf, text="Low dst (a,b):").grid(row=0,column=2); self.pw_la = tk.Entry(pf,width=4); self.pw_lb = tk.Entry(pf,width=4)
        self.pw_la.insert(0,"0"); self.pw_lb.insert(0,"127"); self.pw_la.grid(row=0,column=3); self.pw_lb.grid(row=0,column=4)
        tk.Label(pf, text="High dst (c,d):").grid(row=1,column=2); self.pw_hc = tk.Entry(pf,width=4); self.pw_hd = tk.Entry(pf,width=4)
        self.pw_hc.insert(0,"128"); self.pw_hd.insert(0,"255"); self.pw_hc.grid(row=1,column=3); self.pw_hd.grid(row=1,column=4)
        tk.Button(pf, text="Apply Piecewise", command=self.apply_piecewise).grid(row=0,column=5,rowspan=2,padx=6)

        # Percentile-based histogram stretch
        hf = tk.LabelFrame(left, text="Percentile Histogram Stretch", padx=6, pady=6)
        hf.pack(fill=tk.X, pady=4)
        tk.Label(hf, text="Low%:").grid(row=0,column=0); self.h_low = tk.Entry(hf,width=6); self.h_low.insert(0,"2"); self.h_low.grid(row=0,column=1)
        tk.Label(hf, text="High%:").grid(row=0,column=2); self.h_high = tk.Entry(hf,width=6); self.h_high.insert(0,"98"); self.h_high.grid(row=0,column=3)
        tk.Button(hf, text="Apply Percentile Stretch", command=self.apply_percentile_stretch).grid(row=0,column=4,padx=6)

    
        vb = tk.Frame(left)
        vb.pack(fill=tk.X, pady=6)
        tk.Button(vb, text="Show Before/After Histograms", command=self.show_before_after_hist_stretch).pack(side=tk.LEFT, padx=4)
        tk.Button(vb, text="Show Current Histogram", command=self.show_current_hist_single).pack(side=tk.LEFT, padx=4)

        preview_frame = tk.LabelFrame(right, text="Preview", padx=6, pady=6)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        top = tk.Frame(preview_frame); top.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.preview_before_label = tk.Label(top, text="Before")
        self.preview_before_label.pack(side=tk.LEFT, padx=6, pady=6)
        self.preview_after_label = tk.Label(top, text="After")
        self.preview_after_label.pack(side=tk.LEFT, padx=6, pady=6)

        self.hist_canvas_container_stretch = tk.Frame(preview_frame)
        self.hist_canvas_container_stretch.pack(fill=tk.BOTH, expand=True)
        self.canvas_stretch = None
        self.toolbar_stretch = None

    #Histogram Equalization 
    def build_tab_histeq(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Histogram Equalization")

        left = tk.Frame(tab)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        bframe = tk.Frame(left); bframe.pack(fill=tk.X, pady=4)
        tk.Button(bframe, text="Load Image", command=self.load_image_single).pack(side=tk.LEFT, padx=4)
        tk.Button(bframe, text="Apply Equalization", command=self.apply_histeq).pack(side=tk.LEFT, padx=4)
        tk.Button(bframe, text="Save Result", command=self.save_current_result).pack(side=tk.LEFT, padx=4)
        tk.Button(bframe, text="Reset", command=self.reset_single).pack(side=tk.LEFT, padx=4)
        tk.Button(bframe, text="Show Before/After Hist", command=self.show_before_after_hist_stretch).pack(side=tk.LEFT, padx=4)

        
        preview_frame = tk.LabelFrame(right, text="Preview & Histogram", padx=6, pady=6)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_before_label_eq = tk.Label(preview_frame, text="Before")
        self.preview_before_label_eq.pack(side=tk.LEFT, padx=6, pady=6)
        self.preview_after_label_eq = tk.Label(preview_frame, text="After")
        self.preview_after_label_eq.pack(side=tk.LEFT, padx=6, pady=6)

        self.hist_canvas_container_eq = tk.Frame(preview_frame)
        self.hist_canvas_container_eq.pack(fill=tk.BOTH, expand=True)
        self.canvas_eq = None
        self.toolbar_eq = None

    # Histogram Specification
    def build_tab_spec(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Histogram Specification (Matching)")

        left = tk.Frame(tab)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        
        tk.Label(left, text="Source (Original) Image").pack(anchor="w")
        tk.Button(left, text="Load Source", command=self.load_spec_source).pack(fill=tk.X, pady=4)
        tk.Label(left, text="Target (Specified) Image").pack(anchor="w")
        tk.Button(left, text="Load Target", command=self.load_spec_target).pack(fill=tk.X, pady=4)

        tk.Button(left, text="Apply Histogram Specification", command=self.apply_specification).pack(fill=tk.X, pady=8)
        tk.Button(left, text="Save Result", command=self.save_spec_result).pack(fill=tk.X, pady=4)
        tk.Button(left, text="Reset Spec Tab", command=self.reset_spec_tab).pack(fill=tk.X, pady=4)

        
        preview_frame = tk.LabelFrame(right, text="Source | Target | Result", padx=6, pady=6)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.spec_labels_frame = tk.Frame(preview_frame)
        self.spec_labels_frame.pack(side=tk.TOP, fill=tk.X)
        self.spec_source_label = tk.Label(self.spec_labels_frame, text="Source", width=30); self.spec_source_label.pack(side=tk.LEFT, padx=6)
        self.spec_target_label = tk.Label(self.spec_labels_frame, text="Target", width=30); self.spec_target_label.pack(side=tk.LEFT, padx=6)
        self.spec_result_label = tk.Label(self.spec_labels_frame, text="Result", width=30); self.spec_result_label.pack(side=tk.LEFT, padx=6)

        self.spec_canvas_container = tk.Frame(preview_frame)
        self.spec_canvas_container.pack(fill=tk.BOTH, expand=True)
        self.canvas_spec = None
        self.toolbar_spec = None


    def load_image_single(self):
        path = filedialog.askopenfilename(filetypes=[("Image files","*.png;*.jpg;*.jpeg;*.bmp;*.tif")])
        if not path: return
        try:
            img = load_gray(path)
        except Exception as e:
            messagebox.showerror("Load error", str(e))
            return
        self.orig_img = img
        self.current_img = img.copy()
        self.display_single_before_after()
        self.clear_hist_canvas_stretch()

    def save_current_result(self):
        img = self.current_img
        if img is None:
            messagebox.showinfo("Save", "No image to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png"),("JPG","*.jpg")])
        if not path: return
        cv2.imwrite(path, img)
        messagebox.showinfo("Saved", f"Saved to {path}")

    def reset_single(self):
        if self.orig_img is not None:
            self.current_img = self.orig_img.copy()
            self.display_single_before_after()
            self.clear_hist_canvas_stretch()

    def display_single_before_after(self):
        
        if self.orig_img is None:
            return
        before_tk = pil_from_np_gray(self.orig_img)
        after_tk = pil_from_np_gray(self.current_img)
        
        for lbl in (getattr(self,"preview_before_label",None), getattr(self,"preview_before_label_eq",None)):
            if lbl is not None:
                lbl.configure(image=before_tk)
                lbl.image = before_tk
        for lbl in (getattr(self,"preview_after_label",None), getattr(self,"preview_after_label_eq",None)):
            if lbl is not None:
                lbl.configure(image=after_tk)
                lbl.image = after_tk

    
    def apply_linear_stretch(self):
        if self.current_img is None: return
        try:
            dst_min = int(self.ls_dstmin.get()); dst_max = int(self.ls_dstmax.get())
        except:
            messagebox.showerror("Input", "Invalid dst values.")
            return
        res = linear_stretch(self.current_img, dst_min=dst_min, dst_max=dst_max)
        self.current_img = res
        self.display_single_before_after()
        self.show_before_after_hist_stretch()

    def apply_shrink(self):
        if self.current_img is None: return
        try:
            dst_min = int(self.shr_dstmin.get()); dst_max = int(self.shr_dstmax.get())
        except:
            messagebox.showerror("Input","Invalid shrink values.")
            return
        res = shrink_map(self.current_img, dst_min, dst_max)
        self.current_img = res
        self.display_single_before_after()
        self.show_before_after_hist_stretch()

    def apply_offset(self):
        if self.current_img is None: return
        try:
            off = int(self.offset_entry.get())
        except:
            messagebox.showerror("Input","Invalid offset.")
            return
        res = slide(self.current_img, off)
        self.current_img = res
        self.display_single_before_after()
        self.show_before_after_hist_stretch()

    def apply_piecewise(self):
        if self.current_img is None: return
        try:
            thresh = int(self.pw_thresh.get())
            la = int(self.pw_la.get()); lb = int(self.pw_lb.get())
            hc = int(self.pw_hc.get()); hd = int(self.pw_hd.get())
        except:
            messagebox.showerror("Input","Invalid piecewise params.")
            return
        res = piecewise_linear(self.current_img, thresh, low_dst=(la,lb), high_dst=(hc,hd))
        self.current_img = res
        self.display_single_before_after()
        self.show_before_after_hist_stretch()

    def apply_percentile_stretch(self):
        if self.current_img is None: return
        try:
            lowp = float(self.h_low.get()); highp = float(self.h_high.get())
        except:
            messagebox.showerror("Input","Invalid percentiles.")
            return
        res = percentile_hist_stretch(self.current_img, low_pct=lowp, high_pct=highp, out_min=0, out_max=255)
        self.current_img = res
        self.display_single_before_after()
        self.show_before_after_hist_stretch()

   
    def clear_hist_canvas_stretch(self):
        if getattr(self,"canvas_stretch",None):
            try:
                self.canvas_stretch.get_tk_widget().destroy()
            except: pass
            self.canvas_stretch = None
        if getattr(self,"toolbar_stretch",None):
            try: self.toolbar_stretch.destroy()
            except: pass
            self.toolbar_stretch = None
        if getattr(self,"canvas_eq",None):
            try:
                self.canvas_eq.get_tk_widget().destroy()
            except: pass
            self.canvas_eq = None
        if getattr(self,"toolbar_eq",None):
            try: self.toolbar_eq.destroy()
            except: pass
            self.toolbar_eq = None

    def show_current_hist_single(self):
        if self.current_img is None: return
        self.clear_hist_canvas_stretch()
        fig = Figure(figsize=(6,4), dpi=100)
        ax = fig.add_subplot(111)
        plot_hist_on_axes(ax, self.current_img, title="Current Histogram")
        canvas = FigureCanvasTkAgg(fig, master=self.hist_canvas_container_stretch)
        canvas.draw()
        self.canvas_stretch = canvas
        self.canvas_stretch.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        tb = NavigationToolbar2Tk(canvas, self.hist_canvas_container_stretch); tb.update(); tb.pack(side=tk.TOP, fill=tk.X)
        self.toolbar_stretch = tb

    def show_before_after_hist_stretch(self):
        if self.orig_img is None or self.current_img is None: return
        self.clear_hist_canvas_stretch()
        fig = Figure(figsize=(10,4), dpi=100)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        plot_hist_on_axes(ax1, self.orig_img, title="Before Histogram")
        plot_hist_on_axes(ax2, self.current_img, title="After Histogram")
        canvas = FigureCanvasTkAgg(fig, master=self.hist_canvas_container_stretch)
        canvas.draw()
        self.canvas_stretch = canvas
        self.canvas_stretch.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        tb = NavigationToolbar2Tk(canvas, self.hist_canvas_container_stretch); tb.update(); tb.pack(side=tk.TOP, fill=tk.X)
        self.toolbar_stretch = tb

    
    def apply_histeq(self):
        if self.current_img is None: return
        res = histogram_equalize(self.current_img)
        self.current_img = res
        self.display_single_before_after()
        self.show_before_after_hist_stretch()

   
    def load_spec_source(self):
        path = filedialog.askopenfilename(filetypes=[("Image files","*.png;*.jpg;*.jpeg;*.bmp;*.tif")])
        if not path: return
        try:
            img = load_gray(path)
        except Exception as e:
            messagebox.showerror("Load", str(e)); return
        self.spec_src = img
        self.spec_result = None
        self.update_spec_preview()

    def load_spec_target(self):
        path = filedialog.askopenfilename(filetypes=[("Image files","*.png;*.jpg;*.jpeg;*.bmp;*.tif")])
        if not path: return
        try:
            img = load_gray(path)
        except Exception as e:
            messagebox.showerror("Load", str(e)); return
        self.spec_tgt = img
        self.spec_result = None
        self.update_spec_preview()

    def apply_specification(self):
        if self.spec_src is None or self.spec_tgt is None:
            messagebox.showinfo("Spec", "Load both Source and Target images first.")
            return
        mapping = histogram_specification_map(self.spec_src, self.spec_tgt)  # steps 1..3 slides
        result = apply_mapping(self.spec_src, mapping)  # step 5 slides
        self.spec_result = result
        self.update_spec_preview()
        
        self.show_spec_histograms()

    def update_spec_preview(self):
        
        for label, img in ((self.spec_source_label, self.spec_src),
                           (self.spec_target_label, self.spec_tgt),
                           (self.spec_result_label, self.spec_result)):
            if img is None:
                label.configure(image="", text=label.cget("text"))
                label.image = None
            else:
                tkimg = pil_from_np_gray(img)
                label.configure(image=tkimg, text="")
                label.image = tkimg

    def show_spec_histograms(self):
    
        if self.spec_src is None or self.spec_tgt is None or self.spec_result is None:
            return
        
        if getattr(self,"canvas_spec",None):
            try: self.canvas_spec.get_tk_widget().destroy()
            except: pass
            self.canvas_spec = None
        if getattr(self,"toolbar_spec",None):
            try: self.toolbar_spec.destroy()
            except: pass
            self.toolbar_spec = None
        fig = Figure(figsize=(12,4), dpi=100)
        a1 = fig.add_subplot(131); a2 = fig.add_subplot(132); a3 = fig.add_subplot(133)
        plot_hist_on_axes(a1, self.spec_src, title="Source Histogram")
        plot_hist_on_axes(a2, self.spec_tgt, title="Target Histogram")
        plot_hist_on_axes(a3, self.spec_result, title="Result Histogram")
        canvas = FigureCanvasTkAgg(fig, master=self.spec_canvas_container)
        canvas.draw()
        self.canvas_spec = canvas
        self.canvas_spec.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        tb = NavigationToolbar2Tk(canvas, self.spec_canvas_container); tb.update(); tb.pack(side=tk.TOP, fill=tk.X)
        self.toolbar_spec = tb

    def save_spec_result(self):
        if self.spec_result is None:
            messagebox.showinfo("Save", "No result to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if not path: return
        cv2.imwrite(path, self.spec_result)
        messagebox.showinfo("Saved", f"Saved {path}")

    def reset_spec_tab(self):
        self.spec_src = None; self.spec_tgt = None; self.spec_result = None
        self.update_spec_preview()
        if getattr(self,"canvas_spec",None):
            try: self.canvas_spec.get_tk_widget().destroy()
            except: pass
            self.canvas_spec = None
        if getattr(self,"toolbar_spec",None):
            try: self.toolbar_spec.destroy()
            except: pass
            self.toolbar_spec = None

if __name__ == "__main__":
    root = tk.Tk()
    app = GrayscaleApp(root)
    root.mainloop()
