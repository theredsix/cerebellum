import json
from cerebellum.browser.local import LocalLLMBrowserPlanner
from cerebellum import BrowserSessionMemory, BrowserState, BrowserAction, BrowserActionResult, OpenAIBrowserPlanner

filename = 'radio.cere.zip'
print(f"Processing: {filename}")

recorder = BrowserSessionMemory(filename)
goal, actions = recorder.retrieve()

train_examples = OpenAIBrowserPlanner.convert_into_training_examples(goal, actions, False)

output_file_path = f"{filename}.jsonl"

with open(output_file_path, 'w') as file:
    for example in train_examples:
        json_line = json.dumps(example)
        file.write(json_line + '\n')
