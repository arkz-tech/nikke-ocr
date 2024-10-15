import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import pyautogui
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.automation.click_sequence import ClickAutomation
from src.config import Config
from src.data.data_manager import DataManager
from src.data.database import NikkeDatabase
from src.utils.image_processor import ImageProcessor
from src.utils.localization import get_localized_text as _
from src.utils.localization import set_language

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KeyboardHandler(QObject):
    key_pressed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        self.key_pressed.emit(key)

    def stop(self):
        self.listener.stop()


class NikkeOCRUI(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.config: Config = Config()
        self.data_manager: DataManager = DataManager(self.config)
        self.image_processor: ImageProcessor = ImageProcessor()
        self.database: NikkeDatabase = NikkeDatabase()
        self.click_sequence: ClickAutomation = ClickAutomation()

        self.automation_active: bool = False
        self.first_nikke_name: Optional[str] = None
        self.current_step: int = 0
        self.selected_rarities: List[str] = ["SSR", "SR", "R"]

        self._setup_ui()
        self._setup_automation()
        self._check_and_update_data()

    def _setup_ui(self) -> None:
        self.setWindowTitle(_("NIKKE OCR"))
        self.setGeometry(100, 100, 400, 300)

        self.setWindowIcon(QIcon(str(self.config.RESOURCES_DIR / "icon.png")))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout: QVBoxLayout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)

        self._setup_menu_bar()

        top_layout = QHBoxLayout()

        self.status_label: QLabel = QLabel(_("Status: Idle (Press F1 to start)"))
        top_layout.addWidget(self.status_label)

        rarity_layout = QHBoxLayout()
        self.rarity_label = QLabel(_("Select Rarities:"))
        rarity_layout.addWidget(self.rarity_label)
        self.rarity_checkboxes = {}
        for rarity in ["SSR", "SR", "R"]:
            checkbox = QCheckBox(rarity)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._update_selected_rarities)
            rarity_layout.addWidget(checkbox)
            self.rarity_checkboxes[rarity] = checkbox
        top_layout.addLayout(rarity_layout)

        main_layout.addLayout(top_layout)

        self.image_label: QLabel = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(100)
        main_layout.addWidget(self.image_label)

        bottom_layout = QVBoxLayout()

        self.log_text: QTextEdit = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(80)
        bottom_layout.addWidget(self.log_text)

        self.progress_bar: QProgressBar = QProgressBar(self)
        bottom_layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        main_layout.addLayout(bottom_layout)

    def _update_selected_rarities(self) -> None:
        self.selected_rarities = [
            rarity
            for rarity, checkbox in self.rarity_checkboxes.items()
            if checkbox.isChecked()
        ]

    def _check_and_update_data(self) -> None:
        self.data_manager.progress_updated.connect(self._update_progress)
        if not self.data_manager.check_and_update_data(self):
            self.close()

    def _setup_automation(self) -> None:
        self.keyboard_handler = KeyboardHandler()
        self.keyboard_handler.key_pressed.connect(self._on_key_press)

        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self._perform_automation)

    def _setup_menu_bar(self) -> None:
        menubar = self.menuBar()
        if menubar is None:
            self.log("Error: Unable to create menu bar")
            return

        file_menu = menubar.addMenu(_("File"))
        if file_menu:
            exit_action = QAction(_("Exit"), self)
            exit_action.triggered.connect(self._close_application)
            file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu(_("Settings"))
        if settings_menu:
            language_menu = settings_menu.addMenu(_("Language"))
            if language_menu:
                language_group = QActionGroup(self)
                language_group.setExclusive(True)

                for lang, lang_name in [("en", _("English")), ("es", _("Spanish"))]:
                    action = QAction(lang_name, self)
                    action.setCheckable(True)
                    action.setData(lang)
                    language_group.addAction(action)
                    language_menu.addAction(action)
                    if lang == "en":  # Set English as default
                        action.setChecked(True)

                language_group.triggered.connect(self._change_language)
            else:
                self.log("Error: Unable to create language submenu")
        else:
            self.log("Error: Unable to create settings menu")

    def _change_language(self, action: QAction) -> None:
        lang = action.data()
        set_language(lang)
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(_("NIKKE OCR"))
        self.status_label.setText(_("Status: Idle (Press F1 to start)"))
        self.rarity_label.setText(_("Select Rarities:"))

        menubar = self.menuBar()
        if menubar:
            menubar.clear()
        self._setup_menu_bar()

        self.log(_("UI language updated"))

    def _update_progress(self, value: int, maximum: int) -> None:
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        if value == maximum:
            self.progress_bar.hide()
            self.log(_("Data processing completed"))
            QMessageBox.information(
                self, _("Process Completed"), _("Character processing has finished.")
            )

    @pyqtSlot(object)
    def _on_key_press(self, key: Union[Key, KeyCode, None]) -> None:
        if key == keyboard.Key.f1:
            self._toggle_automation()

    def _toggle_automation(self) -> None:
        if not self.automation_active:
            self._start_automation()
        else:
            self._stop_automation()

    def _start_automation(self) -> None:
        self.automation_active = True
        self.current_step = 0
        self.first_nikke_name = None
        self.status_label.setText(_("Status: Running (Press F1 to stop)"))
        self.log(_("Automation started. Performing click sequence..."))
        self._perform_automation()

    def _stop_automation(self) -> None:
        self.automation_active = False
        self.timer.stop()
        self.current_step = 0
        self.status_label.setText(_("Status: Idle (Press F1 to start)"))
        self.log(_("Automation stopped and reset"))
        self.log(f"Total new Nikkes added: {self.database.get_added_nikkes_count()}")

    def _move_to_next_character(self) -> None:
        self.log(_("Clicking to move to next character."))
        self.click_sequence.perform_click(self.config.CLICK_X, self.config.CLICK_Y, 1)

    @pyqtSlot()
    def _perform_automation(self) -> None:
        if not self.automation_active:
            QMessageBox.warning(
                self,
                _("Automation Stopped"),
                _("Automation has been stopped. Press F1 to start again."),
            )
            return

        try:
            if self.current_step == 0:
                self.log("Executing initial click sequence...")
                self.click_sequence.execute_sequence()
                self.log("Click sequence completed. Starting character processing...")
                self.current_step = 1
                self.first_character_name = None
                self.timer.start(100)
            elif self.current_step == 1:
                self.log("Capturing screenshot...")
                screenshot = cv2.cvtColor(
                    np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR
                )
                self.log("Screenshot captured")

                rarity = self.image_processor.identify_rarity(screenshot)
                self.log(f"Detected rarity: {rarity}")

                if rarity == "Unknown":
                    self.log("Unable to determine rarity. Analyzing character...")
                elif rarity not in self.selected_rarities:
                    self.log(
                        f"Skipping {rarity} character as it's not selected for processing"
                    )
                    self._move_to_next_character()
                    return

                coords = Config.ATTRIBUTE_COORDS[rarity]

                # cp_roi = screenshot[335:389, 1724:1870]
                cp_roi = screenshot[
                    Config.ATTRIBUTE_COORDS[rarity]["cp"][
                        "top"
                    ] : Config.ATTRIBUTE_COORDS[rarity]["cp"]["bottom"],
                    Config.ATTRIBUTE_COORDS[rarity]["cp"][
                        "left"
                    ] : Config.ATTRIBUTE_COORDS[rarity]["cp"]["right"],
                ]
                cp_value = self.image_processor.process_roi(cp_roi)
                self.log(f"Extracted Combat Power: {cp_value}")

                name_roi = screenshot[234:267, 1733:1863]
                ocr_result = self.image_processor.process_roi(name_roi)
                self.log(f"OCR Result: {ocr_result}")

                if ocr_result and ocr_result.lower() not in ["rei", "quency"]:
                    matching_nikkes = self._find_matching_nikkes(ocr_result)
                    if len(matching_nikkes) == 1:
                        nikke_info = matching_nikkes[0]
                        self.log(
                            f"Unique Nikke identified by name: {nikke_info['name']}"
                        )
                        nikke_info["combat_power"] = cp_value
                        nikke_info["rarity"] = rarity
                        self._handle_character(nikke_info)
                        self._move_to_next_character()
                        return
                    elif len(matching_nikkes) > 1:
                        self.log(
                            f"Multiple Nikkes found with name {ocr_result}. Proceeding with detailed identification."
                        )
                    else:
                        self.log(
                            f"No Nikke found with name {ocr_result}. Proceeding with detailed identification."
                        )
                elif ocr_result and ocr_result.lower() in ["rei", "quency"]:
                    self.log(
                        "Nikke named Rei or Quency detected. Proceeding with detailed identification due to multiple characters with this name."
                    )

                # If not uniquely identified by name or is "Rei", continue with detailed process
                nikke_info: Optional[Dict[str, Any]] = self._get_nikke_info(
                    screenshot, coords
                )

                if nikke_info:
                    nikke_info["combat_power"] = cp_value
                    nikke_info["rarity"] = rarity
                    self._handle_character(nikke_info)

                    if self.first_nikke_name is None:
                        self.first_nikke_name = nikke_info["name"]
                        self.log(f"First Nikke detected: {self.first_nikke_name}")
                    elif nikke_info["name"] == self.first_nikke_name:
                        self.log("Cycle completed. Stopping automation.")
                        self._stop_automation()
                        QMessageBox.information(
                            self,
                            _("Process Completed"),
                            _("All characters have been processed."),
                        )
                        return

                    self.processed_nikkes += 1
                    self.log(f"Processed Nikkes: {self.processed_nikkes}")
                else:
                    self.log("Failed to identify Nikke. Moving to next character.")

                self._move_to_next_character()

        except Exception as e:
            self.log(f"Error in perform_automation: {str(e)}")
            import traceback

            self.log(traceback.format_exc())  # This will print the full stack trace

    def _find_matching_nikkes(self, name: str) -> List[Dict[str, Any]]:
        nikke_data = self.data_manager.get_nikke_data()
        return [nikke for nikke in nikke_data if nikke["name"].lower() == name.lower()]

    def _get_nikke_info(
        self, screenshot: np.ndarray, coords: Dict[str, Dict[str, int]]
    ) -> Optional[Dict[str, Any]]:
        nikke_data = self.data_manager.get_nikke_data()
        filtered_nikkes: List[Dict[str, Any]] = nikke_data

        weapon_map: Dict[str, str] = {
            "Sniper Rifle": "SR",
            "Submachine Gun": "SMG",
            "Machine Gun": "MG",
            "Assault Rifle": "AR",
            "Shotgun": "SG",
            "Rocket Launcher": "RL",
        }

        attributes = [
            (
                "element",
                lambda: self._get_attribute(
                    (coords["element"]["x"], coords["element"]["y"]),
                    (837, 540, 242, 57),
                ),
            ),
            (
                "weapon",
                lambda: weapon_map.get(
                    self._get_attribute(
                        (coords["weapon"]["x"], coords["weapon"]["y"]),
                        (825, 402, 380, 40),
                    )
                    or "",
                ),
            ),
            (
                "squad",
                lambda: self._get_attribute(
                    (coords["squad"]["x"], coords["squad"]["y"]), (723, 299, 487, 51)
                ),
            ),
            ("burst", lambda: self.image_processor.identify_burst(screenshot)),
        ]

        for attr_name, getter_func in attributes:
            attr_value = getter_func()
            if attr_value:
                self.log(f"Detected {attr_name}: {attr_value}")
                filtered_nikkes = [
                    n for n in filtered_nikkes if n[attr_name] == attr_value
                ]
                self.log(f"Filtered to {len(filtered_nikkes)} possible Nikkes")

                if len(filtered_nikkes) == 1:
                    self.log(f"Unique Nikke identified: {filtered_nikkes[0]['name']}")
                    return filtered_nikkes[0]
                elif len(filtered_nikkes) == 0:
                    self.log(
                        "No matching Nikkes found. Stopping identification process."
                    )
                    return None

        if len(filtered_nikkes) > 1:
            return self._compare_images(screenshot, filtered_nikkes)

        return None

    def _get_attribute(
        self,
        click_pos: Tuple[int, int],
        screenshot_region: Tuple[int, int, int, int],
        valid_values: Optional[List[str]] = None,
    ) -> Optional[str]:
        self.click_sequence.perform_click(*click_pos, 1)
        screenshot = pyautogui.screenshot(region=screenshot_region)
        attribute = self.image_processor.process_roi(np.array(screenshot))
        self.log(f"Attribute: {attribute}")
        self.click_sequence.perform_click(10, 10, 0)
        return attribute if valid_values is None or attribute in valid_values else None

    def _compare_images(
        self, screenshot: np.ndarray, nikkes: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        nikke_image = screenshot[118:793, 292:1439]
        best_match: Optional[Dict[str, Any]] = None
        best_score: float = -1

        for nikke in nikkes:
            reference_image: np.ndarray = cv2.imread(
                f"{self.config.GENERATED_IMAGES_DIR}/{nikke['images']['big']}",
                cv2.IMREAD_UNCHANGED,  # This will load the image as-is, whether it's color or grayscale
            )

            if reference_image is None:
                print(f"Warning: Could not load image for {nikke['name']}")
                continue

            score: float = self.compare_images(nikke_image, reference_image)
            if score > best_score:
                best_score = score
                best_match = nikke

        return best_match

    def _handle_character(self, nikke_info: Dict[str, Any]) -> None:
        name: str = nikke_info["name"]
        self.log(f"Identified Nikke: {name}")

        success, added = self.database.add_or_update_character(name, nikke_info)
        if success:
            if added:
                self.log(f"Added new Nikke to database: {name}")
            else:
                self.log(f"Updated existing Nikke in database: {name}")
        else:
            self.log(f"Failed to update database for {name}")

    def _close_application(self) -> None:
        self.close()

    def log(self, message: str) -> None:
        logger.info(message)
        self.log_text.append(_(message))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.keyboard_handler.stop()
        self.database.close()
        self.automation_active = False
        super().closeEvent(event)
