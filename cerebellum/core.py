from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Type
from typing import Generic, TypeVar

@dataclass
class BaseState:
    pass

@dataclass
class BaseAction:
    pass

@dataclass
class BaseResult:
    is_terminal_state: bool

# Define type variables
StateT = TypeVar('StateT', bound=BaseState)
ActionT = TypeVar('ActionT', bound=BaseAction)
ResultT = TypeVar('ResultT', bound=BaseResult)
TrainingDataT = TypeVar('TrainingDataT')

@dataclass
class RecordedAction(Generic[StateT, ActionT, ResultT]):
    state: StateT
    action: ActionT
    result: ResultT

class AbstractPlanner(ABC, Generic[StateT, ActionT, ResultT]):
    @abstractmethod
    def get_next_action(self, goal: str, additional_context: Dict[str, Any] | None, current_state: StateT, past_actions: list[RecordedAction[StateT, ActionT, ResultT]]) -> ActionT:
        pass

class TrainablePlanner(ABC, Generic[TrainingDataT, StateT, ActionT, ResultT]):
    @classmethod
    @abstractmethod 
    def convert_into_training_examples(cls, goal: str, actions: List[RecordedAction[StateT, ActionT, ResultT]]) -> List[TrainingDataT]:
        pass

    def convert_playwright_trace(self, goal: str, file_path: str) -> List[RecordedAction[StateT, ActionT, ResultT]]:
        pass

class SupervisorPlanner(AbstractPlanner[StateT, ActionT, ResultT]):
    def __init__(self, base_planner: AbstractPlanner[StateT, ActionT, ResultT]):
        super().__init__()
        self.base_planner = base_planner

    @abstractmethod
    def review_action(self, recommended_action: ActionT, goal: str, current_state: StateT, 
        past_actions: list[RecordedAction[StateT, ActionT, ResultT]]) -> ActionT:
        pass

    def get_next_action(self, goal: str, additional_context: Dict[str, Any] | None, current_state: StateT, past_actions: list[RecordedAction[StateT, ActionT, ResultT]]) -> ActionT:
        base_action = self.base_planner.get_next_action(goal, additional_context, current_state, past_actions)
        reviewed_action = self.review_action(base_action, goal, current_state, past_actions)
        return reviewed_action

class AbstractLimb(ABC, Generic[ActionT, ResultT]):

    @abstractmethod
    def perform_action(self, action: ActionT)-> ResultT:
        pass

class AbstractSensor(ABC, Generic[StateT]):
    @abstractmethod
    def sense(self) -> StateT:
        pass

    @abstractmethod
    def ensure_state_validity(self, last_sense: StateT, change_threshold: float) -> bool:
        pass


class AbstractSession(ABC, Generic[StateT, ActionT, ResultT]):

    def __init__(self, goal: str, 
            additional_context: Dict[str, Any],
            limb: AbstractLimb[ActionT, ResultT], 
            sensor: AbstractSensor[StateT], 
            planner: AbstractPlanner[StateT, ActionT, ResultT], 
            recorders: 'List[AbstractSessionRecorder[StateT, ActionT, ResultT]]' = [],
            past_actions: list[RecordedAction[StateT, ActionT, ResultT]] = []):
        self.goal = goal
        self.additional_context = additional_context
        self.limb = limb
        self.planner = planner
        self.sensor = sensor
        self.recorders = recorders
        self.past_actions = past_actions

    def step(self):
        # Check if planner is None and raise an error if it is
        if self.planner is None:
            raise ValueError("Cannot step without a Planner. Please provide a valid planner.")

        change_threshold = 10.0
        while(True):
            # Gather current state
            current_state = self.sensor.sense()

            # Get next action from reasoner
            next_action = self.planner.get_next_action(self.goal, self.additional_context, current_state, self.past_actions)

            # Ensure planned action is for a state that still exists
            if self.sensor.ensure_state_validity(current_state, change_threshold):
                break;

            # Increase threshold so we always break out of loop eventually
            change_threshold = change_threshold * 4

        # Perform the action
        action_result = self.limb.perform_action(next_action)

        # Record the action
        recorded_action = RecordedAction(
            state=current_state,
            action=next_action,
            result=action_result
        )
        self.past_actions.append(recorded_action)

        # Call the recorder if it exists
        for recorder in self.recorders:
            recorder.record(self.goal, self.past_actions, len(self.past_actions) - 1)

        return action_result
    
    def start(self):
        while not self.past_actions or not self.past_actions[-1].result.is_terminal_state:
            self.step()

class AbstractSessionRecorder(ABC, Generic[StateT, ActionT, ResultT]):
    @abstractmethod
    def record(self, 
              goal: str,
              past_actions: List[RecordedAction[StateT, ActionT, ResultT]],
               step: int | None = None) -> bool:
        pass

class AbstractSessionMemory(AbstractSessionRecorder[StateT, ActionT, ResultT]):
    
    @abstractmethod
    def retrieve(self, state_type: Type[StateT], action_type: Type[ActionT], result_type: Type[ResultT]) -> Tuple[str, List[RecordedAction]]:
        pass