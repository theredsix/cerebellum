import json
import google.generativeai as genai
from src.session import PageAction, PageState, RecordedAction
from src.reasoner import Reasoner
from src.openapi import tools


tool_config = {
  "function_calling_config": {
    "mode": "ANY",
    "allowed_function_names": ["click", "fill", "focus", "achieved", "unreachable"]
  },
}


class GoogleGeminiReasoner(Reasoner):
    model: genai.GenerativeModel

    def __init__(self, model_name: str = "gemini-1.5-pro-latest"):
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def format_actions_into_chats(self, session_history: list[RecordedAction]):
        chat_messages = []
        for past_action in session_history:
            # Add the action as a model message
            chat_messages.append({
                "role": "model",
                "parts": [
                    {
                        "functionCall": {
                            "name": past_action.action.function,
                            "args": past_action.action.args
                        }
                    }
                ]
            })
            
            # Add the result as a function message
            chat_messages.append({
                "role": "function",
                "parts": [{
                    "functionResponse": {
                        "name": past_action.action.function,
                        "response": {
                            "name": past_action.action.function,
                            "content": {
                                "outcome": past_action.result.outcome,
                                "url": past_action.result.url
                            }
                        }
                    }
                }]
          })
        
        return chat_messages

    def get_next_action(self, goal: str, current_page: PageState, session_history: list[RecordedAction]) -> PageAction:
        system_prompt = f'''
You are an expert developer in CSS and HTML with an excellent knowledge of jQuery and CSS selectors.
Given a webpage's HTML and full + viewport screenshot, decide the best action to take to complete the following goal.

Key considerations:
* You are provided with a "viewport" view of the webpage and a full screenshot of the entire webpage. 
* Always create your CSS selectors based on tags, class and id. DO NOT use parent, child or sibling relationships.
* If you believe the goal cannot be achieved, call the "unreachable" function. 
* If you believe the HTML and viewport screenshot shows that the goal has already been achieved, call the "achieved" function.
* Always explain your reasoning the "reasoning" argument to the function called.

Goal: 
{goal}
'''

        response = self.model.generate_content(
            [
                system_prompt,
                visible_html,
                genai.types.Image.from_bytes(full_screenshot, 'full_screenshot.jpg'),
                genai.types.Image.from_bytes(viewport_screenshot, 'viewport_screenshot.jpg')
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                candidate_count=1,
            ),
            tools = tools,
            tool_config = tool_config
        )

        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if isinstance(part, genai.types.FunctionCall):
                        return [{"type": "function", "function": {"name": part.name, "arguments": part.args}}]

        return [{"type": "function", "function": {"name": "unreachable"}}]
