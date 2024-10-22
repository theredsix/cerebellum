# Cerebellum Browser Automation

## Quickstart

```python
from cerebellum.browser.planner import GeminiBrowserPlanner
from cerebellum.browser.session import BrowserSession
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True)
    page = context.new_page()
    page.goto("https://www.amazon.com/")

    goal = "Add a USB C to USB C cable to cart"

    planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'])
    session = BrowserSession(goal, page, planner=planner)

    session.start()
```

## Overview

Cerebellum is an AI-driven browser automation system that uses large language models and planning to navigate web pages and achieve specific goals, providing a flexible, intelligent alternative to traditional rule-based automation.

## Features

- **AI-driven planning for navigating web pages**
- **Playwright-based browser control**
- **Vision-capable mode for image-based actions**
- **Local LLM integration for privacy**
- **Extensible for adding custom capabilities**
- **Apache 2.0 License**

## Why Cerebellum?

Cerebellum aims to make web interactions for AI as intuitive as human actions, serving as a bridge between AI decision-making and browser interactions.

Key benefits:

1. **Chainable**: Cerebellum allows multiple small or medium-sized goals to be chained together in series to achieve a final task. This chainability enables a human or a frontier model to plan an execution route, breaking down complex workflows into manageable steps. For example, Cerebellum can first log in to an e-commerce site, then search for a specific product, add it to the cart, and finally proceed to checkout. Each of these steps can be defined as separate goals, chained in sequence, allowing for a flexible and coordinated execution of complex tasks.
2. **Interoperability:** Cerebellum allows seamless integration between AI-driven automation, human intervention, and traditional rule-based automation. The Playwright page object can be handed off between different control mechanisms, enabling a smooth transition from AI-driven actions to manual human input or conventional scripted automation. This flexibility allows for robust handling of complex tasks where certain parts may benefit from direct human oversight or specific rule-based scripts, enhancing reliability and adaptability in web automation workflows.
3. **Human Knowledge Transcription**: Tools for supervising and creating "golden" sessions to improve AI performance. These tools include features for recording browser sessions and converting them into fine-tuning examples, making it easier to enhance the LLM's capabilities with real-world browsing data.

## Installation

Install from local source by navigating to the root directory and running:

```sh
conda develop ./cerebellum
# or
pip install -e ./cerebellum
```

For local LLM planners, also install [guidance](https://github.com/guidance-ai/guidance) and [llama-cpp-python](https://github.com/abetlen/llama-cpp-python).

## How it works

Cerebellum models web interactions as pathfinding on a directed graph. The state of a webpage is represented as nodes on an infinite graph, with each node capturing the current webpage state, including client-side and server-side information. Actions like clicking a button, filling out a form, or navigating to a new page are edges that transition the state from one node to another.

The process starts with a node representing the initial webpage state, aiming to find an optimal path to a terminal node that signifies goal completion. Each action transitions the webpage state along the graph's edges.

Neighboring nodes are discovered at runtime by analyzing the DOM structure to find interactable elements, like buttons, links, and input fields. These elements are mapped as possible actions that transition the state to new nodes, allowing the system to determine the next steps toward the goal.

The Large Language Model (LLM) planner acts as a heuristic, analyzing the current state, evaluating actions, and selecting the most promising next step. As Cerebellum interacts with the webpage, it updates its understanding of the graph structure, adapting to changes or new information.

This adaptive navigation allows Cerebellum to respond dynamically to changes in the webpage, making real-time decisions. Successful navigation sessions are used to fine-tune the LLM, improving its ability to handle similar tasks. By modeling web interactions in this way, Cerebellum offers a flexible approach to automating complex tasks in dynamic environments.

## Components

- `LocalLLMBrowserPlanner`: Generates browser actions.
- `ExtendedLlama3ChatTemplate`: Custom LLM interaction template.
- `BrowserState`, `BrowserAction`, `BrowserActionResult`: Core data structures.

## Contributing

We welcome contributions! You can help by:

1. **Code Contributions**: Fork the repo, create a branch, and submit a pull request.
2. **Bug Reports**: Report issues on GitHub.
3. **Feature Requests**: Share your ideas for improvements.
4. **Documentation**: Help refine the docs.
5. **Golden Session Files**: Submit `.cere` files for goals where Cerebellum struggles. This will help improve the AI's performance and contribute to fine-tuning efforts.

Refer to our CONTRIBUTING.md for more detailed guidelines.

## License

Apache 2.0
