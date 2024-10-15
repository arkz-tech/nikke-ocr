import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests
from PIL import Image
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QProgressBar

from src.config import Config
from src.utils.localization import get_localized_text as _

BASE_URL = "https://api.dotgg.gg/nikke"
IMAGE_BASE_URL = "https://static.dotgg.gg/nikke/characters"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class DataManager(QObject):
    progress_updated = pyqtSignal(int, int)

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.data_file = os.path.join(config.GENERATED_DATA_FILE)
        self.images_folder = os.path.join(config.GENERATED_DIR, "images")
        self.nikke_data: List[Dict[str, Any]] = []

    def check_and_update_data(self, parent_widget) -> bool:
        if not os.path.exists(self.data_file):
            reply = QMessageBox.question(
                parent_widget,
                _("Download Data"),
                _(
                    "Nikke data is not found. Do you want to download it? This is necessary for the program to function."
                ),
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                return self.download_data(parent_widget)
            else:
                return False
        else:
            local_data = self.load_local_data()
            remote_characters = self.get_remote_characters()

            if self.data_needs_update(local_data, remote_characters):
                reply = QMessageBox.question(
                    parent_widget,
                    _("Update Data"),
                    _(
                        "New Nikke characters are available. Do you want to update the data?"
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    return self.download_data(parent_widget)

        return True

    def load_local_data(self) -> List[Dict[str, Any]]:
        with open(self.data_file, "r", encoding="utf-8") as f:
            self.nikke_data = json.load(f)
        return self.nikke_data

    def get_nikke_data(self) -> List[Dict[str, Any]]:
        if not self.nikke_data:
            self.load_local_data()
        return self.nikke_data

    def get_remote_characters(self) -> List[Dict[str, Any]]:
        response = requests.get(f"{BASE_URL}/characters", headers=HEADERS)
        return response.json() if response.status_code == 200 else []

    def data_needs_update(
        self, local_data: List[Dict[str, Any]], remote_characters: List[Dict[str, Any]]
    ) -> bool:
        local_names = set(char["name"] for char in local_data)
        remote_names = set(char["name"] for char in remote_characters)
        return local_names != remote_names

    def download_data(self, parent_widget) -> bool:
        progress_bar = QProgressBar(parent_widget)
        progress_bar.setGeometry(30, 40, 200, 25)
        progress_bar.show()

        characters = self.get_remote_characters()
        if not characters:
            QMessageBox.critical(
                parent_widget, _("Error"), _("Failed to fetch character data.")
            )
            return False

        total_tasks = (
            len(characters) * 3
        )  # 3 tasks per character: details, small image, big image
        completed_tasks = 0

        processed_data = []
        os.makedirs(self.images_folder, exist_ok=True)

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_char = {
                executor.submit(self.process_single_nikke, char): char
                for char in characters
            }
            for future in as_completed(future_to_char):
                result = future.result()
                if result:
                    processed_data.append(result)
                completed_tasks += 3
                self.progress_updated.emit(completed_tasks, total_tasks)

        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)

        self.nikke_data = processed_data

        progress_bar.hide()
        QMessageBox.information(
            parent_widget,
            _("Download Complete"),
            _("Nikke data has been successfully downloaded and processed."),
        )
        return True

    def process_single_nikke(
        self, character: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        name = character["name"]
        details = self.get_character_details(name)

        if not details:
            print(f"Failed to get details for {name}")
            return None

        small_image_url = f"{IMAGE_BASE_URL}/{character['img']}.webp"
        big_image_url = (
            f"{IMAGE_BASE_URL}/{details.get('imgBig', character['img'])}.webp"
        )
        small_image_path = os.path.join(self.images_folder, f"{character['img']}.png")
        big_image_path = os.path.join(
            self.images_folder, f"{details.get('imgBig', character['img'])}.png"
        )

        self.download_and_convert_image(small_image_url, small_image_path)
        self.download_and_convert_image(big_image_url, big_image_path)

        return {
            "id": details.get("id", ""),
            "name": name,
            "manufacturer": character["manufacturer"],
            "squad": character["squad"],
            "class": character["class"],
            "burst": character["burst"],
            "rarity": character["rarity"],
            "weapon": character["weapon"],
            "element": character["element"],
            "stats": {
                "burst_gen": float(character["burstGen"].rstrip("%")),
                "max_ammo": details.get("maxAmmo", 0),
                "damage": details.get("damage", "0%").rstrip("%"),
                "charge_time": details.get("chargeTime", 0),
                "charge_damage": details.get("chargeDamage", "0%").rstrip("%"),
                "reload_time": details.get("reloadTime", 0),
            },
            "images": {
                "small": os.path.relpath(small_image_path, self.config.GENERATED_DIR),
                "big": os.path.relpath(big_image_path, self.config.GENERATED_DIR),
            },
            "description": details.get("description", ""),
            "extra": {
                "cv_en": details.get("cv_en", ""),
                "cv_kr": details.get("cv_kr", ""),
                "cv_jp": details.get("cv_jp", ""),
            },
        }

    def get_character_details(self, name: str) -> Optional[Dict[str, Any]]:
        response = requests.get(
            f"{BASE_URL}/character/{name.replace(' ', '%20')}", headers=HEADERS
        )
        return response.json() if response.status_code == 200 else None

    def download_and_convert_image(self, url: str, output_path: str) -> bool:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img.save(output_path, "PNG")
            return True
        return False
