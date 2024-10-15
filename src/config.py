from pathlib import Path
import sys


class Config:
    if getattr(sys, "frozen", False):
        BASE_DIR = Path(sys.executable).parent
        INTERNAL_DIR = BASE_DIR / "_internal"
    else:
        BASE_DIR = Path(__file__).resolve().parent.parent
        INTERNAL_DIR = BASE_DIR

    RESOURCES_DIR = INTERNAL_DIR / "resources"
    STATIC_DIR = RESOURCES_DIR / "static"

    GENERATED_DIR = BASE_DIR / "generated"
    USER_DATA_DIR = BASE_DIR / "output"

    IMAGES_DIR = STATIC_DIR / "images"
    LANG_DIR = STATIC_DIR / "lang"

    GENERATED_IMAGES_DIR = GENERATED_DIR / "images" / "characters"
    GENERATED_DATA_FILE = GENERATED_DIR / "data" / "nikke_data.json"

    @classmethod
    def get_user_data_file(cls, timestamp):
        return cls.USER_DATA_DIR / f"nikke_ocr_{timestamp}.json"

    OCR_LANGUAGE = "en"
    CLICK_X = 1893
    CLICK_Y = 583
    LANGUAGE = "en"
    RARITY_ROI = (1569, 176, 1718, 253)
    ATTRIBUTE_COORDS: dict[str, dict[str, dict[str, int]]] = {
        "SSR": {
            "element": {"x": 1617, "y": 639},
            "weapon": {"x": 1684, "y": 645},
            "squad": {"x": 1716, "y": 592},
            "cp": {"left": 1724, "top": 335, "right": 1870, "bottom": 389},
            "name": {"left": 1733, "top": 234, "right": 1863, "bottom": 267},
            "burst": {"left": 1634, "top": 304, "right": 1695, "bottom": 363},
        },
        "SR": {
            "element": {"x": 1617, "y": 639},
            "weapon": {"x": 1684, "y": 645},
            "squad": {"x": 1716, "y": 592},
            "cp": {"left": 1724, "top": 335, "right": 1870, "bottom": 389},
            "name": {"left": 1733, "top": 234, "right": 1863, "bottom": 267},
            "burst": {"left": 1634, "top": 304, "right": 1695, "bottom": 363},
        },
        "R": {
            "element": {"x": 1612, "y": 606},
            "weapon": {"x": 1683, "y": 606},
            "squad": {"x": 1734, "y": 558},
            "cp": {"left": 1713, "top": 296, "right": 1870, "bottom": 355},
            "name": {"left": 1733, "top": 234, "right": 1863, "bottom": 267},
            "burst": {"left": 1634, "top": 304, "right": 1695, "bottom": 363},
        },
    }
