"""
Module for converting TTF fonts to C/C++ bitmap arrays."""

import os
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageFont, ImageDraw
from colossus_ltsm.settings import settings


@dataclass
class GlyphRenderCtx: # pylint: disable=too-many-instance-attributes
    """Lightweight bundle passed to glyph-render helpers."""
    draw: object
    char: str
    code: int
    glyph_w: int
    canvas_w: int
    canvas_h: int
    params: dict
    char_list: list
    debug: bool


class FontConverter(tk.Frame):  # pylint: disable=too-many-instance-attributes
    """Page for converting TTF fonts to C/C++ bitmap arrays."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._create_title()
        self._create_file_selection()
        self._create_options()
        self._create_buttons()
        self._create_log_panel()

    def _create_title(self):
        label = tk.Label(self, text="Font Converter", font=("Arial", 24))
        label.pack(pady=20)

    def _create_file_selection(self):
        self.ttf_path = tk.StringVar()
        tk.Button(self, text="Select TTF File",
                  command=self.select_file).pack(pady=5)
        tk.Entry(self, textvariable=self.ttf_path, width=60).pack(pady=5)

    def _create_options(self):
        options_frame = tk.Frame(self)
        options_frame.pack(pady=10)
        # Variables
        self.pixel_width = tk.IntVar(value=16)
        self.pixel_height = tk.IntVar(value=16)
        self.ascii_start = tk.IntVar(value=32)
        self.ascii_end = tk.IntVar(value=126)
        self.output_name = tk.StringVar(value="my_font_file")
        self.font_name = tk.StringVar(value="MyFontName")
        self.file_ext = tk.StringVar(value="hpp")
        self.array_style = tk.StringVar(value="cpp")
        self.addr_mode = tk.StringVar(value="horizontal")

        # Row 1 - Pixel size
        tk.Label(options_frame, text="Pixel Width:").grid(
            row=0, column=0, sticky="e")
        tk.Entry(options_frame, textvariable=self.pixel_width,
                 width=5).grid(row=0, column=1, padx=5)

        tk.Label(options_frame, text="Pixel Height:").grid(
            row=0, column=2, sticky="e")
        tk.Entry(options_frame, textvariable=self.pixel_height,
                 width=5).grid(row=0, column=3, padx=5)

        # Row 2 - ASCII range
        tk.Label(options_frame, text="ASCII Start:").grid(
            row=1, column=0, sticky="e")
        tk.Entry(options_frame, textvariable=self.ascii_start,
                 width=5).grid(row=1, column=1, padx=5)

        tk.Label(options_frame, text="ASCII End:").grid(
            row=1, column=2, sticky="e")
        tk.Entry(options_frame, textvariable=self.ascii_end,
                 width=5).grid(row=1, column=3, padx=5)

        # Row 3 - Names
        tk.Label(options_frame, text="Font Name:").grid(
            row=2, column=0, sticky="e")
        tk.Entry(options_frame, textvariable=self.font_name,
                 width=20).grid(row=2, column=1, padx=5)

        tk.Label(options_frame, text="Output File Name:").grid(
            row=2, column=2, sticky="e")
        tk.Entry(options_frame, textvariable=self.output_name,
                 width=20).grid(row=2, column=3, padx=5)

        # Row 4 - File & Array style
        tk.Label(options_frame, text="File Extension:").grid(
            row=3, column=0, sticky="e")
        tk.OptionMenu(options_frame, self.file_ext, "h", "hpp").grid(
            row=3, column=1, padx=5)

        tk.Label(options_frame, text="Array Style:").grid(
            row=3, column=2, sticky="e")
        tk.OptionMenu(options_frame, self.array_style, "c", "cpp").grid(
            row=3, column=3, padx=5)

        # Row 5 - Addressing mode
        tk.Label(options_frame, text="Addressing:").grid(
            row=4, column=0, sticky="e")
        tk.Radiobutton(options_frame, text="Horizontal",
                       variable=self.addr_mode,
                       value="horizontal").grid(row=4, column=1, sticky="w")
        tk.Radiobutton(options_frame, text="Vertical",
                       variable=self.addr_mode,
                       value="vertical").grid(row=4, column=2, sticky="w")

    def _create_buttons(self):
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Convert",
                  command=self.convert).pack(side="left", padx=10)

    def _create_log_panel(self):
        log_frame = tk.Frame(self)
        log_frame.pack(pady=5, padx=10, fill="x", expand=False)
        tk.Label(log_frame, text="Conversion Log:", anchor="w").pack(fill="x")
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")
        self.log_text = tk.Text(
            log_frame,
            height=8,
            width=70,
            state="disabled",
            yscrollcommand=scrollbar.set,
            bg="#1e1e1e",
            fg="#d4d4d4",
            font=("Courier", 9),
            relief="sunken",
            bd=1,
        )
        self.log_text.pack(side="left", fill="x", expand=True)
        scrollbar.config(command=self.log_text.yview)
        # Colour tags for log levels
        self.log_text.tag_config("info",    foreground="#d4d4d4")
        self.log_text.tag_config("warning", foreground="#f0a500")
        self.log_text.tag_config("success", foreground="#4ec94e")
        self.log_text.tag_config("error",   foreground="#f44747")

    def _log(self, message, level="info"):
        """Append a message to the on-screen log panel and stdout."""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n", level)
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        print(message)

    def _log_clear(self):
        """Clear the log panel before a new conversion run."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def select_file(self):
        """ Open a file dialog to select a TTF file."""
        input_dir = settings.getstr("Paths", "input_dir", fallback=str(os.path.expanduser("~")))
        if not input_dir or not os.path.isdir(input_dir):
            input_dir = str(os.path.expanduser("~"))
        file_path = filedialog.askopenfilename(
            title="Select TTF Font File",
            initialdir=input_dir,
            filetypes=[("TrueType Font", "*.ttf"), ("All Files", "*.*")]
        )
        if file_path:
            self.ttf_path.set(file_path)
        else:
            print("[cview] No file selected, open cancelled.")

    def convert(self):
        """Convert the selected TTF font to a C/C++ bitmap array."""
        if not self.ttf_path.get():
            messagebox.showerror("Error", "Please select a TTF file first.")
            return
        try:
            self._log_clear()
            params = self._get_params()
            if not params:
                messagebox.showerror(
                "Error", "Invalid parameters, conversion cancelled.")
                print("[cview] Invalid parameters, conversion cancelled.")
                return
            save_path = self._ask_save_path(
                params['output_name'], params['ext'])
            if not save_path:
                messagebox.showerror(
                "Error", "No save location selected, conversion cancelled.")
                print("[cview] No save location selected, conversion cancelled.")
                return
            if not self._validate_dimensions(params):
                messagebox.showerror(
                "Error", "Invalid dimensions for addressing mode, conversion cancelled. " \
                "Pixel width  must be a multiple of 8 for horizontal mode." \
                "Pixel height must be a multiple of 8 for vertical mode.")
                print("[cview] Invalid dimensions for addressing mode, conversion cancelled.")
                return
            font = ImageFont.truetype(self.ttf_path.get(), params['height'])
            font_name, font_style = font.getname()
            ascent, descent = font.getmetrics()
            self._log(f"Font: {font_name} {font_style} | "
                      f"Size: {params['width']}x{params['height']} | "
                      f"Ascent: {ascent}px  Descent: {descent}px")
            if settings.getbool("Debug", "debugOnOff", False):
                print(f"Font selected: {font_name} , {font_style}")
                print(f"Font metrics: ascent={ascent}px, descent={descent}px")

            control = [params['width'], params['height'], params['start'],
                       params['end'] - params['start']]
            glyph_blocks = self._generate_glyph_blocks(font, params)
            output = self._compose_output(control, glyph_blocks, params)
            Path(save_path).write_text(output, encoding="utf-8")
            self._log(f"Saved: {save_path}", "success")
            messagebox.showinfo("Success", f"Font converted:\n{save_path}")
            print(f"Font conversion successful. Output saved to: {save_path}")

        except Exception as e: # pylint: disable=broad-exception-caught
            self._log(f"Conversion failed: {e}", "error")
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
            if not font_name:
                font_name = "CustomFont"
            if not output_name:
                output_name = "font_output"
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
        except (tk.TclError, ValueError):
            messagebox.showerror("Error", "Invalid parameters.")
            return None


    def _ask_save_path(self, output_name, ext):
        """Ask user where to save output file."""
        output_dir = settings.getstr("Paths", "output_dir", fallback=str(os.path.expanduser("~")))
        if not output_dir or not os.path.isdir(output_dir):
            output_dir = str(os.path.expanduser("~"))
        return filedialog.asksaveasfilename(
            title="Save Font Array",
            initialdir=output_dir,
            defaultextension=f".{ext}",
            initialfile=f"{output_name}.{ext}",
            filetypes=[("Header files", f"*.{ext}")]
        )

    def _validate_dimensions(self, params):
        """Validate width/height multiples for addressing mode."""
        width = params.get("width", 0)
        height = params.get("height", 0)

        if width <= 0 or height <= 0:
            return False
        if params["addr_mode"] == "horizontal" and width % 8 != 0:
            return False
        if params["addr_mode"] == "vertical" and height % 8 != 0:
            return False
        return True

    def _calculate_baseline(self, font, canvas_h, ascii_start=32, ascii_end=126):
        """Calculate baseline_y by measuring the actual ink extents of all glyphs
        in the ASCII range and fitting the baseline so nothing is clipped at
        either the top or the bottom of the canvas.
        """
        max_above, max_below = self._scan_ink_extents(font, ascii_start, ascii_end)
        total_ink_h = max_above + max_below

        if total_ink_h == 0:
            # No ink found — fall back to metric-based calculation
            ascent, descent = font.getmetrics()
            font_cell_h = ascent + descent
            return round(ascent * canvas_h / font_cell_h) if font_cell_h > 0 else canvas_h - 1

        if total_ink_h <= canvas_h:
            spare = canvas_h - total_ink_h
            baseline_y = spare // 2 + max_above
        else:
            baseline_y = max_above - (total_ink_h - canvas_h) // 2
            self._log(
                f"Warning: font ink height ({total_ink_h}px) exceeds canvas "
                f"({canvas_h}px). Some clipping may be unavoidable — "
                f"try a smaller font size or larger cell height.",
                "warning"
            )

        if settings.getbool("Debug", "debugOnOff", False):
            print(f"  Baseline calc: max_above={max_above}, max_below={max_below}, "
                  f"total_ink={total_ink_h}, canvas_h={canvas_h}, "
                  f"baseline_y={baseline_y}")

        return baseline_y

    def _scan_ink_extents(self, font, ascii_start, ascii_end):
        """Return (max_above, max_below) ink extents across the ASCII range."""
        max_above = 0
        max_below = 0
        for code in range(ascii_start, ascii_end + 1):
            try:
                bbox = font.getbbox(chr(code), anchor="ls")
                if bbox is None:
                    continue
                # bbox format: (left, top, right, bottom)
                max_above = max(max_above, -bbox[1])   # -top   (distance above baseline)
                max_below = max(max_below, bbox[3])    # bottom (distance below baseline)
            except (ValueError, OSError):
                continue
        return max_above, max_below

    def _generate_glyph_blocks(self, font, params): # pylint: disable=too-many-locals
        """Generate glyph blocks with baseline anchoring, with horizontal fit protection."""
        glyph_blocks = []
        canvas_w = params['width']
        canvas_h = params['height']
        baseline_y = self._calculate_baseline(
            font, canvas_h, params['start'], params['end']
        )
        debug = settings.getbool("Debug", "debugOnOff", False)
        scaled_chars = []
        centred_chars = []

        for code in range(params['start'], params['end'] + 1):
            char = chr(code)
            img = Image.new("1", (canvas_w, canvas_h), 0)
            draw = ImageDraw.Draw(img)
            try:
                bbox = font.getbbox(char, anchor="ls")
                if bbox is None:
                    glyph_blocks.append((char, self._extract_glyph_bytes(img, params)))
                    continue
                glyph_w = bbox[2] - bbox[0]
                ctx = GlyphRenderCtx(draw, char, code, glyph_w,
                                     canvas_w, canvas_h, params,
                                     scaled_chars if glyph_w > canvas_w else centred_chars,
                                     debug)
                if glyph_w > canvas_w:
                    self._render_scaled_glyph(ctx)
                else:
                    self._render_centered_glyph(ctx, font, baseline_y)
            except (OSError, ValueError) as err:
                if debug:
                    print(f"  Char '{char}' fallback render: {err}")
                draw.text((0, 0), char, fill=1, font=font)

            glyph_blocks.append((char, self._extract_glyph_bytes(img, params)))

        self._report_glyph_stats(canvas_w, scaled_chars, centred_chars, debug)
        return glyph_blocks

    def _render_scaled_glyph(self, ctx: GlyphRenderCtx):
        """Render a glyph that is wider than the cell by scaling the font down."""
        scale = ctx.canvas_w / ctx.glyph_w
        scaled_size = max(1, int(ctx.params['height'] * scale))
        scaled_font = ImageFont.truetype(self.ttf_path.get(), scaled_size)
        baseline = self._calculate_baseline(
            scaled_font, ctx.canvas_h, ctx.params['start'], ctx.params['end']
        )
        ctx.draw.text((0, baseline), ctx.char, fill=1, font=scaled_font, anchor="ls")
        ctx.char_list.append(f"'{ctx.char}'(0x{ctx.code:02X})")
        if ctx.debug:
            print(
                f"Scaled '{ctx.char}' (0x{ctx.code:02X}) "
                f"glyph_w={ctx.glyph_w} > canvas_w={ctx.canvas_w}, "
                f"new size={scaled_size}"
            )

    def _render_centered_glyph(self, ctx: GlyphRenderCtx, font, baseline_y):
        """Render a glyph centred horizontally within the cell."""
        x_offset = (ctx.canvas_w - ctx.glyph_w) // 2
        if x_offset > 0:
            ctx.char_list.append(f"'{ctx.char}'(0x{ctx.code:02X})")
        ctx.draw.text((x_offset, baseline_y), ctx.char, fill=1, font=font, anchor="ls")
        if ctx.debug and ctx.glyph_w > ctx.canvas_w * 0.9:
            print(
                f"Char '{ctx.char}' (0x{ctx.code:02X}) "
                f"glyph_w={ctx.glyph_w}, canvas_w={ctx.canvas_w} (tight fit)"
            )

    def _report_glyph_stats(self, canvas_w, scaled_chars, centred_chars, debug):
        if scaled_chars:
            self._log(
                f"Width-scaled {len(scaled_chars)} glyph(s) to fit {canvas_w}px cell: "
                f"{', '.join(scaled_chars)}",
                "warning"
            )
            self._log(
                "Tip: increase Pixel Width or reduce font size to avoid scaling.",
                "warning"
            )
        else:
            self._log(
                "All glyphs fit within the cell width — no scaling needed.",
                "info"
            )
        if debug and centred_chars:
            preview = ", ".join(centred_chars[:10])
            if len(centred_chars) > 10:
                preview += " ..."

            self._log(
                f"Horizontally centred {len(centred_chars)} glyph(s): {preview}",
                "info"
            )

    def _extract_glyph_bytes(self, img, params):
        """Extract glyph bytes from image according to addressing mode."""
        width  = params['width']
        height = params['height']
        if params['addr_mode'] == "vertical":
            return self._pack_vertical(img, width, height)
        return self._pack_horizontal(img, width, height)

    @staticmethod
    def _pack_vertical(img, width, height):
        """Pack pixels column-major, 8 rows per byte (vertical addressing)."""
        glyph_bytes = []
        for y_block in range(0, height, 8):
            for x in range(width):
                byte_val = 0
                for bit in range(8):
                    yy = y_block + bit
                    if yy < height:
                        pixel = img.getpixel((x, yy))
                        byte_val |= (1 if pixel else 0) << bit
                glyph_bytes.append(byte_val)
        return glyph_bytes

    @staticmethod
    def _pack_horizontal(img, width, height):
        """Pack pixels row-major, 8 columns per byte (horizontal addressing)."""
        glyph_bytes = []
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
            f"// Generated by Colossus_LTSM\n"
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
    print("[cview] This is a module, not a standalone script.")
else:
    print("[cview] Font Convert module loaded.")
