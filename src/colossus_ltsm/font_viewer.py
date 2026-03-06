""" Font Viewer module for displaying font data from C++ header files.
This module provides a GUI to visualize font data extracted from header files,
allowing users to see the glyphs and their addressing modes.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import math
from dataclasses import dataclass
from PIL import Image
from colossus_ltsm.settings import settings

@dataclass
class GlyphRenderContext:
    """ Context for rendering a single glyph, used in PNG export."""
    pixels: any
    x_size: int
    y_size: int
    x_offset: int
    y_offset: int
    color: tuple

@dataclass
class FontMeta:
    """ Metadata about the font, extracted from the first 4 bytes of the font data."""
    x_size: int
    y_size: int
    ascii_offset: int
    last_offset: int

class FontViewer(tk.Frame): # pylint: disable=too-many-instance-attributes
    """ Page for viewing font data from C++ header files."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.addr_mode_var = tk.StringVar(value="horizontal")
        self.glyph_color = settings.getstr("Display", "glyph_color", "#0078FF")
        self.background_color = settings.getstr("Display", "background_color", "#000000")

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
        self.canvas = tk.Canvas(container, bg=self.background_color)
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
        """ Open a C/C++ header file, parse font data, and render it on the canvas."""
        self.export_btn.config(state="disabled")
        self.current_font_bytes = None
        file_path = self._select_file()
        if not file_path:
            print("[fview] No file selected, open cancelled.")
            return
        try:
            font_bytes = self._parse_font_file(file_path)
            self._validate_and_render(font_bytes)
        except Exception as e:  # pylint: disable=broad-exception-caught
            messagebox.showerror("Error: open_file", str(e))
            print(f"[fview] Error opening file: {e}")

    def _select_file(self):
        """ Open a file dialog to select a C/C++ header file,
        starting in the output_dir from settings."""
        output_dir = settings.getstr(
            "Paths", "output_dir", fallback=str(os.path.expanduser("~"))
        )
        if not output_dir or not os.path.isdir(output_dir):
            output_dir = str(os.path.expanduser("~"))
        return filedialog.askopenfilename(
            title="Open File",
            initialdir=output_dir,
            filetypes=[("C++ Header", "*.hpp"), ("C++ Header", "*.h")],
        )

    def _parse_font_file(self, file_path):
        """ Parse the selected header file to extract font byte data."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()
        data = re.sub(r"//.*", "", data)
        data = re.sub(r"/\*.*?\*/", "", data, flags=re.S)
        match = re.search(r"\{([^}]*)\}", data, re.S)
        if not match:
            raise ValueError("No font data found in file.")
        raw_data = match.group(1)
        raw_data = raw_data.replace("\n", " ").replace("\r", " ").strip()
        raw_bytes = raw_data.split(",")
        return [int(b.strip(), 16) for b in raw_bytes if b.strip()]

    def _validate_and_render(self, font_bytes):
        if len(font_bytes) < 4:
            messagebox.showerror("Error", "Invalid font data format.")
            self.canvas.delete("all")
            return
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
                f"Byte count mismatch.\nExpected {expected}, got {len(font_bytes)}",
            )
        self.current_font_bytes = font_bytes
        self.render_font(font_bytes)
        self.export_btn.config(state="normal")

    def render_font(self, font_bytes):
        """Render the font data on the canvas."""
        self.canvas.delete("all")
        meta = FontMeta(
            x_size=font_bytes[0],
            y_size=font_bytes[1],
            ascii_offset=font_bytes[2],
            last_offset=font_bytes[3],
        )
        num_chars = meta.last_offset + 1
        bytes_per_char = self._calc_bytes_per_char(meta.x_size, meta.y_size)
        # Loop through characters
        for idx in range(num_chars):
            char_code = meta.ascii_offset + idx
            start = 4 + idx * bytes_per_char
            end = 4 + (idx + 1) * bytes_per_char
            glyph_data = font_bytes[start:end]
            col = idx % self.cols
            row = idx // self.cols
            x_offset = col * (meta.x_size * self.scale + 20)
            y_offset = row * (meta.y_size * self.scale + 30)
            self._draw_char_label(char_code, meta.x_size, x_offset, y_offset)
            if len(glyph_data) < bytes_per_char:
                print("[fview] Warning: glyph too short, skipping")
                continue
            if self.addr_mode_var.get() == "horizontal":
                self._render_horizontal(glyph_data, x_offset, y_offset)
            else:
                self._render_vertical(glyph_data, x_offset, y_offset)

        # Track max extents for scrolling
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _draw_char_label(self, char_code, x_size, x_offset, y_offset):
        self.canvas.create_text(
            x_offset + (x_size * self.scale) // 2,
            y_offset - 5,
            text=chr(char_code)
        )

    def _render_horizontal(self, glyph_data, x_offset, y_offset):
        x_size = self.current_font_bytes[0]
        y_size = self.current_font_bytes[1]
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
                                                     fill=self.glyph_color,
                                                     outline="")

    def _render_vertical(self, glyph_data, x_offset, y_offset):
        x_size = self.current_font_bytes[0]
        y_size = self.current_font_bytes[1]
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
                            py + self.scale, fill=self.glyph_color,
                            outline="")

    def export_png(self):
        """Export currently loaded font to PNG image."""
        if not self.current_font_bytes:
            messagebox.showerror("Error", "No font loaded.")
            return
        path = self._select_export_path()
        if not path:
            print("[fview] Export path not valid, export cancelled.")
            return
        font_bytes = self.current_font_bytes
        image = self._create_font_image(font_bytes)
        image.save(path, "PNG")
        messagebox.showinfo("Success", f"PNG exported:\n{path}")

    def _select_export_path(self):
        output_dir = settings.getstr(
            "Paths", "output_dir", fallback=str(os.path.expanduser("~"))
        )
        if not output_dir or not os.path.isdir(output_dir):
            output_dir = str(os.path.expanduser("~"))
        return filedialog.asksaveasfilename(
            title="Export PNG",
            initialdir=output_dir,
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")]
        )

    def _create_font_image(self, font_bytes):
        background_color = self._hex_to_rgb(self.background_color)
        x_size = font_bytes[0]
        y_size = font_bytes[1]
        last_offset = font_bytes[3]
        num_chars = last_offset + 1
        bytes_per_char = self._calc_bytes_per_char(x_size, y_size)
        cols = self.cols
        rows = math.ceil(num_chars / cols)
        img_width = cols * x_size
        img_height = rows * y_size
        image = Image.new("RGB", (img_width, img_height), background_color)
        pixels = image.load()
        for idx in range(num_chars):
            self._render_glyph(idx, font_bytes, bytes_per_char, pixels)
        return image

    def _calc_bytes_per_char(self, x_size, y_size):
        if self.addr_mode_var.get() == "horizontal":
            return math.ceil(x_size / 8) * y_size
        return math.ceil(y_size / 8) * x_size

    def _render_glyph(self, idx, font_bytes, bytes_per_char, pixels):

        glyph_color = self._hex_to_rgb(self.glyph_color) # blue
        start = 4 + idx * bytes_per_char
        end = start + bytes_per_char
        glyph_data = font_bytes[start:end]
        x_size = font_bytes[0]
        y_size = font_bytes[1]
        col = idx % self.cols
        row = idx // self.cols
        ctx = GlyphRenderContext(
            pixels=pixels,
            x_size=x_size,
            y_size=y_size,
            x_offset=col * x_size,
            y_offset=row * y_size,
            color=glyph_color,
        )
        if self.addr_mode_var.get() == "horizontal":
            self._draw_horizontal(glyph_data, ctx)
        else:
            self._draw_vertical(glyph_data, ctx)

    def _draw_horizontal(self, glyph_data, ctx):
        row_bytes = ctx.x_size // 8
        for y in range(ctx.y_size):
            for byte_index in range(row_bytes):
                i = y * row_bytes + byte_index
                if i >= len(glyph_data):
                    continue
                byte_val = glyph_data[i]
                for bit in range(8):
                    if (byte_val >> (7 - bit)) & 1:
                        px = ctx.x_offset + byte_index * 8 + bit
                        py = ctx.y_offset + y
                        ctx.pixels[px, py] = ctx.color

    def _draw_vertical(self, glyph_data, ctx):
        bytes_per_col = ctx.y_size // 8
        for x in range(ctx.x_size):
            for row_block in range(bytes_per_col):
                i = row_block * ctx.x_size + x
                if i >= len(glyph_data):
                    continue
                byte_val = glyph_data[i]
                for bit in range(8):
                    if byte_val & (1 << bit):
                        px = ctx.x_offset + x
                        py = ctx.y_offset + row_block * 8 + bit
                        ctx.pixels[px, py] = ctx.color

    def _hex_to_rgb(self, hex_color):
        """ Convert hex color string to RGB tuple, Pillow needs RGB tuples"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


if __name__ == "__main__":
    print("[fview] This is a module, not a standalone script.")
else:
    print("[fview] Font Viewer module loaded.")
