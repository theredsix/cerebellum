import json
from cerebellum.browser.local import LocalLLMBrowserPlanner
from cerebellum import BrowserSessionMemory, BrowserState, BrowserAction, BrowserActionResult, OpenAIBrowserPlanner


recorder = BrowserSessionMemory('session.cerebellum.zip')
goal, actions = recorder.retrieve()

train_examples = OpenAIBrowserPlanner.convert_into_training_examples(goal, actions, False)

output_file_path = 'training_examples.jsonl'

with open(output_file_path, 'w') as file:
    for example in train_examples:
        json_line = json.dumps(example)
        file.write(json_line + '\n')
