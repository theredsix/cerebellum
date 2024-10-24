from typing import List, Tuple, Type
import json
import zipfile
from pathlib import Path
from core import (
    StateT, ActionT, ResultT, AbstractSessionMemory, RecordedAction
)

class FileSessionMemory(AbstractSessionMemory[StateT, ActionT, ResultT]):
    file_path: str

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def record(self, 
            goal: str,
            past_actions: List[RecordedAction[StateT, ActionT, ResultT]],
            step: int | None = None) -> bool:
        
        # Determine the mode based on whether we're saving all actions or just one
        mode = 'w' if step == 0 or (step is None and not past_actions) else 'a'
        
        with zipfile.ZipFile(self.file_path, mode, compression=zipfile.ZIP_DEFLATED) as zip_file:
            if step == 0 or (step is None and not past_actions):
                # Save the goal if it's the first step or we're saving all actions
                goal_data = {"goal": goal}
                zip_file.writestr('goal.json', json.dumps(goal_data))
            
            # Determine which actions to save
            actions_to_save = [past_actions[step]] if step is not None else past_actions
            
            for i, action in enumerate(actions_to_save):
                action_data = {
                    "state": {field: getattr(action.state, field) for field in action.state.__dataclass_fields__},
                    "action": {field: getattr(action.action, field) for field in action.action.__dataclass_fields__},
                    "result": {field: getattr(action.result, field) for field in action.result.__dataclass_fields__},
                }
                
                action_index = step if step is not None else len(past_actions) - len(actions_to_save) + i
                zip_file.writestr(f'action{action_index}.json', json.dumps(action_data))

        return True

    def retrieve(self, state_type: Type[StateT], action_type: Type[ActionT], result_type: Type[ResultT]) -> Tuple[str, List[RecordedAction[StateT, ActionT, ResultT]]]:
        goal = ""
        actions = []

        with zipfile.ZipFile(self.file_path, 'r') as zip_file:
            # Read the goal
            with zip_file.open('goal.json') as goal_file:
                goal_data = json.load(goal_file)
                goal = goal_data['goal']

            # Read all action files
            action_files = sorted([f for f in zip_file.namelist() if f.startswith('action') and f.endswith('.json')],
                                  key=lambda x: int(x[6:-5]))  # Sort by action number

            for action_file in action_files:
                with zip_file.open(action_file) as file:
                    action_data = json.load(file)
                    
                    state = state_type(**{
                        field: action_data['state'][field]
                        for field in action_data['state']
                    })
                    
                    action = action_type(**{
                        field: action_data['action'][field]
                        for field in action_data['action']
                    })
                    
                    result = result_type(**{
                        field: action_data['result'][field]
                        for field in action_data['result']
                    })
                    
                    recorded_action = RecordedAction(state, action, result)
                    actions.append(recorded_action)

        return goal, actions
