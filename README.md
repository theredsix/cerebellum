# Cerebellum

Cerebellum is a lightweight browser automation tool powered by large language models (LLMs) that accomplishes user-defined goals on webpages using keyboard and mouse actions.

[![Google Example Video](https://github.com/user-attachments/assets/00278da9-1c89-40a4-b72e-8c853c8c003c)](https://github.com/user-attachments/assets/811a64e2-b3d7-408c-bac2-c9bc3bd78f51)

## Quick Start

Install dependencies:
```bash
npm i cerebellum-ai
```

Ensure you have [Selenium Webdrivers](https://www.npmjs.com/package/selenium-webdriver) installed for the browser you want to automate. 

Run the example:
```typescript
import { Builder, Browser } from 'selenium-webdriver';

import { AnthropicPlanner, BrowserAgent, pauseForInput } from 'cerebellum-ai';


(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX);
  try {
    await driver.get('https://www.google.com');
    
    // Define your goal
    const goal = 'Show me the wikipedia page of the creator of Bitcoin';
    
    // Create the Cerebellum browser agent
    const planner = new AnthropicPlanner(process.env.ANTHROPIC_API_KEY as string);
    const agent = new BrowserAgent(driver, planner, goal);

    // Have Cerebellum takeover website navigation
    await agent.start();

    // Goal has now been reached, you resume control over the browser
    // ...
    
  } finally {
    await driver.quit();
  }
})();
```

## Examples

See the `/example` folder for more usage examples including form filling and prompt instruction tuning.

## Flexibility and Integration

Cerebellum is designed to work with a large swath of scenarios. Key features include:

1. Hybrid Control: Easily switch between human, AI, and automated control during a browsing session.
2. Wide Browser Support: Compatible with any Selenium-supported browser, expanding its use beyond traditional web automation.
3. Diverse Applications: 
   - Enhance Electron applications with AI-assisted interactions
   - Augment human browsing sessions with intelligent automation
   - Enable fully autonomous web navigation and task completion

This flexibility makes Cerebellum a powerful tool for a wide range of scenarios, from assisting users with complex web tasks to fully automating web-based workflows.

## How it works

Cerebellum models web interactions as navigation through a directed graph. Each webpage state represents a node in this graph, encompassing both visible elements and underlying data. User actions, such as clicking or typing, function as edges that transition between nodes.

The process begins at an initial node representing the starting webpage. Cerebellum's objective is to find an optimal path to a goal node that signifies task completion. As it progresses, the system discovers new nodes by analyzing page screenshots and identifying interactive elements.

A Large Language Model (LLM) serves as the decision-making component, evaluating the current state and determining the next action. This approach enables Cerebellum to adapt to changing web environments and make informed decisions in real-time.

The system's design allows for continuous improvement. Successful navigation sessions can be used to fine-tune the LLM's performance on similar tasks.

## Class Abstractions

Cerebellum AI is built on two main class abstractions: `BrowserAgent` and `ActionPlanner`.

### BrowserAgent

The `BrowserAgent` class is responsible for interacting with the web browser. It:

- Controls the Selenium WebDriver
- Captures screenshots of the current webpage
- Executes actions (like clicking, typing, etc) based on instructions from the ActionPlanner
- Provides feedback to the ActionPlanner about the current state of the webpage

### ActionPlanner

The `ActionPlanner` is an abstract class that defines the interface for different planning strategies. It:

- Receives the current state of the webpage (including screenshots)
- Analyzes the state and determines the next action to take
- Provides instructions to the BrowserAgent on what action to perform next
- TODO: Convert browsing sessions into a training dataset

Currently, Cerebellum AI only implements the `AnthropicPlanner`, which uses the Claude 3.5 Sonnet model from Anthropic to make decisions. Nevertheless, this abstraction allows for easy integration of other planning strategies in the future, such as local models or other LLM providers.

The separation of `BrowserAgent` and `Planner` allows for a clear division of responsibilities:
- The `BrowserAgent` handles the "how" of interacting with the browser
- The `Planner` decides the "what" and "why" of the actions to be taken

## Roadmap

- [x] Integrate Claude 3.5 Sonnet as a `ActionPlanner`
- [x] Demonstrate successful `BrowserAgent` across a variety of tasks
- [ ] Improve system prompt performance
- [ ] Improve mouse position marking on screenshots
- [ ] Add ability for converting browser sessions into training datasets
- [ ] Train a local model
- [ ] Integrate local model as a `ActionPlanner`

## Contributing

We welcome contributions to Cerebellum! For more detailed information on how to contribute, please see our [CONTRIBUTING.md](CONTRIBUTING.md) file.

We appreciate all contributions, whether they're bug reports, feature requests, or code changes. 

## License

This project is licensed under the [MIT License](LICENSE).


## Acknowledgements

This project was inspired by the following:

- [Claude Computer Use](https://www.anthropic.com/news/3-5-models-and-computer-use)
- [Agent.exe](https://github.com/corbt/agent.exe)
- [Skyvern](https://github.com/Skyvern-AI/skyvern)

## Maintainer

* [Han Wang](mailto:han.wang.2718@gmail.com)

## Collaborators

* Han Wang
* Darwin Lo
* Michael Shuffett
