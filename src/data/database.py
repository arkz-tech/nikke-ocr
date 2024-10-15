import datetime
import json
import os
from typing import Any, Dict, Optional, List, Tuple

from src.config import Config


class NikkeDatabase:

    def __init__(self) -> None:
        self.config: Config = Config()
        self.data_folder: str = str(self.config.USER_DATA_DIR)
        self.current_file: str = self._generate_new_filename()
        self.data: List[Dict[str, Any]] = []
        self.added_nikkes: int = 0

    def _generate_new_filename(self) -> str:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        return str(self.config.get_user_data_file(timestamp))

    def load_data(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.current_file):
            with open(self.current_file, "r") as f:
                return json.load(f)
        return []

    def save_data(self) -> None:
        os.makedirs(self.data_folder, exist_ok=True)
        with open(self.current_file, "w") as f:
            json.dump(self.data, f, indent=4)

    def add_or_update_character(
        self, name: str, nikke_info: Dict[str, Any]
    ) -> Tuple[bool, bool]:
        # Validate combat_power
        try:
            combat_power = int(nikke_info.get("combat_power", "0"))
        except ValueError:
            combat_power = 0

        simplified_info = {
            "name": name,
            "manufacturer": nikke_info.get("manufacturer"),
            "squad": nikke_info.get("squad"),
            "class": nikke_info.get("class"),
            "burst": nikke_info.get("burst"),
            "rarity": nikke_info.get("rarity"),
            "weapon": nikke_info.get("weapon"),
            "element": nikke_info.get("element"),
            "combat_power": str(combat_power),
            "last_updated": str(datetime.datetime.now()),
        }

        # Check if character already exists
        for i, character in enumerate(self.data):
            if character["name"] == name:
                # Update existing character
                self.data[i] = simplified_info
                self.save_data()
                return True, False  # Updated, but not added

        # If character doesn't exist, add new one
        self.data.append(simplified_info)
        self.added_nikkes += 1
        self.save_data()
        return True, True  # Added new character

    def get_character(self, name: str) -> Optional[Dict[str, Any]]:
        for character in self.data:
            if character["name"] == name:
                return character
        return None

    def get_added_nikkes_count(self) -> int:
        return self.added_nikkes

    def get_all_characters(self) -> List[Dict[str, Any]]:
        return self.data

    def close(self) -> None:
        self.save_data()
