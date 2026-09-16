## Image Enhancement GUI (Tkinter + OpenCV) ##
## Purpose ##

This project implements gray-scale image enhancement algorithms with an intuitive Tkinter-based GUI, allowing users to visualize and compare transformations interactively.
It demonstrates key digital image processing concepts such as contrast stretching, shrinking, sliding, histogram equalization, and histogram specification.

## Algorithms Implemented ##

## Stretching & Shrinking (Linear / Piecewise / Sliding) ##

Uses mapping equations to enhance or compress intensity ranges.

Piecewise mapping allows selective intensity control.

## Histogram Equalization ##

Automatically redistributes gray levels for uniform brightness and improved contrast.

## Histogram Specification ##

Adjusts an image’s intensity distribution to match another image’s histogram.




| **Use Case**                   | **Suggested Image Type**                    | **Recommended Values / Parameters**            | **Expected Result**                                                     |
| ------------------------------ | ------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------- |
| **Stretching (Linear)**        | Low-contrast grayscale image                | New Min = 0, New Max = 255                     | Improves contrast and reveals hidden details                            |
| **Stretching (Piecewise)**     | Image with both dark and bright regions     | Range1: 0–100 → 0–80, Range2: 100–255 → 80–255 | Enhances dark areas more strongly than bright                           |
| **Shrinking**                  | High-contrast grayscale image               | New Min = 50, New Max = 200                    | Compresses dynamic range; softer image tones                            |
| **Sliding (Brightness Shift)** | Normal grayscale image                      | Offset = +40 (brighter) or −40 (darker)        | Shifts overall brightness without changing contrast                     |
| **Histogram Equalization**     | Dull grayscale image                        | No parameters                                  | Redistributes pixel intensities for uniform contrast                    |
| **Histogram Specification**    | Two grayscale images (Original + Specified) | Load both images and click **Apply**           | Original image adopts the intensity distribution of the specified image |


## 1. Adaptive Contrast Enhancement (ACE)
## Concept

Adaptive Contrast Enhancement (ACE) improves the visibility of details in images by adjusting contrast locally , meaning it looks at small regions (windows) of the image rather than the entire image at once.

It’s especially useful when:

An image has uneven lighting (some parts are dark, others bright).

You want to highlight local details without losing global structure.

## Working Principle

Each pixel’s intensity is modified based on the contrast in its local neighborhood (window).
The algorithm compares each pixel to its surrounding pixels and adjusts it using gain factors that depend on local variance (contrast).

| Parameter       | Meaning                                           | How It Affects Output                                                                                        |
| --------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **k1**          | Lower gain factor                                 | Controls enhancement in low-contrast areas —> higher k1 increases local brightness.                           |
| **k2**          | Upper gain factor                                 | Controls enhancement in high-contrast regions —> higher k2 increases edge sharpness and fine detail.          |
| **Window Size** | Size of local region (odd number like 3, 5, 7, 9) | Larger window = smoother enhancement but may lose fine details. Smaller window = sharper but possibly noisy. |

## Why odd window size?
Because there must be a center pixel —> e.g., a 3×3 window has a clear middle (the pixel being enhanced).

## Expected Effect

Low-contrast regions become clearer.

Shadows get more detail.
Image appears more balanced and natural.


| Type                           | Why                                           |
| ------------------------------ | --------------------------------------------- |
| A dark photo with uneven light | To observe local enhancement.                 |
| Landscape with shadows         | To see improved details in darker regions.    |
| Portrait with soft lighting    | To verify it doesn’t distort colors too much. |

## Expected Result:
Enhanced version should look brighter, clearer, and more detailed, but still realistic (not over-saturated).



## Color Contrast Enhancement (CCE)
## Concept

Color Contrast Enhancement (CCE) improves the vibrancy and contrast of a color image while preserving natural hues.
It operates in the HSL (Hue–Saturation–Lightness) color space because it separates:

Hue → Color tone

Saturation → Color richness

Lightness → Brightness

This allows more controlled enhancement.

## Algorithm Flow
Input Image
   ↓
Convert RGB → HSL
   ↓
Hue Band -> Remains Same   
Saturation Band → Histogram Equalization
Lightness Band → Histogram Stretching
   ↓
Combine Enhanced H, S, L Bands
   ↓
Convert HSL → RGB
   ↓
Output: Enhanced Color Image


| Step                       | Operation                           | Purpose                                          |
| -------------------------- | ----------------------------------- | ------------------------------------------------ |
| Convert to HSL             | Separate hue, lightness, saturation | Allows independent control of brightness & color |
| Histogram Equalization (S) | Redistributes color intensity       | Makes colors more vivid                          |
| Histogram Stretching (L)   | Expands brightness range            | Improves overall contrast                        |
| Combine Bands              | Merge adjusted channels             | Reconstructs enhanced HSL image                  |
| Convert to RGB             | Back to normal color image          | For display or saving                            |



## Expected Effect

Colors look richer and more natural.

Brightness range improves —> darks become deeper, highlights more defined.

No color distortion because hue is preserved.

| Type              | Why                                           |
| ----------------- | --------------------------------------------- |
| Outdoor landscape | See better sky, grass, and water colors       |
| Portrait          | Natural skin tones but with improved lighting |
| Old/faded photo   | Restores original color contrast              |

## Expected Result:
Image appears visually sharper, colorful, and balanced, while staying true to its natural colors.


## Image Spatial Frequency & Color Channel Visualization

## Concept Overview

This project demonstrates two fundamental image processing concepts:

Color Channel Separation (RGB)
→ How red, green, and blue contribute individually to a color image.

Spatial Resolution Reduction
→ How reducing image resolution affects visible detail and sharpness, which relates to spatial frequency and pixel size.

## Purpose

This GUI helps visualize how:

Each RGB channel carries different information.

Spatial frequency (detail) changes when resolution is reduced.

Pixel size and spacing determine how much fine detail we can resolve.

It is especially useful for understanding display resolution, camera sensor quality, and image perception in human vision or computer vision systems.

## Concept Breakdown
## 1. Spatial Frequency

Describes how quickly brightness changes across an image.

A high spatial frequency → fine details (sharp edges, texture).

A low spatial frequency → smooth areas (sky, background).

Experimentally, resolution is measured by showing patterns of different spatial frequencies and checking the finest pattern that can be distinguished.

## 2. Image Resolution

Resolution = ability to distinguish two adjacent pixels as separate.

Higher resolution → more pixels → more visible fine detail.

Reducing resolution = lowering spatial frequency → loss of detail.

## 3. RGB Color Channels

Every color image is made of Red, Green, and Blue layers.

Each channel controls how much of that color contributes to the final image.

Viewing them independently helps understand color composition.

## Features Implemented
## 1. Display RGB Channels Separately

Splits the original image into Red, Green, and Blue components.

Opens three separate windows showing each channel’s contribution.

| Channel | What You’ll See                                      |
| ------- | ---------------------------------------------------- |
| Red     | Highlights red-dominant areas                        |
| Green   | Midtones and brightness (most human-visible channel) |
| Blue    | Adds cool tone and depth                             |


## 2. Spatial Resolution Reduction

Reduces the number of pixels (downsampling) but keeps canvas size constant.

Simulates loss of spatial frequency (fine detail).

You can choose reduction percentage interactively (e.g., 50%, 30%, 10%).

The reduced image is then upsampled back to the original size for comparison.

| Reduction % | Visual Effect                    |
| ----------- | -------------------------------- |
| 90–100%     | Original detail                  |
| 50%         | Slight blur, reduced texture     |
| 20%         | Clearly blocky/pixelated         |
| 10%         | Strongly degraded, coarse detail |


| Type                                | Why It’s Useful                                    |
| ----------------------------------- | -------------------------------------------------- |
| Landscape photo (trees, grass, sky) | Has both high and low spatial frequencies          |
| Portrait with lighting              | Shows how resolution affects edges and color tones |
| Checkerboard or grid pattern        | Clearly reveals spatial frequency loss             |
| Colored object photo                | Helps visualize contribution of RGB channels       |


## JPEG Compressor (Python + Tkinter)

A complete grayscale JPEG-like compressor built from scratch using Python, implementing DCT, Quantization, Zigzag Scan, RLE, Huffman Coding, Entropy Measurement, and Image Reconstruction, with GUI visualization.

## Purpose

This assignment demonstrates how the JPEG compression algorithm works internally by implementing each step manually rather than using any library.
It provides an educational, interactive tool that allows users to visualize quantized DCT blocks, Huffman tables, and compressed vs reconstructed images.

## Algorithms Implemented / Working Principle
## Preprocessing ##

Input image is converted to grayscale.

Image is padded so that its dimensions are multiples of 8.

## JPEG Compression Pipeline
## 8×8 Blocking

The image is divided into 8×8 blocks as required by the JPEG standard.

## Discrete Cosine Transform (DCT)

Each block is converted from spatial domain → frequency domain.

## Quantization

Each DCT coefficient is divided by a quantization matrix based on user-selected Quality (1–100).
This is where loss occurs.

## Zigzag Scan

The quantized 8×8 block is converted into a 1×64 vector in zigzag order.

## Run-Length Encoding (RLE) 

Long sequences of zeros in AC coefficients are compressed into (RUN, VALUE) pairs + EOB marker.

## Huffman Coding

All RLE tokens are used to build a custom Huffman table:

1.Symbol frequencies collected

2.Huffman tree built

3.Each symbol assigned a binary code

The encoded bitstream is stored along with the Huffman table.

View:

1.The Huffman symbol list

2.Corresponding Huffman codes

3.Frequency table

## JPEG Decompression Pipeline
## Huffman Decoding

Converts the compressed Huffman bitstream back into a sequence of RLE (Run-Length Encoded) symbols.

## RLE Decoding

Expands each (RUN, VALUE) pair and reconstructs the zigzag-ordered coefficient vectors.

## Dequantization

Multiplies each quantized DCT coefficient with the corresponding value in the JPEG quantization matrix.

## Inverse DCT

Converts each 8×8 block from the frequency domain back into the spatial domain by applying IDCT.

## Block Assembly

Reconstructed 8×8 blocks are combined to form the final decompressed grayscale image.

## Additional Features
## Quantized DCT Block Preview

Displays the lossy quantized DCT coefficients for any selected 8×8 block.

## Huffman Table Viewer

Shows all unique RLE symbols with their assigned Huffman codes and frequencies.

## Entropy Metric

Calculates Shannon entropy for:

Original image

Quantized DCT coefficients

Huffman-encoded symbol stream

These metrics help analyze compression effectiveness and data complexity.

## Input Requirements

Accepts any grayscale-compatible image format.

If an RGB image is loaded, it is internally converted to 8-bit grayscale.

## Expected Output
## 1. Compressed File (.jdemo)

Contains:

Huffman table

DC coefficients (differential encoded)

RLE AC stream

Quantized DCT blocks

Encoded Huffman bitstream

## 2. Reconstructed Image

A lossy grayscale image obtained after dequantization and IDCT.

## 3. Metrics Provided

PSNR (Peak Signal-to-Noise Ratio)

Compression Ratio

Entropy values

## 4. Visual Previews

Original image

Reconstructed image

Quantized DCT block visualization

Huffman table listing

## Flow Diagram

Input Image
↓
Grayscale
↓
Split into 8×8 Blocks
↓
DCT → Quantization → Zigzag → RLE → Huffman Encode
↓
Compressed Data (.jdemo)
↓
Huffman Decode → RLE Decode → Dequantize → IDCT
↓
Reconstructed Image



