from typing import List, Tuple

from core import RecordedAction
from cerebellum.memory.file import FileSessionMemory
from cerebellum.browser.types import BrowserState, BrowserAction, BrowserActionResult

class BrowserSessionMemory(FileSessionMemory[BrowserState, BrowserAction, BrowserActionResult]):
    def retrieve(self) -> Tuple[str, List[RecordedAction[BrowserState, BrowserAction, BrowserActionResult]]]:
        return super().retrieve(BrowserState, BrowserAction, BrowserActionResult)