import openai
from src.reasoner import Reasoner
from src.openapi import tools

class OpenAIReasoner(Reasoner):
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)


    def get_next_action(self, prompt: str, visible_html: str, viewport_screenshot: str, full_screenshot: str) -> str:
        system_prompt = f'''
You are an expert developer in CSS and HTML with an excellent knowledge of jQuery and CSS selectors.
Given a webpage's HTML and full + viewport screenshot, decide the best action to take to complete the following goal.

Key considerations:
* You are provided with a "viewport" view of the webpage and a full screenshot of the entire webpage. 
* The HTML provided is only of visible elements in the current viewport you may need to scroll the webpage to find the correct interactive elements
* If you believe the goal cannot be achieved, call the "unreachable" function. 
* If you believe the HTML shows that the goal has already been achieved, call the "achieved" function.
* Always explain your reasoning the "reasoning" argument to the function called.

Goal: 
{prompt}
'''

        response = self.client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {
                        "type": "text",
                        "text": visible_html
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{full_screenshot}",
                            "detail": "low"
                        },
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{viewport_screenshot}",
                            "detail": "high"
                        },
                    }
                ]},
            ],
            tools=tools,
            tool_choice="required"
        )

        message = response.choices[0].message
        
        if message.tool_calls and isinstance(message.tool_calls, list) and len(message.tool_calls) > 0:
            return message.tool_calls
        else:
            return [{"type": "function", "function": {"name": "unreachable"}}]
