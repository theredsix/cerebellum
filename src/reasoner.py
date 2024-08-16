from abc import ABC, abstractmethod
from src.session import RecordedAction, PageState, PageAction

class Reasoner(ABC):
    @abstractmethod
    def get_next_action(self, goal: str, current_page: PageState, session_history: list[RecordedAction]) -> PageAction:
        pass

    @abstractmethod
    def create_training_set(self, goal: str, recorded_session: list[RecordedAction]):
        pass

