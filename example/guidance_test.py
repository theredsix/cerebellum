from guidance import models, gen, system, user, assistant, role, select
from guidance.chat import Llama3ChatTemplate

class ExtendedLlama3ChatTemplate(Llama3ChatTemplate):
    def get_role_start(self, role_name):
        if role_name == "tool_response":
            return "<|start_header_id|>ipython<|end_header_id|>\n\n"
        else:
            return super().get_role_start(role_name)

llm = models.LlamaCpp("/usr/share/ollama/.ollama/models/blobs/sha256-09cd6813dc2e73d9db9345123ee1b3385bb7cee88a46f13dc37bc3d5e96ba3a4", 
                      echo=False,                      
                      chat_template=ExtendedLlama3ChatTemplate, n_ctx=12072, n_gpu_layers=35, verbose=True)

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(script_dir, 'prompt.txt')
with open(prompt_path, 'r') as file:
    prompt = file.read()

llm = llm + prompt
llm = llm + '{ "progress_summary": "' + gen('progress_summary', stop_regex=',\s*"reasoning"') + \
                ',\n"reasoning": "' + gen('reasoning', stop_regex=',\s*"name"') + \
            f''',\n"name": "{select(["click", "fill", "focus", "goto", "achieved", "unreachable"], name="name")}"'''
            # f''',\n"name": "click"'''

print(llm)

llm = llm + f''', "parameters": {{"css_selector": "{select(['a', 'b', 'c'], name="css_selector")}"}}'''

print(llm)