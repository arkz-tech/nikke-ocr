import os
from pathlib import Path
from typing import Dict, Optional

import cv2
import easyocr
import numpy as np
from skimage.metrics import structural_similarity as ssim

from src.config import Config


class OCRProcessor:
    def __init__(self) -> None:
        self.reader = easyocr.Reader([Config.OCR_LANGUAGE], gpu=False)

    def process_name_roi(self, image: np.ndarray) -> Optional[str]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results = self.reader.readtext(binary)
        return results[0][1] if results else None

    def process_rarity_roi(self, image: np.ndarray) -> str:
        results = self.reader.readtext(
            image, allowlist="RSr", min_size=10, width_ths=2.0
        )
        return " ".join([result[1] for result in results]) if results else ""


class ImageProcessor:
    def __init__(self) -> None:
        self.ocr_processor: OCRProcessor = OCRProcessor()
        self.burst_references: Dict[str, np.ndarray] = {}
        self.load_burst_references()

    def load_burst_references(self) -> None:
        reference_dir: Path = Config.STATIC_DIR / "images" / "bursts"
        for filename in os.listdir(reference_dir):
            if filename.endswith(".png"):
                img = cv2.imread(str(reference_dir / filename))
                self.burst_references[filename] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def process_roi(self, image: np.ndarray) -> Optional[str]:
        return self.ocr_processor.process_name_roi(image)

    def compare_images(self, img1: np.ndarray, img2: np.ndarray) -> float:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(gray1, gray2, full=True)
        return score

    def identify_burst(self, screenshot: np.ndarray) -> Optional[str]:
        roi: np.ndarray = screenshot[341:400, 1635:1696]
        best_match: Optional[str] = None
        best_score: float = -1

        for filename, ref_img in self.burst_references.items():
            ref_img = cv2.resize(ref_img, (roi.shape[1], roi.shape[0]))
            score: float = self.compare_images(roi, ref_img)

            if score > best_score:
                best_score = score
                best_match = filename

        return best_match.split(".")[0] if best_match else None

    def preprocess_image(self, roi: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        orange_mask = cv2.inRange(
            hsv, np.array([0, 100, 100]), np.array([30, 255, 255])
        )
        blue_mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
        pink_mask = cv2.inRange(hsv, np.array([140, 50, 50]), np.array([170, 255, 255]))
        combined_mask = cv2.bitwise_or(
            cv2.bitwise_or(orange_mask, blue_mask), pink_mask
        )
        result = cv2.bitwise_and(roi, roi, mask=combined_mask)
        lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return final

    def classify_color(self, roi: np.ndarray) -> str:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        average_color = np.mean(hsv, axis=(0, 1))
        if 0 <= average_color[0] <= 30:
            return "SSR"
        elif 90 <= average_color[0] <= 130:
            return "R"
        elif 140 <= average_color[0] <= 170:
            return "SR"
        else:
            return "Unknown"

    def identify_rarity(self, screenshot: np.ndarray) -> str:
        roi = screenshot[
            Config.RARITY_ROI[1] : Config.RARITY_ROI[3],
            Config.RARITY_ROI[0] : Config.RARITY_ROI[2],
        ]
        processed_roi = self.preprocess_image(roi)
        ocr_result = self.ocr_processor.process_rarity_roi(processed_roi)
        color_class = self.classify_color(roi)

        print(f"ROI shape: {roi.shape}")
        print(f"Processed ROI shape: {processed_roi.shape}")
        print(f"OCR result: {ocr_result}")
        print(f"Color classification: {color_class}")

        final_result = self.validate_result(ocr_result, color_class)

        return final_result

    def validate_result(self, text: str, color_class: str) -> str:
        valid_results = ["SSR", "SR", "R", "ssr", "sr", "r"]
        if text and text.upper() in valid_results:
            return text.upper()
        else:
            return color_class
