from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
from typing import Generic, TypeVar

class ActionOutcome(Enum):
    GOAL_ACHIEVED = "Goal achieved."
    GOAL_UNREACHABLE = "Goal is unreachable."

@dataclass
class ActionResult:
    outcome: TypeVar('T', bound=ActionOutcome)

# Define type variables
StateT = TypeVar('StateT')
ActionT = TypeVar('ActionT')
ResultT = TypeVar('ResultT', bound=ActionResult)
TrainingDataT = TypeVar('TrainingDataT')

@dataclass
class RecordedAction(Generic[StateT, ActionT, ResultT]):
    state: StateT
    action: ActionT
    result: ResultT

class AbstractPlanner(ABC, Generic[StateT, ActionT, ResultT]):
    @abstractmethod
    def get_next_action(self, goal: str, current_state: StateT, past_actions: list[RecordedAction[StateT, ActionT, ResultT]]) -> ActionT:
        pass

class TrainablePlanner(ABC, Generic[TrainingDataT]):
    @abstractmethod
    def get_training_data(self, step: int = None) -> List[TrainingDataT]:
        pass

class SupervisorPlanner(AbstractPlanner[StateT, ActionT, ResultT]):
    base_planner: AbstractPlanner[StateT, ActionT, ResultT]

    def __init__(self, base_planner: AbstractPlanner[StateT, ActionT, ResultT]):
        super().__init__()
        self.base_planner = base_planner

    @abstractmethod
    def review_action(self, recommended_action: ActionT, goal: str, current_state: StateT, 
        past_actions: list[RecordedAction[StateT, ActionT, ResultT]]) -> ActionT:
        pass

    def get_next_action(self, goal: str, current_state: StateT, past_actions: list[RecordedAction[StateT, ActionT, ResultT]]) -> ActionT:
        base_action = self.base_planner.get_next_action(goal, current_state, past_actions)
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

class AbstractSession(ABC, Generic[StateT, ActionT, ResultT]):
    limb: AbstractLimb[ActionT, ResultT]
    goal: str
    planner: AbstractPlanner[StateT, ActionT, ResultT]
    sensor: AbstractSensor[StateT]
    past_actions: List[RecordedAction[StateT, ActionT, ResultT]]
    recorders: 'List[AbstractSessionRecorder[StateT, ActionT, ResultT]]'

    def __init__(self, goal: str, limb: AbstractLimb[ActionT, ResultT], 
            sensor: AbstractSensor[StateT], 
            planner: AbstractPlanner[StateT, ActionT, ResultT], 
            recorders: 'List[AbstractSessionRecorder[StateT, ActionT, ResultT]]' = [],
            past_actions: list[RecordedAction[StateT, ActionT, ResultT]] = []):
        self.goal = goal
        self.limb = limb
        self.planner = planner
        self.sensor = sensor
        self.recorders = recorders
        self.past_actions = past_actions

    def step(self):
        # Check if planner is None and raise an error if it is
        if self.planner is None:
            raise ValueError("Cannot step without a Planner. Please provide a valid planner.")

        # Gather current state
        current_state = self.sensor.sense()

        # Get next action from reasoner
        next_action = self.planner.get_next_action(self.goal, current_state, self.past_actions)

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
            recorder.record(self.goal, self.past_actions)

        return action_result
    
    def start(self):
        while (not self.past_actions or
               self.past_actions[-1].result.outcome not in [ActionOutcome.GOAL_ACHIEVED,
                                                       ActionOutcome.GOAL_UNREACHABLE]):
            self.step()

class AbstractSessionRecorder(ABC, Generic[StateT, ActionT, ResultT]):
    @abstractmethod
    def record(self, 
              goal: str,
              past_actions: List[RecordedAction[StateT, ActionT, ResultT]],
               step: int = 0) -> bool:
        pass

class AbstractSessionMemory(AbstractSessionRecorder[StateT, ActionT, ResultT]):
    
    @abstractmethod
    def retrieve(self) -> Tuple[str, List[RecordedAction]]:
        pass