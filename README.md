# Cerebellum Browser Automation

## Quickstart

```python
from cerebellum.browser.planner import GeminiBrowserPlanner, HumanBrowserPlanner
from cerebellum.browser.session import BrowserSession
from cerebellum.memory.file import FileSessionMemory
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.tracing.start(screenshots=True)
    page = context.new_page()
    page.goto("https://www.amazon.com/")

    planner = GeminiBrowserPlanner(api_key=os.environ['GEMINI_API_KEY'])

    goal = "Add a USB C to USB C cable to cart"

    session = BrowserSession(goal, page, planner=planner)

    session.start()

```


## Overview
Cerebellum is a browser automation system that uses AI-driven planning to navigate web pages and perform goals. This project combines the power of large language models with browser automation tools to create a flexible and intelligent system for completing goals on websites.

## Why Cerebellum

Cerebellum is named after the part of the brain responsible for coordinating movement and fine motor skills. This analogy is fitting for our project, as Cerebellum aims to provide AI with the ability to navigate and interact with web interfaces as smoothly and intuitively as humans do.

Key reasons for using Cerebellum:

1. **Autonomous Web Interaction**: Cerebellum acts as an AI "cerebellum," enabling AI systems to plan and execute web-based tasks independently, much like how the human cerebellum coordinates physical movements.

2. **Task Granularity**: Designed to handle small to medium-sized tasks, Cerebellum is ideal for operations such as navigating to a user's account profile or adding items to a shopping cart. This allows a frontier model to offload browser actions to Cerebellum.

3. **Bridging AI and Web Interfaces**: Just as the cerebellum connects the brain to limbs, Cerebellum.ai serves as a bridge between AI decision-making capabilities and web browser interactions, treating the browser as a digital limb for AI systems.

4. **Flexible and Intelligent**: By combining AI-driven planning with browser automation, Cerebellum offers a more adaptable and intelligent approach to web interaction compared to traditional, rule-based automation tools.

5. **Support for Complex Workflows**: Cerebellum's ability to understand context and plan actions makes it suitable for navigating complex web applications and multi-step processes, mimicking human-like interaction with web interfaces.

6. **Native Playwright integration** Cerebellum uses Playwright to control the webpages and allows smooth switching to human or rule-based automation control.

7. **Transcribing of human knowledge** Cerebellum comes with tools for supervising and crafting "golden" browsing sessions for easy fine tuning of the underlying LLM planner.

## Features
- AI-driven planning for web navigation
- Support for various browser actions (click, fill, focus, goto)
- Vision-capable mode for image-based decision making
- Local LLM integration for privacy
- Extensible architecture for adding new capabilities

## Installation

To install Cerebellum from local source, cd to git root directory.

`conda develop ./cerebellum` or `pip install -e ./cerebellum`

Online pip and conda instructions will be added once package is published.

#### Local LLM Planner configuration

If you want to use Cerebellum with a local model, please also install [guidance](https://github.com/guidance-ai/guidance) and [llama-cpp-python](https://github.com/abetlen/llama-cpp-python).

## Theory

Cerebellum models webpage interactions as path-finding on a directed graph. This approach provides a structured way to navigate complex web environments and achieve specific goals. Here's a breakdown of the key theoretical components:

1. **Graph Representation**:
   - Nodes: Represent the webpage's state, including both client-side and server-side information.
   - Edges: Represent actions that can be taken, such as clicking, filling forms, or navigating to new pages.

2. **Path-Finding**:
   - Starting Node: The initial webpage state when the task begins.
   - Terminal Nodes: A set of states that represent successful completion of the goal.
   - Objective: Find an optimal path from the starting node to one of the terminal nodes.

3. **LLM Planner as Heuristic**:
   - The Large Language Model (LLM) planner acts as a sophisticated heuristic for navigating the graph.
   - It analyzes the current state, potential actions, and the goal to suggest the most promising next steps.

4. **Adaptive Navigation**:
   - As Cerebellum interacts with the webpage, it updates its understanding of the graph structure.
   - The system can adapt to unexpected changes or new information discovered during navigation.

5. **Fine-Tuning for Optimization**:
   - The underlying LLM can be fine-tuned using successful navigation sessions.
   - This process hones the navigation heuristic, improving efficiency and success rates over time.

By modeling web interactions in this way, Cerebellum can tackle complex, multi-step tasks while maintaining flexibility and adaptability. The integration of AI-driven planning with this graph-based approach allows for intelligent decision-making in dynamic web environments.



## Components
- `LocalLLMBrowserPlanner`: Main planner class that generates browser actions
- `ExtendedLlama3ChatTemplate`: Custom chat template for LLM interactions
- `BrowserState`, `BrowserAction`, `BrowserActionResult`: Core data structures

## Contributing
We welcome contributions to Cerebellum! Here are some ways you can help:

1. **Code Contributions**: If you'd like to contribute code, please fork the repository, create a feature branch, and submit a pull request with your changes.

2. **Bug Reports**: If you encounter any issues, please open a detailed bug report in the GitHub issues section.

3. **Feature Requests**: Have ideas for new features? We'd love to hear them! Open an issue to discuss your proposal.

4. **Documentation**: Help improve our documentation by submitting updates or clarifications.

5. **Golden Session Files**: Cerebellum performs well out of the box for many goals. However, we welcome ".cere" golden session files for goals where Cerebellum is currently unable to achieve the desired outcome. These files will be consolidated in this repository for the community to use in fine-tuning, and will be incorporated into the next official Cerebellum fine-tune. Through the power of open-source collaboration, we aim to curate a fine-tuning dataset that will enable Cerebellum to perform and generalize across all webpages.

To contribute a golden session file:
- Ensure the file is in the correct ".cere" format
- Include a brief description of the goal and the webpage(s) involved
- Submit the file via a pull request to the designated directory in the repository

By contributing golden session files, you're helping to improve Cerebellum's capabilities and benefiting the entire user community. We appreciate your efforts in making Cerebellum more robust and versatile!

Please refer to our CONTRIBUTING.md file for more detailed information on our contribution process and guidelines.


## License
(Add license information here)

## Contact
(Add contact information here)
