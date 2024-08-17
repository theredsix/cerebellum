tools = [
             {
                "name": "click",
                "description": "Initial a mouse click on the intended HTML element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": "Specifies the CSS selector of the input element to fill. This string is a CSS selector that can be passed to jQuery. Only supports html tag, class and id attributes. Cannot use descendant, child or sibling selectors.",
                        }
                    },
                    "required": ["reasoning", "css_selector"],
                },
            },
            {
                "name": "fill",
                "description": "Fill in the input field with the specified text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": "Specifies the CSS selector of the input element to fill. This string is a CSS selector that can be passed to jQuery. Only supports html tag, class and id attributes. Cannot use descendant, child or sibling selectors.",
                        },
                        "text": {
                            "type": "string",
                            "description": "The text that should be filled into the input element.",
                        },
                        "press_enter": {
                            "type": "boolean",
                            "description": "If true, the input will be filled and the enter key will be pressed. This is helpful for form or search submissions",
                        },
                    },
                    "required": ["reasoning", "css_selector", "text", "press_enter"],
                },
            },
            {
                "name": "focus",
                "description": "Scroll the viewport to an element, only use this function to display a part of the page to the user. Do not use if you intent to interact with an offscreen element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                        "css_selector": {
                            "type": "string",
                            "description": "Specifies the CSS selector of the input element to fill. This string is a CSS selector that can be passed to jQuery. Only supports html tag, class and id attributes. Cannot use descendant, child or sibling selectors.",
                        },
                    },
                    "required": ["reasoning", "css_selector"],
                },
            },
            {
                "name": "achieved",
                "description": "Call this function when the goal has been achieved.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                    },
                    "required": ["reasoning"],
                },
            },
            {
                "name": "unreachable",
                "description": "Call this function when if you believe the goal cannot be achieved.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Your reasoning on the browsing session thus far and why you believe the current action is the right one",
                        },
                    },
                    "required": ["reasoning"],
                },
            },
        ]