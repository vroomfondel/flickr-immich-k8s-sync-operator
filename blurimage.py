#!/usr/bin/env python3


def install_and_import(packagename: str, pipname: str) -> None:
    import importlib

    try:
        importlib.import_module(packagename)
    except ImportError:
        import pip

        pip.main(["install", pipname])
    finally:
        globals()[packagename] = importlib.import_module(packagename)


install_and_import(packagename="pytesseract", pipname="pytesseract")
install_and_import(packagename="cv2", pipname="opencv-python")

import shutil

if shutil.which("tesseract") is None:
    raise SystemExit("tesseract is not installed or not in PATH. Install it, e.g.: apt install tesseract-ocr")

import cv2
import pytesseract
from pytesseract import Output
import re
import argparse
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(description="Blur sensitive text in an image using OCR detection.")
    parser.add_argument("--username", required=True, help="Username to blur in the image")
    parser.add_argument(
        "image", nargs="?", default="Bildschirmfoto_2026-02-02_18-43-40.local.png", help="Path to input image"
    )
    args = parser.parse_args()

    image_path = args.image
    output_path = str(Path(image_path).with_suffix("")) + "_blurred" + Path(image_path).suffix

    # Lade das Bild
    img = cv2.imread(image_path)

    # OCR Konfiguration (psm 6 ist gut für Textblöcke/Code)
    custom_config = r"--oem 3 --psm 6"

    # Texterkennung durchführen
    d = pytesseract.image_to_data(img, output_type=Output.DICT, config=custom_config)

    # Regex für die Zielwörter:
    # Findet "vroomfondel" (case insensitive)
    # ODER Wörter, die auf .png, .jpg, .mp4 enden
    pattern = re.compile(rf"({re.escape(args.username)}|.*\.png$|.*\.jpg$|.*\.mp4$|.*\.mp4\.json$)", re.IGNORECASE)

    n_boxes = len(d["text"])
    for i in range(n_boxes):
        text = d["text"][i].strip()

        # Prüfen, ob das Wort gematcht wird
        if pattern.search(text):
            x, y, w, h = (d["left"][i], d["top"][i], d["width"][i], d["height"][i])

            # Region of Interest (ROI) auswählen
            roi = img[y : y + h, x : x + w]

            # Starken Gaussian Blur anwenden
            # (31, 31) ist die Kernel-Größe (muss ungerade sein), 30 ist die Standardabweichung
            blur = cv2.GaussianBlur(roi, (31, 31), 30)

            # Geblurrtes ROI zurück ins Bild setzen
            img[y : y + h, x : x + w] = blur
            print(f"Geblurrt: {text}")

    # Ergebnis speichern (als PNG für verlustfreie Qualität des Restbildes)
    cv2.imwrite(output_path, img)
    print(f"Fertig! Bild gespeichert unter {output_path}")


if __name__ == "__main__":
    main()
