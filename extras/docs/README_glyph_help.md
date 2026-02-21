# Glyph Rendering — Baseline Alignment & Width Fitting

## How glyphs are placed in the bitmap cell

Each character is rendered into a fixed-size cell defined by the **Pixel Width** and
**Pixel Height** values you enter. The converter measures the actual ink extents of
every glyph in your ASCII range and positions the baseline so all characters fit
within the cell without clipping at the top or bottom.

If in settings if debug is on , verbose output will show the font's ascent, descent, and line gap values, as well as the actual ink extents of each character. This can be helpful for understanding how the converter is positioning the glyphs. In addtion messages about width scaling and clipping will be shown in the conversion log if they occur. See below for details.

## Conversion Log messages

The **Conversion Log** panel at the bottom of the Font Converter page reports anything
that affected the output. Messages in amber are warnings that may impact quality.

### Width scaling (amber)

```bash
Width-scaled 2 glyph(s) to fit 24px cell: 'W'(0x57), '@'(0x40)
Tip: increase Pixel Width or reduce font size to avoid scaling.
```

Some glyphs (commonly **W**, **M**, **@**, **%**) are wider than the cell at certain
sizes. The converter scales those characters down individually so they fit, but they
will appear slightly smaller than their neighbours. To avoid this, increase **Pixel
Width** (must stay a multiple of 8 for horizontal mode) or reduce **Pixel Height**.
User can see this on the included FreeSans font at size 24 with a 24x32 cell, where W and @ are scaled down to fit the 24px width. The FreenSans font is fine at 16x16 or 32x32 size.

### Unavoidable clipping (amber)

```bash
Warning: font ink height (34px) exceeds canvas (32px). Some clipping may be 
unavoidable — try a smaller font size or larger cell height.
```

The font's tallest glyphs are simply too large for the cell. Increase **Pixel Height**
or reduce the font size to resolve this. The clipping may only affect a few characters, and may be acceptable depending on your use case, but the warning is there to make sure you know about it.
