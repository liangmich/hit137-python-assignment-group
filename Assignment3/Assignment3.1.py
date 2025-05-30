import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageEnhance
import cv2
import numpy as np
from collections import deque

class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Image Editor")
        self.root.geometry("1200x800")
        
        self.original_img = None      # Stores the original image (OpenCV RGB format)
        self.cropped_img = None       # Stores the cropped region from the original image
        self.processed_img = None     # The processed image after crop/scale/adjustments
        self.display_ratio = 1.0      # Ratio for fitting original image on the left canvas
        self.current_scale = 1.0      # Current scaling factor for the cropped image
        
        self.history_stack = deque(maxlen=20)
        self.redo_stack = deque(maxlen=20)
        
        self.create_ui()
        self.setup_shortcuts()
        self.show_placeholders()
        
    def create_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left canvas: displays the original image, auto-fit
        self.orig_canvas = tk.Canvas(self.canvas_frame, width=500, height=500, bg='#2E2E2E')
        self.orig_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right canvas: processed image, with scrollbars for navigation
        proc_container = ttk.Frame(self.canvas_frame)
        proc_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.proc_canvas = tk.Canvas(proc_container, bg='#2E2E2E')
        self.proc_canvas.grid(row=0, column=0, sticky="nsew")
        xbar = ttk.Scrollbar(proc_container, orient=tk.HORIZONTAL, command=self.proc_canvas.xview)
        ybar = ttk.Scrollbar(proc_container, orient=tk.VERTICAL, command=self.proc_canvas.yview)
        self.proc_canvas.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
        xbar.grid(row=1, column=0, sticky="we")
        ybar.grid(row=0, column=1, sticky="ns")
        proc_container.rowconfigure(0, weight=1)
        proc_container.columnconfigure(0, weight=1)

        # Mouse wheel scroll binding
        def _on_mousewheel(event):
            self.proc_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _on_shiftmousewheel(event):
            self.proc_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        self.proc_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.proc_canvas.bind_all("<Shift-MouseWheel>", _on_shiftmousewheel)

        control_panel = ttk.Frame(main_frame)
        control_panel.pack(fill=tk.X, pady=10)
        
        file_frame = ttk.Frame(control_panel)
        file_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Open (Ctrl+O)", command=self.open_image).pack(side=tk.LEFT, padx=2)
        self.save_btn = ttk.Button(file_frame, text="Save (Ctrl+S)", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Undo (Ctrl+Z)", command=self.undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Redo (Ctrl+Y)", command=self.redo).pack(side=tk.LEFT, padx=2)
        
        scale_frame = ttk.Frame(control_panel)
        scale_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(scale_frame, text="Scale:").pack(side=tk.LEFT)
        self.scale_var = tk.DoubleVar(value=100)
        self.scale_slider = ttk.Scale(
            scale_frame,
            from_=10,
            to=200,
            orient=tk.HORIZONTAL,
            variable=self.scale_var,
            command=lambda _: self.on_scale_change(),
            length=200
        )
        self.scale_slider.pack(side=tk.LEFT, padx=5)
        self.scale_label = ttk.Label(scale_frame, text="100%", width=5)
        self.scale_label.pack(side=tk.LEFT)
        
        adjust_frame = ttk.Frame(control_panel)
        adjust_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(adjust_frame, text="Brightness").pack(side=tk.LEFT)
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.brightness_slider = ttk.Scale(
            adjust_frame,
            from_=0.1,
            to=3.0,
            orient=tk.HORIZONTAL,
            variable=self.brightness_var,
            command=lambda _: self.on_brightness_contrast_change(),
            length=120
        )
        self.brightness_slider.pack(side=tk.LEFT, padx=2)
        ttk.Label(adjust_frame, text="Contrast").pack(side=tk.LEFT)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.contrast_slider = ttk.Scale(
            adjust_frame,
            from_=0.1,
            to=3.0,
            orient=tk.HORIZONTAL,
            variable=self.contrast_var,
            command=lambda _: self.on_brightness_contrast_change(),
            length=120
        )
        self.contrast_slider.pack(side=tk.LEFT, padx=2)
        
        rotate_frame = ttk.Frame(control_panel)
        rotate_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(rotate_frame, text="Rotate Left", command=lambda: self.rotate_image(90)).pack(side=tk.LEFT)
        ttk.Button(rotate_frame, text="Rotate Right", command=lambda: self.rotate_image(-90)).pack(side=tk.LEFT)
        
        self.status_bar = ttk.Label(self.root, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X)
        
        # Crop selection on original image
        self.orig_canvas.bind("<ButtonPress-1>", self.start_crop)
        self.orig_canvas.bind("<B1-Motion>", self.update_crop)
        self.orig_canvas.bind("<ButtonRelease-1>", self.finalize_crop)
    
    def setup_shortcuts(self):
        self.root.bind("<Control-o>", lambda e: self.open_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
    
    def show_placeholders(self):
        self.orig_canvas.delete("all")
        self.orig_canvas.create_text(250, 250, text="Open image to start editing", fill="white", font=('Arial', 12))
        self.proc_canvas.delete("all")
        self.proc_canvas.create_text(250, 250, text="Processed result will appear here", fill="white", font=('Arial', 12))
    
    def open_image(self):
        filetypes = [
            ("Image Files", "*.jpg *.jpeg *.png *.bmp"),
            ("All Files", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            try:
                self.original_img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
                self.cropped_img = None
                self.reset_processing_state()
                self.update_displays()
                self.save_btn.state(["!disabled"])
                self.scale_slider.config(state="normal")
                self.status_bar.config(text=f"Loaded image: {path}")
            except Exception as e:
                self.status_bar.config(text=f"Error: {str(e)}")
    
    def reset_processing_state(self):
        self.processed_img = self.original_img.copy() if self.original_img is not None else None
        self.current_scale = 1.0
        self.scale_var.set(100)
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.history_stack.clear()
        self.redo_stack.clear()
    
    def update_displays(self):
        # Draw original image (auto fit)
        if self.original_img is not None:
            h, w = self.original_img.shape[:2]
            canvas_w = self.orig_canvas.winfo_width()
            canvas_h = self.orig_canvas.winfo_height()
            ratio = min(canvas_w/w, canvas_h/h)
            self.display_ratio = ratio
            disp_img = cv2.resize(self.original_img, (int(w*ratio), int(h*ratio)))
            self.tk_orig = ImageTk.PhotoImage(Image.fromarray(disp_img))
            self.orig_canvas.create_image(canvas_w//2, canvas_h//2, image=self.tk_orig, anchor=tk.CENTER)
        # Draw processed image (actual size, not fit, use scrollbars if needed)
        if self.processed_img is not None:
            self.proc_canvas.delete("all")
            h, w = self.processed_img.shape[:2]
            self.tk_proc = ImageTk.PhotoImage(Image.fromarray(self.processed_img))
            self.proc_canvas.create_image(0, 0, image=self.tk_proc, anchor=tk.NW)
            self.proc_canvas.config(scrollregion=(0, 0, w, h))
    
    def start_crop(self, event):
        self.crop_start = (event.x, event.y)
        self.crop_rect = self.orig_canvas.create_rectangle(
            *self.crop_start, *self.crop_start,
            outline='#FF5555', dash=(5,5), width=2
        )
    
    def update_crop(self, event):
        if self.crop_rect:
            self.orig_canvas.coords(
                self.crop_rect,
                *self.crop_start,
                event.x, event.y
            )
    
    def finalize_crop(self, event):
        if self.crop_rect and self.original_img is not None:
            img_w = int(self.original_img.shape[1] * self.display_ratio)
            img_h = int(self.original_img.shape[0] * self.display_ratio)
            canvas_w = self.orig_canvas.winfo_width()
            canvas_h = self.orig_canvas.winfo_height()
            offset_x = (canvas_w - img_w) // 2
            offset_y = (canvas_h - img_h) // 2
            x1 = (self.crop_start[0] - offset_x) / self.display_ratio
            y1 = (self.crop_start[1] - offset_y) / self.display_ratio
            x2 = (event.x - offset_x) / self.display_ratio
            y2 = (event.y - offset_y) / self.display_ratio
            orig_h, orig_w = self.original_img.shape[:2]
            x1 = max(0, min(x1, orig_w))
            x2 = max(0, min(x2, orig_w))
            y1 = max(0, min(y1, orig_h))
            y2 = max(0, min(y2, orig_h))
            x1, x2 = sorted([int(x1), int(x2)])
            y1, y2 = sorted([int(y1), int(y2)])
            if x2 > x1 and y2 > y1:
                self.cropped_img = self.original_img[y1:y2, x1:x2]
                self.current_scale = 1.0
                self.scale_var.set(100)
                self.brightness_var.set(1.0)
                self.contrast_var.set(1.0)
                self.push_history()
                self.apply_adjustments()
                self.update_displays()
                self.status_bar.config(text=f"Cropped: {x2-x1}x{y2-y1} pixels")
    
    def on_scale_change(self):
        if self.cropped_img is not None:
            self.current_scale = self.scale_var.get() / 100.0
            self.scale_label.config(text=f"{int(self.current_scale*100)}%")
            self.push_history()
            self.apply_adjustments()
            self.update_displays()
    
    def on_brightness_contrast_change(self):
        if self.cropped_img is not None:
            self.apply_adjustments()
            self.update_displays()
    
    def apply_adjustments(self):
        if self.cropped_img is None:
            return
        scale = self.current_scale
        h, w = self.cropped_img.shape[:2]
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        img = cv2.resize(self.cropped_img, (new_w, new_h), interpolation=interp)
        pil_img = Image.fromarray(img)
        pil_img = ImageEnhance.Brightness(pil_img).enhance(self.brightness_var.get())
        pil_img = ImageEnhance.Contrast(pil_img).enhance(self.contrast_var.get())
        self.processed_img = np.array(pil_img)
    
    def rotate_image(self, angle):
        if self.cropped_img is not None:
            self.push_history()
            img = self.cropped_img
            h, w = img.shape[:2]
            center = (w//2, h//2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img, rot_mat, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            self.cropped_img = rotated
            self.apply_adjustments()
            self.update_displays()
    
    def push_history(self):
        state = {
            'cropped': self.cropped_img.copy() if self.cropped_img is not None else None,
            'scale': self.current_scale,
            'brightness': self.brightness_var.get(),
            'contrast': self.contrast_var.get()
        }
        self.history_stack.append(state)
        self.redo_stack.clear()
    
    def restore_state(self, state):
        self.cropped_img = state['cropped'].copy() if state['cropped'] is not None else None
        self.current_scale = state['scale']
        self.scale_var.set(state['scale'] * 100)
        self.brightness_var.set(state['brightness'])
        self.contrast_var.set(state['contrast'])
        self.apply_adjustments()
        self.update_displays()
    
    def undo(self):
        if self.history_stack:
            current_state = {
                'cropped': self.cropped_img.copy() if self.cropped_img is not None else None,
                'scale': self.current_scale,
                'brightness': self.brightness_var.get(),
                'contrast': self.contrast_var.get()
            }
            self.redo_stack.append(current_state)
            prev_state = self.history_stack.pop()
            self.restore_state(prev_state)
    
    def redo(self):
        if self.redo_stack:
            current_state = {
                'cropped': self.cropped_img.copy() if self.cropped_img is not None else None,
                'scale': self.current_scale,
                'brightness': self.brightness_var.get(),
                'contrast': self.contrast_var.get()
            }
            self.history_stack.append(current_state)
            next_state = self.redo_stack.pop()
            self.restore_state(next_state)
    
    def save_image(self):
        if self.processed_img is not None:
            filetypes = [
                ("PNG Files", "*.png"),
                ("JPEG Files", "*.jpg"),
                ("BMP Files", "*.bmp"),
                ("All Files", "*.*")
            ]
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=filetypes,
                title="Save Image"
            )
            if path:
                try:
                    save_img = cv2.cvtColor(self.processed_img, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(path, save_img)
                    self.status_bar.config(text=f"Image saved: {path}")
                except Exception as e:
                    self.status_bar.config(text=f"Save failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditor(root)
    root.mainloop()

