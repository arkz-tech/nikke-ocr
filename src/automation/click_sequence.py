import time
from typing import List, Tuple

import pyautogui


class ClickAutomation:
    def __init__(self) -> None:
        self.click_sequence: List[Tuple[int, int, int]] = [(738, 987, 2), (126, 403, 1)]

    def execute_sequence(self) -> None:
        """Executes the predefined sequence of clicks."""
        for x, y, delay in self.click_sequence:
            pyautogui.click(x, y)
            time.sleep(delay)

    def perform_click(self, x: int, y: int, delay: int = 0) -> None:
        """Performs a single click at the specified coordinates with a delay."""
        pyautogui.click(x, y)
        time.sleep(delay)
