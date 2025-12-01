#GROUP MEMBERS
#Ameer Abdullah - 21L-5694---> CS-5A
#Usman Ahmed - 21L-6273---> DS-9A


import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, scrolledtext
from PIL import Image, ImageTk
import numpy as np
from scipy.fftpack import dct, idct
import heapq
import pickle
import io
import os
import math

PREVIEW_MAX = (520, 520)    

STD_LUMINANCE_Q = np.array([
    [16,11,10,16,24,40,51,61],
    [12,12,14,19,26,58,60,55],
    [14,13,16,24,40,57,69,56],
    [14,17,22,29,51,87,80,62],
    [18,22,37,56,68,109,103,77],
    [24,35,55,64,81,104,113,92],
    [49,64,78,87,103,121,120,101],
    [72,92,95,98,112,100,103,99]
], dtype=np.float32)

def to_uint8(arr):
    return np.clip(np.round(arr), 0, 255).astype(np.uint8)

def psnr(orig, recon):
    mse = np.mean((orig.astype(np.float64) - recon.astype(np.float64))**2)
    if mse == 0:
        return float('inf')
    PIXEL_MAX = 255.0
    return 20 * np.log10(PIXEL_MAX / np.sqrt(mse))


def dct2(block):
    return dct(dct(block.T, norm='ortho').T, norm='ortho')

def idct2(block):
    return idct(idct(block.T, norm='ortho').T, norm='ortho')

ZIGZAG_IDX = None
def make_zigzag_idx():
    global ZIGZAG_IDX
    if ZIGZAG_IDX is not None:
        return ZIGZAG_IDX
    idx = []
    for s in range(0, 15):
        if s % 2 == 0:
            for i in range(s+1):
                j = s - i
                if i < 8 and j < 8:
                    idx.append((i,j))
        else:
            for i in range(s+1):
                j = s - i
                if j < 8 and i < 8:
                    idx.append((j,i))
    ZIGZAG_IDX = [(r,c) for r,c in idx if r<8 and c<8][:64]
    return ZIGZAG_IDX

def block_to_zigzag(block):
    zz = np.empty(64, dtype=np.int32)
    idx = make_zigzag_idx()
    for k,(r,c) in enumerate(idx):
        zz[k] = int(block[r,c])
    return zz

def zigzag_to_block(zz):
    block = np.zeros((8,8), dtype=np.int32)
    idx = make_zigzag_idx()
    for k,(r,c) in enumerate(idx):
        block[r,c] = int(zz[k])
    return block


def rle_encode_block(zz):
    out = []
    run = 0
    for v in zz[1:]:
        if v == 0:
            run += 1
        else:
            out.append((run, int(v)))
            run = 0
    out.append(('EOB', 0))
    return out

def rle_decode_block(dc_val, rle_pairs):
    zz = np.zeros(64, dtype=np.int32)
    zz[0] = int(dc_val)
    idx = 1
    for pair in rle_pairs:
        if pair[0] == 'EOB':
            break
        run, val = pair
        idx += run
        if idx < 64:
            zz[idx] = int(val)
            idx += 1
        else:
            break
    return zz

class HuffmanNode:
    def __init__(self,left=None,right=None,symbol=None,freq=0):
        self.left=left; self.right=right; self.symbol=symbol; self.freq=freq
    def __lt__(self,other):
        return self.freq < other.freq

def build_huffman_code(symbols):
    freq = {}
    for s in symbols:
        freq[s] = freq.get(s,0)+1
    heap = []
    for sym,f in freq.items():
        heapq.heappush(heap,(f, HuffmanNode(symbol=sym, freq=f)))
    if len(heap)==0:
        return {}, {}
    while len(heap)>1:
        f1, n1 = heapq.heappop(heap)
        f2, n2 = heapq.heappop(heap)
        parent = HuffmanNode(left=n1, right=n2, freq=f1+f2)
        heapq.heappush(heap,(parent.freq, parent))
    root = heapq.heappop(heap)[1]
    codes = {}
    def traverse(node, prefix=""):
        if node.symbol is not None:
            codes[node.symbol] = prefix or "0"
            return
        traverse(node.left, prefix+"0")
        traverse(node.right, prefix+"1")
    traverse(root)
    return codes, root

def huffman_encode(tokens, codes):
    bits = "".join(codes[t] for t in tokens)
    b = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            chunk = chunk.ljust(8, '0')
        b.append(int(chunk, 2))
    return bytes(b), len(bits)  

def huffman_decode(bitbytes, bitlen, root):
    bits = []
    for byte in bitbytes:
        bits.append(format(byte, '08b'))
    bitstr = "".join(bits)[:bitlen]
    out = []
    node = root
    for ch in bitstr:
        node = node.left if ch=='0' else node.right
        if node.symbol is not None:
            out.append(node.symbol)
            node = root
    return out


class SimpleJPEG:
    def __init__(self, quality=50):
        self.quality = quality
        self.qtable = self._scaled_q(STD_LUMINANCE_Q, quality)

    @staticmethod
    def _scaled_q(qtable, quality):
        q = np.array(qtable, dtype=np.float32)
        if quality < 50:
            scale = 5000 / quality
        else:
            scale = 200 - 2*quality
        q_scaled = np.floor((q * scale + 50) / 100.0)
        q_scaled[q_scaled < 1] = 1
        return q_scaled

    def compress(self, img):
        H, W = img.shape
        pad_h = (8 - (H % 8)) % 8
        pad_w = (8 - (W % 8)) % 8
        padded = np.pad(img, ((0,pad_h),(0,pad_w)), mode='edge')
        H2, W2 = padded.shape

        blocks_dc = []
        blocks_rle = []
        
        for i in range(0, H2, 8):
            for j in range(0, W2, 8):
                block = padded[i:i+8, j:j+8].astype(np.float32)
                
                block -= 128.0
                
                coeff = dct2(block)
                
                qcoeff = np.round(coeff / self.qtable).astype(np.int32)
            
                zz = block_to_zigzag(qcoeff)
                
                blocks_dc.append(int(zz[0]))
                rle = rle_encode_block(zz)
                
                tokens = []
                for p in rle:
                    tokens.append(p)
                blocks_rle.append(tokens)

        
        flat_tokens = []
        for tlist in blocks_rle:
            for tok in tlist:
                flat_tokens.append(tok)

        
        codes, tree = build_huffman_code(flat_tokens)
        
        codes = codes or {}

        
        dc_arr = np.array(blocks_dc, dtype=np.int32)
        dc_diff = np.empty_like(dc_arr)
        prev = 0
        for i, v in enumerate(dc_arr):
            dc_diff[i] = v - prev
            prev = v

        
        token_sequence = []
        for tlist in blocks_rle:
            for tok in tlist:
                token_sequence.append(tok)

        
        if codes:
            encoded_bytes, bitlen = huffman_encode(token_sequence, codes)
        else:
            
            encoded_bytes = pickle.dumps(token_sequence)
            bitlen = None
            tree = None

        compressed = {
            'H': H, 'W': W, 'pad_h': pad_h, 'pad_w': pad_w,
            'quality': self.quality,
            'qtable': self.qtable,
            'dc_diff': dc_diff.tolist(),
            'encoded_bytes': encoded_bytes,
            'bitlen': bitlen,
            'huff_tree': tree,  
            'token_codes': codes  
        }
    
        return compressed

    def decompress(self, compressed):
        H = compressed['H']; W = compressed['W']
        pad_h = compressed['pad_h']; pad_w = compressed['pad_w']
        qtable = compressed['qtable']

        dc_diff = np.array(compressed['dc_diff'], dtype=np.int32)
        
        dc_seq = np.empty_like(dc_diff)
        prev = 0
        for i,v in enumerate(dc_diff):
            dc_seq[i] = prev + v
            prev = dc_seq[i]

        
        token_sequence = None
        if compressed['bitlen'] is not None and compressed['huff_tree'] is not None:
            token_sequence = huffman_decode(compressed['encoded_bytes'], compressed['bitlen'], compressed['huff_tree'])
        elif compressed['token_codes'] and compressed['encoded_bytes']:
            
            try:
                token_sequence = pickle.loads(compressed['encoded_bytes'])
            except Exception:
                token_sequence = []
        else:
            
            token_sequence = pickle.loads(compressed['encoded_bytes'])

        
        blocks_rle = []
        idx = 0
        Nblocks = len(dc_seq)
        for b in range(Nblocks):
            lst = []
            while True:
                if idx >= len(token_sequence):
                    
                    lst.append(('EOB', 0))
                    break
                tok = token_sequence[idx]; idx += 1
                lst.append(tok)
                if tok[0] == 'EOB':
                    break
            blocks_rle.append(lst)

        
        blocks = []
        for b in range(Nblocks):
            zz = rle_decode_block(dc_seq[b], blocks_rle[b])
            qcoeff = zigzag_to_block(zz)
            
            deq = qcoeff.astype(np.float32) * qtable
            
            block = idct2(deq)
            
            block = block + 128.0
            block = to_uint8(block)
            blocks.append(block)

        blocks_per_row = (W + pad_w) // 8
        H2 = H + pad_h; W2 = W + pad_w
        recon = np.zeros((H2, W2), dtype=np.uint8)
        bidx = 0
        for i in range(0, H2, 8):
            for j in range(0, W2, 8):
                recon[i:i+8, j:j+8] = blocks[bidx]
                bidx += 1
        
        return recon[:H, :W]

def _calculate_entropy(tokens):
    if not tokens:
        return 0.0
    
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    
    total_tokens = len(tokens)
    entropy = 0.0
    
    for f in freq.values():
        p = f / total_tokens
        entropy -= p * math.log2(p)
        
    return entropy

def _capture_quantized_info(img, quality):
    coder = SimpleJPEG(quality=quality)
    qtable = coder.qtable
    H, W = img.shape
    
    pad_h = (8 - (H % 8)) % 8
    pad_w = (8 - (W % 8)) % 8
    padded = np.pad(img, ((0,pad_h),(0,pad_w)), mode='edge')
    H2, W2 = padded.shape
    
    blocks_rle = []
    qcoeff_blocks = [] 

    for i in range(0, H2, 8):
        for j in range(0, W2, 8):
            block = padded[i:i+8, j:j+8].astype(np.float32)
            
            block -= 128.0
            coeff = dct2(block)
            qcoeff = np.round(coeff / qtable).astype(np.int32)
            
            qcoeff_blocks.append(qcoeff)
        
            zz = block_to_zigzag(qcoeff)
            rle = rle_encode_block(zz)
            tokens = [p for p in rle]
            blocks_rle.append(tokens)

    token_sequence = []
    for tlist in blocks_rle:
        token_sequence.extend(tlist)

    compressed = coder.compress(img)
    
    return compressed, token_sequence, qcoeff_blocks


class JPEGApp:
    def __init__(self, root):
        self.root = root
        root.title("JPEG Compressor (grayscale)")
        self.orig_img = None    
        self.recon_img = None
        self.compressed_blob = None
        
        self.compressed_data = None 
        self.huffman_tokens = None
        self.quantized_coeffs = None
        
        self.photo_orig = None
        self.photo_recon = None

        
        ctrl = tk.Frame(root); ctrl.pack(pady=6)
        tk.Button(ctrl, text="Open Image", command=self.open_image).pack(side=tk.LEFT, padx=6)
        tk.Button(ctrl, text="Save Reconstructed", command=self.save_reconstructed).pack(side=tk.LEFT, padx=6)
        tk.Button(ctrl, text="Save Compressed", command=self.save_compressed).pack(side=tk.LEFT, padx=6)

        self.quality_var = tk.IntVar(value=50)
        qscale = tk.Scale(ctrl, from_=1, to=100, label="Quantization Slider", orient=tk.HORIZONTAL, variable=self.quality_var)
        qscale.pack(side=tk.LEFT, padx=6)

        tk.Button(ctrl, text="Compress & Decompress", command=self.run_jpeg).pack(side=tk.LEFT, padx=6)
        
        tk.Button(ctrl, text="Quantized Preview", command=self.show_quantized_preview).pack(side=tk.LEFT, padx=6)
        tk.Button(ctrl, text="Show Q-Table", command=self.show_q_table).pack(side=tk.LEFT, padx=6)
        tk.Button(ctrl, text="Show Huffman Table", command=self.show_huffman_table).pack(side=tk.LEFT, padx=6)
        stats = tk.Frame(root); stats.pack(fill=tk.X)
        self.lbl_cr = tk.Label(stats, text="Compression Ratio: -")
        self.lbl_cr.pack(side=tk.LEFT, padx=6)
        self.lbl_psnr = tk.Label(stats, text="PSNR: -")
        self.lbl_psnr.pack(side=tk.LEFT, padx=6)
        
        self.lbl_entropy = tk.Label(stats, text="Entropy: -")
        self.lbl_entropy.pack(side=tk.LEFT, padx=6)

        canvas_frame = tk.Frame(root); canvas_frame.pack(pady=8)
        
        self.canvas_orig = tk.Canvas(canvas_frame, width=PREVIEW_MAX[0], height=PREVIEW_MAX[1], bg='lightgray')
        self.canvas_orig.pack(side=tk.LEFT, padx=8)
        self.canvas_recon = tk.Canvas(canvas_frame, width=PREVIEW_MAX[0], height=PREVIEW_MAX[1], bg='lightgray')
        self.canvas_recon.pack(side=tk.LEFT, padx=8)

        self.lbl_orig = tk.Label(root, text="Original (grayscale)")
        self.lbl_orig.pack()
        self.lbl_recon = tk.Label(root, text="Reconstructed")
        self.lbl_recon.pack()

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images","*.png;*.jpg;*.jpeg;*.bmp;*.tif")])
        if not path: return
        im = Image.open(path).convert('L') 
        arr = np.array(im, dtype=np.uint8)
        self.orig_img = arr
        self.recon_img = None
        self.compressed_blob = None
        self.compressed_data = None
        self.huffman_tokens = None
        self.quantized_coeffs = None
        self.display_on_canvas(self.canvas_orig, im, set_photo=True, which='orig')
        self.canvas_recon.delete("all")
        self.lbl_entropy.config(text="Entropy: -")


    def display_on_canvas(self, canvas, pil_img, set_photo=False, which='orig'):
        
        max_w, max_h = PREVIEW_MAX
        w,h = pil_img.size
        ratio = min(max_w / w, max_h / h, 1.0)
        new_w, new_h = int(w*ratio), int(h*ratio)
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.ANTIALIAS 

        img_r = pil_img.resize((new_w, new_h), resample_filter)
        tkimg = ImageTk.PhotoImage(img_r)
        canvas.delete("all")
        x = (max_w - new_w)//2
        y = (max_h - new_h)//2
        canvas.create_image(x, y, anchor='nw', image=tkimg)
        
        if set_photo:
            if which=='orig':
                self.photo_orig = tkimg
            else:
                self.photo_recon = tkimg
        else:
            if which=='orig':
                self.photo_orig = tkimg
            else:
                self.photo_recon = tkimg

    def run_jpeg(self):
        if self.orig_img is None:
            messagebox.showinfo("Info","Load an image first.")
            return
        
        quality = int(self.quality_var.get())
        
        compressed, token_sequence, qcoeff_blocks = _capture_quantized_info(self.orig_img, quality)
        self.compressed_data = compressed
        self.huffman_tokens = token_sequence
        self.quantized_coeffs = qcoeff_blocks
        
        entropy = _calculate_entropy(self.huffman_tokens)
        self.lbl_entropy.config(text=f"Entropy: {entropy:.2f} bits/symbol")

        coder = SimpleJPEG(quality=quality)
        
        packed = pickle.dumps(compressed)
        size_compressed = len(packed)
        size_orig = self.orig_img.size  
        orig_bytes = size_orig
        cr = (orig_bytes / size_compressed) if size_compressed>0 else float('inf')
        recon = coder.decompress(compressed)
        self.recon_img = recon
        
        self.display_on_canvas(self.canvas_recon, Image.fromarray(recon), set_photo=True, which='recon')
        self.display_on_canvas(self.canvas_orig, Image.fromarray(self.orig_img), set_photo=True, which='orig')
        
        self.lbl_cr.config(text=f"Compression Ratio: {orig_bytes}:{size_compressed} = {cr:.2f}:1")
        self.lbl_psnr.config(text=f"PSNR: {psnr(self.orig_img, recon):.2f} dB")
        self.compressed_blob = packed

    def save_reconstructed(self):
        if self.recon_img is None:
            messagebox.showinfo("Info","No reconstructed image to save.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if p:
            Image.fromarray(self.recon_img).save(p)
            messagebox.showinfo("Saved", f"Saved reconstructed image to {p}")

    def save_compressed(self):
        if self.compressed_blob is None:
            messagebox.showinfo("Info","No compressed data to save. Run compression first.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".jdemo", filetypes=[("JPEG demo","*.jdemo")])
        if p:
            with open(p, 'wb') as f:
                f.write(self.compressed_blob)
            messagebox.showinfo("Saved", f"Saved compressed demo file to {p}")

    
    def _reconstruct_quantized_image(self, H, W, pad_h, pad_w, qtable, qcoeff_blocks):
        H2 = H + pad_h; W2 = W + pad_w
        quantized_recon = np.zeros((H2, W2), dtype=np.uint8)
        bidx = 0
        
        for i in range(0, H2, 8):
            for j in range(0, W2, 8):
                qcoeff = qcoeff_blocks[bidx]
                
                deq = qcoeff.astype(np.float32) * qtable
                
                block = idct2(deq)
                
                block = block + 128.0
                block = to_uint8(block)
                
                quantized_recon[i:i+8, j:j+8] = block
                bidx += 1
                
        return quantized_recon[:H, :W]
    
    def _create_heatmap(self, qcoeff_blocks, H, W, pad_h, pad_w):
        H2 = H + pad_h; W2 = W + pad_w
        full_dct_magnitude = np.zeros((H2, W2), dtype=np.float32)
        bidx = 0
        
        for i in range(0, H2, 8):
            for j in range(0, W2, 8):
                magnitude_block = np.abs(qcoeff_blocks[bidx]).astype(np.float32)
                full_dct_magnitude[i:i+8, j:j+8] = magnitude_block
                bidx += 1

        max_val = np.max(full_dct_magnitude)
        if max_val == 0:
            heatmap_array = np.zeros_like(full_dct_magnitude, dtype=np.uint8)
        else:
            heatmap_array = to_uint8((full_dct_magnitude / max_val) * 255)
            
        return heatmap_array[:H, :W]


    def show_quantized_preview(self):
        if self.compressed_data is None:
            messagebox.showinfo("Info", "Run compression first to generate quantized data.")
            return

        H = self.compressed_data['H']; W = self.compressed_data['W']
        pad_h = self.compressed_data['pad_h']; pad_w = self.compressed_data['pad_w']
        qtable = self.compressed_data['qtable']
        qcoeffs = self.quantized_coeffs

        quantized_image_array = self._reconstruct_quantized_image(H, W, pad_h, pad_w, qtable, qcoeffs)
        pil_quantized_img = Image.fromarray(quantized_image_array, 'L')
        
        heatmap_array = self._create_heatmap(qcoeffs, H, W, pad_h, pad_w)
        pil_heatmap = Image.fromarray(heatmap_array, 'L')


        preview_win = Toplevel(self.root)
        preview_win.title(f"Quantization Preview (Q={self.compressed_data['quality']})")
        
        img_frame = tk.Frame(preview_win)
        img_frame.pack(padx=10, pady=10)
        
        tk.Label(img_frame, text="Lossy Reconstructed Image (IDCT of Quantized Coefficients)").grid(row=0, column=0, pady=5)
        canvas1 = tk.Canvas(img_frame, width=300, height=300, bg='black')
        canvas1.grid(row=1, column=0, padx=10)
        self._display_small_image(canvas1, pil_quantized_img, 'quant_img')
        
        tk.Label(img_frame, text="Quantized DCT Magnitude Heatmap (Frequency Data)").grid(row=0, column=1, pady=5)
        canvas2 = tk.Canvas(img_frame, width=300, height=300, bg='black')
        canvas2.grid(row=1, column=1, padx=10)
        self._display_small_image(canvas2, pil_heatmap, 'heatmap')
        
    def _display_small_image(self, canvas, pil_img, tag):
        max_w, max_h = 300, 300
        w,h = pil_img.size
        ratio = min(max_w / w, max_h / h, 1.0)
        new_w, new_h = int(w*ratio), int(h*ratio)
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.ANTIALIAS 

        img_r = pil_img.resize((new_w, new_h), resample_filter)
        tkimg = ImageTk.PhotoImage(img_r)
        
        canvas.delete("all")
        x = (max_w - new_w)//2
        y = (max_h - new_h)//2
        canvas.create_image(x, y, anchor='nw', image=tkimg)
        
        canvas.tkimg = tkimg 

    def show_q_table(self):
        if self.compressed_data is None:
            messagebox.showinfo("Info", "Run compression first to view the Q-Table.")
            return

        qtable = self.compressed_data['qtable']
        
        qtable_win = Toplevel(self.root)
        qtable_win.title(f"Quantization Table (Q={self.compressed_data['quality']})")
        
        qtable_str = "Luminance Quantization Matrix:\n\n"
        qtable_str += np.array2string(qtable, separator=', ', formatter={'float_kind':lambda x: f"{int(x):>3}"})
        
        tk.Label(qtable_win, text=qtable_str, font=("Courier", 12), justify=tk.LEFT).pack(padx=10, pady=10)
 

    def show_huffman_table(self):
        if self.compressed_data is None:
            messagebox.showinfo("Info", "Run compression first to view the Huffman Table.")
            return

        codes = self.compressed_data.get('token_codes', {})
        if not codes:
            messagebox.showinfo("Info", "No Huffman codes available.")
            return

        huff_win = Toplevel(self.root)
        huff_win.title("Huffman Code Table")
        
        st = scrolledtext.ScrolledText(huff_win, width=50, height=30, font=("Courier", 10))
        st.pack(padx=10, pady=10)
        
        st.insert(tk.END, "Huffman Code\n")
        for symbol, code in sorted(codes.items(), key=lambda x: (len(x[1]), x[1])):
            st.insert(tk.END, f"{symbol}\t{code}\n")
        
        st.config(state=tk.DISABLED)

if __name__ == "__main__":
    try:
        Image.Resampling.LANCZOS
    except AttributeError:
        Image.Resampling.LANCZOS = Image.ANTIALIAS 

    root = tk.Tk()
    app = JPEGApp(root)
    root.mainloop()