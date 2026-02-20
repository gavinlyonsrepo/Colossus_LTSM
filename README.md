# Colossus_LTSM

[![Website](https://img.shields.io/badge/Website-Link-blue.svg)](https://gavinlyonsrepo.github.io/)  [![Rss](https://img.shields.io/badge/Subscribe-RSS-yellow.svg)](https://gavinlyonsrepo.github.io//feed.xml)  [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/paypalme/whitelight976)

## Table of Contents

* [Overview](#overview)
* [Installation](#installation)
* [Libraries](#libraries)
* [Usage](#usage)
* [Input](#input)
* [Output](#output)
* [Configuration file](#configuration-file)
* [Desktop Entry](#desktop-entry)
* [Screenshots](#screenshots)
* [Projects](#projects)

## Overview

**Colossus_LTSM** is a Python tool for converting TrueType fonts (`.ttf`) into C/C++ bitmap arrays and for visualizing font data stored in C/C++ header files.  
It is aimed at users working with embedded systems, LCDs, and GUIs where compact fonts are needed.

* Convert `.ttf` fonts to C/C++ arrays
* Adjustable font size, ASCII range, and addressing mode
* Visualize fonts from existing C/C++ headers
* GUI built with Tkinter
* Lightweight: only depends on `Pillow`

## Installation

1. [github repository](https://www.github.com/gavinlyonsrepo/Colossus_LTSM)
2. [Pypi package](https://pypi.org/project/colossus-ltsm/)

The program is present in python package index, Pypi.
Install (you can use *pip* or *pipx*) to the location or environment of your choice.

```python
# For example with pipx 
pipx install colossus-ltsm
```

## Libraries

[Pillow](https://python-pillow.org/) for image processing

## Usage

0. Github repository: Colossus_LTSM
1. PyPI package name: colossus-ltsm
2. Import path: import colossus_ltsm
3. Executable command: colossus

Run the GUI:

Select from application menu(if desktop entry installed) or run from terminal with:

```python
colossus
# or directly with Python
 python3 -m colossus_ltsm.colossus_main
```

## Input

* Select a `.ttf` font file
* Set font size, Width and Height(e.g., 12, 16, 24)
* Define ASCII range (e.g., 32-126)
* Choose data addressing mode (horizontal or vertical)
* Choose C or C++ arrays
* Choose file extension (.h or .hpp)
* Choose font name and file name
* Some ttf files are available in the `extras/ttf` directory for testing.

## Output

* Generates a C or C++ header file with bitmap arrays.
* Visualizes the font in the GUI, a PNG image can also be exported.

Example output :

```c
// Example Font
// An 8 by 8 character size font starting at 
// ASCII offset 0x30 in ASCII table with 0x02 characters in font. 
// 0 and 1 , size 20 bytes, 4 Control bytes at start.
static const std::array<uint8_t, 20> FontBinaryExample =
{
0x08, 0x08, 0x30, 0x01,   // x-size, y-size, offset, (last character-offset : 0x31-0x30)
0x7C,0xC6,0xCE,0xD6,0xE6,0xC6,0x7C,0x00, // ASCII font data '0' : 0x30
0x18,0x38,0x18,0x18,0x18,0x18,0x7E,0x00 // ASCII font data  '1' : 0x31
};
```

Exported PNG image of font data visualization:

![ img font ](https://github.com/gavinlyonsrepo/Colossus_LTSM/blob/main/extras/images/HomeSpun.png)

## Configuration file

The configuration file is created on startup and populated by default values.
The file is located at '~/.config/colossus_ltsm/colossus_ltsm.cfg' on Linux systems.

| Setting | Value | Default | Note |
| ------ | ------ | ----- | ----- |
| scale | int | 4 | Scale of font displayed |
| Columns | int | 16 | Number of columns of font characters to display |
| debug | bool | False | Enable debug logging |

## Desktop Entry

A button on the main GUI allows Linux users to install a desktop entry and icon for Colossus.This creates a `.desktop` file in `~/.local/share/applications/` and an icon in `~/.local/share/icons/`, allowing Colossus to be launched from the application menu. The button is automatically disabled if the desktop entry is already installed. Uses *Curl* to download the icon from GitHub and creates the desktop entry file with the correct paths.

## Screenshots

![ image ](https://github.com/gavinlyonsrepo/Colossus_LTSM/blob/main/extras/images/screenshot.png)

## Projects

Some of my libraries that use these fonts are:

| MCU type | Library link | Data adddressing mode |
| ------ | ------ | ----- |
| Arduino | [GFX](https://github.com/gavinlyonsrepo/display16_LTSM) | Horizontal |
| Raspberry Pi Pico | [GFX 16 bit](https://github.com/gavinlyonsrepo/displaylib_16bit_PICO) | Horizontal |
| Raspberry Pi Pico | [GFX 1 bit](https://github.com/gavinlyonsrepo/displaylib_1bit_PICO) | Vertical |
| Raspberry Pi | [GFX](https://github.com/gavinlyonsrepo/Display_Lib_RPI) | Horizontal |
| PIC | [OLED](https://github.com/gavinlyonsrepo/pic_18F47K42_projects ) | Vertical |
