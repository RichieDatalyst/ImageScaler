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
