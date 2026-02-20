""" Font Viewer module for displaying font data from C++ header files.
This module provides a GUI to visualize font data extracted from header files,
allowing users to see the glyphs and their addressing modes.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import re
import math
from PIL import Image
from colossus_ltsm.settings import settings


class FontViewer(tk.Frame):
    """ Page for viewing font data from C++ header files."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.addr_mode_var = tk.StringVar(value="horizontal")

        # Addressing mode selection (centered row)
        addr_frame = tk.Frame(self)
        addr_frame.grid(row=0, column=0, columnspan=3, pady=5)
        tk.Label(addr_frame, text="Addressing:").pack(side="left", padx=5)
        tk.Radiobutton(addr_frame, text="Horizontal", variable=self.addr_mode_var,
                       value="horizontal").pack(side="left", padx=5)
        tk.Radiobutton(addr_frame, text="Vertical", variable=self.addr_mode_var,
                       value="vertical").pack(side="left", padx=5)
        # Load from settings
        self.scale = settings.getint("Display", "scale", 4)
        self.cols = settings.getint("Display", "cols", 16)
        # Open button
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=8)

        tk.Button(
            btn_frame,
            text="Open header Font File",
            command=self.open_file
        ).pack(side="left", padx=5)

        self.export_btn = tk.Button(
            btn_frame,
            text="Export PNG",
            command=self.export_png,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5)
        # Show current settings for scale and columns
        self.info_label = tk.Label(
            self, text=f"Scale: {self.scale}, Cols: {self.cols}")
        self.info_label.grid(row=2, column=0, columnspan=3, pady=4)
        # Container for canvas + scroll bars
        container = tk.Frame(self)
        container.grid(row=3, column=0, columnspan=3, sticky="nsew")
        # Canvas
        self.canvas = tk.Canvas(container, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        # Scroll bars
        self.v_scroll = tk.Scrollbar(
            container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(
            container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        # Link canvas <-> scroll bars
        self.canvas.configure(xscrollcommand=self.h_scroll.set,
                              yscrollcommand=self.v_scroll.set)
        # Expand properly
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # Expand the whole widget in parent
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Current font data.
        self.current_font_bytes = None

    def open_file(self):
        """ Open a file dialog to select a C or C++ header file"""
        self.export_btn.config(state="disabled")
        self.current_font_bytes = None
        path = filedialog.askopenfilename(
            filetypes=[("C++ Header", "*.hpp"), ("C++ Header", "*.h")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            # 1. Strip comments
            data = re.sub(r"//.*", "", data)
            data = re.sub(r"/\*.*?\*/", "", data, flags=re.S)
            # 2. Extract bytes inside { ... }
            match = re.search(r"\{([^}]*)\}", data, re.S)
            if not match:
                messagebox.showerror("Error", "No font data found in file.")
                self.canvas.delete("all")
                return
            raw_data = match.group(1)
            # 3. Normalize whitespace
            raw_data = raw_data.replace("\n", " ").replace("\r", " ").strip()
            # 4. Parse hex values
            raw_bytes = raw_data.split(",")
            font_bytes = [int(b.strip(), 16) for b in raw_bytes if b.strip()]
            # 5. Sanity check
            if len(font_bytes) >= 4:
                x_size = font_bytes[0]
                y_size = font_bytes[1]
                first_char = font_bytes[2]
                last_char = first_char + font_bytes[3]
                num_chars = last_char - first_char + 1
                if self.addr_mode_var.get() == "horizontal":
                    bytes_per_char = math.ceil(x_size / 8) * y_size
                else:
                    bytes_per_char = math.ceil(y_size / 8) * x_size
                expected = 4 + num_chars * bytes_per_char
                if len(font_bytes) != expected:
                    messagebox.showwarning(
                        "Warning",
                        f"Byte count mismatch.\n"
                        f"Expected {expected}, got {len(font_bytes)}"
                    )
                self.current_font_bytes = font_bytes
                self.render_font(font_bytes)
                self.export_btn.config(state="normal")
            else:
                messagebox.showerror("Error", "Invalid font data format.")
                self.canvas.delete("all")
                return
        except Exception as e:
            messagebox.showerror("Error: open_file", str(e))

    def render_font(self, font_bytes):
        """Render the font data on the canvas."""
        self.canvas.delete("all")

        # Control bytes
        x_size = font_bytes[0]
        y_size = font_bytes[1]
        ascii_offset = font_bytes[2]
        last_offset = font_bytes[3]
        num_chars = last_offset + 1

        if self.addr_mode_var.get() == "horizontal":
            bytes_per_char = math.ceil(x_size / 8) * y_size
        else:
            bytes_per_char = math.ceil(y_size / 8) * x_size

        # Loop through characters
        for idx in range(num_chars):
            char_code = ascii_offset + idx
            start = 4 + idx * bytes_per_char
            end = 4 + (idx + 1) * bytes_per_char
            glyph_data = font_bytes[start:end]

            col = idx % self.cols
            row = idx // self.cols
            x_offset = col * (x_size * self.scale + 20)
            y_offset = row * (y_size * self.scale + 30)

            self._draw_char_label(char_code, x_size, x_offset, y_offset)

            if len(glyph_data) < bytes_per_char:
                print("Warning: glyph too short, skipping")
                continue

            if self.addr_mode_var.get() == "horizontal":
                self._render_horizontal(
                    glyph_data, x_size, y_size, x_offset, y_offset)
            else:
                self._render_vertical(glyph_data, x_size,
                                      y_size, x_offset, y_offset)

        # Track max extents for scrolling
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _draw_char_label(self, char_code, x_size, x_offset, y_offset):
        self.canvas.create_text(
            x_offset + (x_size * self.scale) // 2,
            y_offset - 5,
            text=chr(char_code)
        )

    def _render_horizontal(self, glyph_data, x_size, y_size, x_offset, y_offset):
        for y in range(y_size):
            for byte_index in range(x_size // 8):
                idx = y * (x_size // 8) + byte_index
                if idx >= len(glyph_data):
                    continue
                byte_val = glyph_data[idx]
                for bit in range(8):
                    if (byte_val >> (7 - bit)) & 1:
                        px = x_offset + (byte_index * 8 + bit) * self.scale
                        py = y_offset + y * self.scale
                        self.canvas.create_rectangle(px, py,
                                                     px + self.scale,
                                                     py + self.scale,
                                                     fill="black")

    def _render_vertical(self, glyph_data, x_size, y_size, x_offset, y_offset):
        if y_size % 8 != 0:
            print("Error: render_font: vertical fonts "
                  "must have height divisible by 8")
            return
        bytes_per_col = y_size // 8
        for x in range(x_size):
            for row_block in range(bytes_per_col):
                idx = (row_block * x_size) + x
                if idx >= len(glyph_data):
                    continue
                byte_val = glyph_data[idx]
                for bit in range(8):
                    if byte_val & (1 << bit):
                        px = x_offset + x * self.scale
                        py = y_offset + (row_block * 8 + bit) * self.scale
                        self.canvas.create_rectangle(
                            px, py, px + self.scale,
                            py + self.scale, fill="black")

    def export_png(self):
        """Export currently loaded font to PNG image."""
        if not self.current_font_bytes:
            messagebox.showerror("Error", "No font loaded.")
            return
        BG_COLOR = (0, 0, 0) # Black
        GLYPH_COLOR = (0, 120, 255) # Soft Blue 
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")]
        )

        if not path:
            print("Export path not valid, export cancelled.")
            return

        font_bytes = self.current_font_bytes
        x_size = font_bytes[0]
        y_size = font_bytes[1]
        ascii_offset = font_bytes[2]
        last_offset = font_bytes[3]
        num_chars = last_offset + 1

        if self.addr_mode_var.get() == "horizontal":
            bytes_per_char = math.ceil(x_size / 8) * y_size
        else:
            bytes_per_char = math.ceil(y_size / 8) * x_size

        cols = self.cols
        rows = math.ceil(num_chars / cols)
        img_width = cols * x_size
        img_height = rows * y_size
        image = Image.new("RGB", (img_width, img_height), BG_COLOR)
        pixels = image.load()

        for idx in range(num_chars):
            start = 4 + idx * bytes_per_char
            end = 4 + (idx + 1) * bytes_per_char
            glyph_data = font_bytes[start:end]
            col = idx % cols
            row = idx // cols
            x_offset = col * x_size
            y_offset = row * y_size

            if self.addr_mode_var.get() == "horizontal":
                for y in range(y_size):
                    for byte_index in range(x_size // 8):
                        i = y * (x_size // 8) + byte_index
                        if i >= len(glyph_data):
                            continue
                        byte_val = glyph_data[i]
                        for bit in range(8):
                            if (byte_val >> (7 - bit)) & 1:
                                px = x_offset + byte_index * 8 + bit
                                py = y_offset + y
                                pixels[px, py] = (0, 120, 255)
            else:
                bytes_per_col = y_size // 8
                for x in range(x_size):
                    for row_block in range(bytes_per_col):
                        i = row_block * x_size + x
                        if i >= len(glyph_data):
                            continue
                        byte_val = glyph_data[i]
                        for bit in range(8):
                            if byte_val & (1 << bit):
                                px = x_offset + x
                                py = y_offset + row_block * 8 + bit
                                pixels[px, py] = GLYPH_COLOR

        image.save(path, "PNG")
        messagebox.showinfo("Success", f"PNG exported:\n{path}")

if __name__ == "__main__":
    print("This is a module, not a standalone script.")
else:
    print("Font Viewer module loaded.")
