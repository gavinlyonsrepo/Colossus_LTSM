"""
Module for converting TTF fonts to C/C++ bitmap arrays."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageFont, ImageDraw
from colossus_ltsm.settings import settings


class FontConverter(tk.Frame):
    """ Page for converting TTF fonts to C/C++ bitmap arrays.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        label = tk.Label(self, text="Font Converter", font=("Arial", 24))
        label.pack(pady=20)
        # Load from settings
        if settings.getbool("Debug", "debugOnOff", False):
            print("Debug enabled")
        # File selection
        self.ttf_path = tk.StringVar()
        tk.Button(self, text="Select TTF File",
                  command=self.select_file).pack(pady=5)
        tk.Entry(self, textvariable=self.ttf_path, width=60).pack(pady=5)
        # Options
        options_frame = tk.Frame(self)
        options_frame.pack(pady=10)
        self.pixel_width = tk.IntVar(value=16)
        self.pixel_height = tk.IntVar(value=16)
        self.ascii_start = tk.IntVar(value=32)
        self.ascii_end = tk.IntVar(value=126)
        self.output_name = tk.StringVar(value="my_font_file")
        self.font_name = tk.StringVar(value="MyFontName")
        self.file_ext = tk.StringVar(value="hpp")
        self.array_style = tk.StringVar(value="cpp")
        self.addr_mode = tk.StringVar(
            value="horizontal")  # horizontal / vertical
        # Row 1
        tk.Label(options_frame,
                 text="Pixel Width:").grid(row=0, column=0, sticky="e")
        tk.Entry(options_frame,
                 textvariable=self.pixel_width,
                 width=5).grid(row=0, column=1, padx=5)
        tk.Label(options_frame, text="Pixel Height:").grid(row=0,
                                                           column=2, sticky="e")
        tk.Entry(options_frame, textvariable=self.pixel_height,
                 width=5).grid(row=0, column=3, padx=5)
        # Row 2
        tk.Label(options_frame,
                 text="ASCII Start:").grid(row=1, column=0, sticky="e")
        tk.Entry(options_frame,
                 textvariable=self.ascii_start, width=5).grid(row=1,
                                                              column=1, padx=5)
        tk.Label(options_frame,
                 text="ASCII End:").grid(row=1, column=2, sticky="e")
        tk.Entry(options_frame,
                 textvariable=self.ascii_end, width=5).grid(row=1,
                                                            column=3, padx=5)
        # Row 3
        tk.Label(options_frame,
                 text="Font Name:").grid(row=2,
                                         column=0, sticky="e")
        tk.Entry(options_frame,
                 textvariable=self.font_name,
                 width=20).grid(row=2, column=1, padx=5)
        tk.Label(options_frame, text="Output File Name:").grid(
            row=2, column=2, sticky="e")
        tk.Entry(options_frame, textvariable=self.output_name,
                 width=20).grid(row=2, column=3, padx=5)
        # Row 4
        tk.Label(options_frame, text="File Extension:").grid(
            row=3, column=0, sticky="e")
        tk.OptionMenu(options_frame, self.file_ext, "h",
                      "hpp").grid(row=3, column=1, padx=5)
        tk.Label(options_frame, text="Array Style:").grid(
            row=3, column=2, sticky="e")
        tk.OptionMenu(options_frame, self.array_style, "c",
                      "cpp").grid(row=3, column=3, padx=5)
        # Row 5 (addressing mode)
        tk.Label(options_frame, text="Addressing:").grid(
            row=4, column=0, sticky="e")
        tk.Radiobutton(options_frame, text="Horizontal", variable=self.addr_mode,
                       value="horizontal").grid(row=4, column=1, sticky="w")
        tk.Radiobutton(options_frame, text="Vertical", variable=self.addr_mode,
                       value="vertical").grid(row=4, column=2, sticky="w")
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Convert", command=self.convert).pack(
            side="left", padx=10)

    def select_file(self):
        """ Open a file dialog to select a TTF file."""
        path = filedialog.askopenfilename(
            filetypes=[("TrueType Font", "*.ttf"), ("All Files", "*.*")]
        )
        if path:
            self.ttf_path.set(path)

    def convert(self):
        """Convert the selected TTF font to a C/C++ bitmap array."""
        if not self.ttf_path.get():
            messagebox.showerror("Error", "Please select a TTF file first.")
            return
        try:
            params = self._get_params()
            if not params:
                return
            save_path = self._ask_save_path(
                params['output_name'], params['ext'])
            if not save_path:
                return
            if not self._validate_dimensions(params):
                return
            font = ImageFont.truetype(self.ttf_path.get(), params['height'])
            if settings.getbool("Debug", "debugOnOff", False):
                fontName, fontStyle = font.getname()
                ascent, descent = font.getmetrics()
                print(f"Font selected: {fontName} , {fontStyle}")
                print (f"Font metrics: ascent={ascent}px, descent={descent}px")

            control = [params['width'], params['height'], params['start'],
                       params['end'] - params['start']]
            glyph_blocks = self._generate_glyph_blocks(font, params)
            output = self._compose_output(control, glyph_blocks, params)
            Path(save_path).write_text(output, encoding="utf-8")
            messagebox.showinfo("Success", f"Font converted:\n{save_path}")
            print(f"Font conversion successful. Output saved to: {save_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed:\n{e}")

    def _get_params(self):
        """Get and validate parameters from UI."""
        try:
            width = self.pixel_width.get()
            height = self.pixel_height.get()
            start = self.ascii_start.get()
            end = self.ascii_end.get()
            font_name = self.font_name.get()
            output_name = self.output_name.get()
            ext = self.file_ext.get()
            array_style = self.array_style.get()
            addr_mode = self.addr_mode.get()
            return {
                'width': width,
                'height': height,
                'start': start,
                'end': end,
                'font_name': font_name,
                'output_name': output_name,
                'ext': ext,
                'array_style': array_style,
                'addr_mode': addr_mode
            }
        except Exception:
            messagebox.showerror("Error", "Invalid parameters.")
            return None

    def _ask_save_path(self, output_name, ext):
        """Ask user where to save output file."""
        return filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            initialfile=f"{output_name}.{ext}",
            filetypes=[("Header files", f"*.{ext}")]
        )

    def _validate_dimensions(self, params):
        """Validate width/height multiples for addressing mode."""
        if params['addr_mode'] == "horizontal" and params['width'] % 8 != 0:
            messagebox.showerror(
                "Error", "Pixel width must be a multiple of 8 for horizontal mode.")
            return False
        if params['addr_mode'] == "vertical" and params['height'] % 8 != 0:
            messagebox.showerror(
                "Error", "Pixel height must be a multiple of 8 for vertical mode.")
            return False
        return True

    def _generate_glyph_blocks(self, font, params):
        """Generate glyph blocks with middle-middle (mm) anchoring for vertical centering."""
        glyph_blocks = []
        canvas_w = params['width']
        canvas_h = params['height']
        center_x = canvas_w // 2
        center_y = canvas_h // 2
        for code in range(params['start'], params['end'] + 1):
            char = chr(code)
            img = Image.new("1", (canvas_w, canvas_h), 0)
            draw = ImageDraw.Draw(img)
            try:
                bbox = font.getbbox(char)
                if bbox is None:
                    # No ink (e.g. space, control char) → leave blank
                    glyph_bytes = self._extract_glyph_bytes(img, params)
                    glyph_blocks.append((char, glyph_bytes))
                    continue
                # With anchor="mm", Pillow centers the glyph's visual middle at (center_x, center_y)
                # This automatically handles most ascender/descender balancing nicely
                draw.text((center_x, center_y), char, fill=1, font=font, anchor="mm")
            except Exception:
                draw.text((0, 0), char, fill=1, font=font)

            glyph_bytes = self._extract_glyph_bytes(img, params)
            glyph_blocks.append((char, glyph_bytes))

        return glyph_blocks

    def _extract_glyph_bytes(self, img, params):
        """Extract glyph bytes from image according to addressing mode."""
        width, height, addr_mode =params['width'], params['height'], params['addr_mode']
        glyph_bytes = []
        if addr_mode == "vertical":
            for y_block in range(0, height, 8):
                for x in range(width):
                    byte_val = 0
                    for bit in range(8):
                        yy = y_block + bit
                        if yy < height:
                            pixel = img.getpixel((x, yy))
                            byte_val |= (1 if pixel else 0) << bit
                    glyph_bytes.append(byte_val)
        else:
            for y in range(height):
                for x_block in range(0, width, 8):
                    byte_val = 0
                    for bit in range(8):
                        xx = x_block + bit
                        pixel = img.getpixel((xx, y)) if xx < width else 0
                        byte_val = (byte_val << 1) | (1 if pixel else 0)
                    glyph_bytes.append(byte_val)
        
        return glyph_bytes

    def _compose_output(self, control, glyph_blocks, params):
        """Compose the output string for the font array."""
        lines = []
        control_line = ",".join(f"0x{b:02X}" for b in control) + ","
        lines.append(control_line)
        for char, glyph_bytes in glyph_blocks:
            chunk = ",".join(f"0x{b:02X}" for b in glyph_bytes)
            if 32 <= ord(char) <= 126:
                line = chunk + ", // '" + char + "'"
            else:
                line = chunk
            lines.append(line)
        header = (
            f"// Auto-generated monospaced bitmap font (C++/C array)\n"
            f"// Format: [width, height, ASCII offset, last char- ASCII offset]\n"
            f"// Data layout: {params['addr_mode']}-addressed byte rows per glyph\n"
            f"// Generated by Colossus\n"
            f"// Generated font: {params['font_name']}\n"
            f"// Size: {params['width']}x{params['height']}\n"
            f"// ASCII range: 0x{params['start']:02X} → 0x{params['end']:02X}\n"
            f"// Total size: {len(control) + sum(len(g) for _, g in glyph_blocks)} bytes \n"
        )
        if params['array_style'] == "cpp":
            array_header = (
                f"static const std::array<uint8_t, "
                f"{len(control) + sum(len(g) for _, g in glyph_blocks)}>"
                f" {params['font_name']} = {{"
            )
        else:
            array_header = (
                f"static const unsigned char {params['output_name']}["
                f"{len(control) + sum(len(g) for _, g in glyph_blocks)}] = {{"
            )
        footer = "};\n"
        return header + "\n" + array_header + "\n" + "\n".join(lines) + "\n" + footer


if __name__ == "__main__":
    print("This is a module, not a standalone script.")
else:
    print("Font Convert module loaded.")
