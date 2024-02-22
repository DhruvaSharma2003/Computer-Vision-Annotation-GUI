#!/usr/bin/env python
# coding: utf-8

# In[3]:


import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk, simpledialog, colorchooser
from PIL import Image, ImageTk

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor")

        self.image_path = None
        self.image = None
        self.processed_image = None
        self.annotations = []
        self.text_annotations = []
        self.annotation_types = ["Line", "Rectangle", "Circle", "Text"]
        self.current_annotation_type = tk.StringVar(value="Line")
        self.undo_stack = []
        self.redo_stack = []

        self.annotation_color = (0, 255, 0)  
        self.text_color = (0, 0, 0)  
        self.text_size = 1

        self.create_widgets()

    def create_widgets(self):
    
        top_button_frame = tk.Frame(self.root)
        top_button_frame.pack(pady=10)

        browse_button = ttk.Button(top_button_frame, text="Browse Image", command=self.browse_image)
        browse_button.grid(row=0, column=0, padx=5)

        process_button = ttk.Button(top_button_frame, text="Process Image", command=self.process_image)
        process_button.grid(row=0, column=1, padx=5)

        convert_label = ttk.Label(top_button_frame, text="Convert To:")
        convert_label.grid(row=0, column=2, padx=5)
        self.convert_var = tk.StringVar(value="RGB")
        convert_options = ttk.OptionMenu(top_button_frame, self.convert_var, "RGB", "Grayscale", "Binary")
        convert_options.grid(row=0, column=3, padx=5)

        brightness_label = ttk.Label(top_button_frame, text="Brightness:")
        brightness_label.grid(row=0, column=4, padx=5)
        self.brightness_scale = ttk.Scale(top_button_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        self.brightness_scale.grid(row=0, column=5, padx=5)

        contrast_label = ttk.Label(top_button_frame, text="Contrast:")
        contrast_label.grid(row=0, column=6, padx=5)
        self.contrast_scale = ttk.Scale(top_button_frame, from_=1, to=3, orient=tk.HORIZONTAL)
        self.contrast_scale.grid(row=0, column=7, padx=5)

        annotation_frame = tk.LabelFrame(self.root, text="Annotation")
        annotation_frame.pack(padx=10, pady=5)

        for idx, annotation_type in enumerate(self.annotation_types):
            button = ttk.Button(annotation_frame, text=annotation_type, command=lambda at=annotation_type: self.set_annotation_type(at))
            button.grid(row=0, column=idx, padx=5)

        color_button_frame = tk.Frame(self.root)
        color_button_frame.pack(pady=5)

        annotation_color_button = ttk.Button(color_button_frame, text="Choose Annotation Color", command=self.choose_annotation_color)
        annotation_color_button.grid(row=0, column=0, padx=5)

        text_color_button = ttk.Button(color_button_frame, text="Choose Text Color", command=self.choose_text_color)
        text_color_button.grid(row=0, column=1, padx=5)

        undo_button = ttk.Button(self.root, text="Undo", command=self.undo_annotation)
        undo_button.pack(side=tk.LEFT, padx=5)
        redo_button = ttk.Button(self.root, text="Redo", command=self.redo_annotation)
        redo_button.pack(side=tk.LEFT, padx=5)

        self.image_frame = tk.LabelFrame(self.root, text="Image Display")
        self.image_frame.pack(padx=10, pady=10)
        self.panel = tk.Label(self.image_frame)
        self.panel.pack()

        self.panel.bind("<ButtonPress-1>", self.on_click)
        self.panel.bind("<B1-Motion>", self.on_drag)
        self.panel.bind("<ButtonRelease-1>", self.on_release)

    def browse_image(self):
        self.image_path = filedialog.askopenfilename()
        if self.image_path:
            self.image = cv2.imread(self.image_path)
            self.display_image(self.image)

    def display_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)

        self.panel.config(image=image)
        self.panel.image = image

    def process_image(self):
        if self.image is None:
            return
        
        if self.convert_var.get() == "Grayscale":
            self.processed_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        elif self.convert_var.get() == "Binary":
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            _, self.processed_image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        else:
            self.processed_image = self.image.copy()

        brightness = self.brightness_scale.get() - 50
        contrast = self.contrast_scale.get()
        self.processed_image = cv2.convertScaleAbs(self.processed_image, alpha=contrast, beta=brightness)

        self.display_image(self.processed_image)

    def set_annotation_type(self, annotation_type):
        self.current_annotation_type.set(annotation_type)

    def choose_annotation_color(self):
        color = colorchooser.askcolor(title="Choose Annotation Color")
        if color:
            self.annotation_color = tuple(map(int, color[0]))

    def choose_text_color(self):
        color = colorchooser.askcolor(title="Choose Text Color")
        if color:
            self.text_color = tuple(map(int, color[0]))

    def update_text_size(self, value):
        self.text_size = int(value)

    def on_click(self, event):
        annotation_type = self.current_annotation_type.get()
        self.start_x = event.x
        self.start_y = event.y

        if annotation_type == "Text":
            self.annotate_text()
        else:
            self.annotating = True

    def on_drag(self, event):
        if self.annotating:
            self.end_x = event.x
            self.end_y = event.y
            clone = self.image.copy()
            annotation_type = self.current_annotation_type.get()

            if annotation_type == "Line":
                cv2.line(clone, (self.start_x, self.start_y), (self.end_x, self.end_y), self.annotation_color, 2)
            elif annotation_type == "Rectangle":
                cv2.rectangle(clone, (self.start_x, self.start_y), (self.end_x, self.end_y), self.annotation_color, 2)
            elif annotation_type == "Circle":
                radius = int(np.sqrt((self.end_x - self.start_x) ** 2 + (self.end_y - self.start_y) ** 2))
                cv2.circle(clone, (self.start_x, self.start_y), radius, self.annotation_color, 2)

            self.display_image(clone)

    def on_release(self, event):
        if self.annotating:
            self.annotating = False
            annotation_type = self.current_annotation_type.get()
            if annotation_type != "Text":
                self.annotations.append((annotation_type, self.start_x, self.start_y, self.end_x, self.end_y))
                self.update_image()

    def annotate_text(self):
        text = simpledialog.askstring("Input", "Enter text:")
        if text is not None:
            self.text_annotations.append((text, self.start_x, self.start_y))
            self.update_image()

    def undo_annotation(self):
        if self.annotations or self.text_annotations:
            self.redo_stack.append((self.annotations.copy(), self.text_annotations.copy()))
            self.annotations.clear()
            self.text_annotations.clear()
            self.update_image()

    def redo_annotation(self):
        if self.redo_stack:
            self.annotations, self.text_annotations = self.redo_stack.pop()
            self.update_image()

    def update_image(self):
        clone = self.image.copy()
        for annotation in self.annotations:
            annotation_type = annotation[0]
            if annotation_type == "Line":
                cv2.line(clone, (annotation[1], annotation[2]), (annotation[3], annotation[4]), self.annotation_color, 2)
            elif annotation_type == "Rectangle":
                cv2.rectangle(clone, (annotation[1], annotation[2]), (annotation[3], annotation[4]), self.annotation_color, 2)
            elif annotation_type == "Circle":
                radius = int(np.sqrt((annotation[3] - annotation[1]) ** 2 + (annotation[4] - annotation[2]) ** 2))
                cv2.circle(clone, (annotation[1], annotation[2]), radius, self.annotation_color, 2)

        for text_annotation in self.text_annotations:
            text, x, y = text_annotation
            cv2.putText(clone, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, self.text_size, self.text_color, 2)

        self.display_image(clone)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()


# In[ ]:




