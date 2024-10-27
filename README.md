# Cerebellum

Cerebellum is a lightweight browser automation tool powered by large language models (LLMs) that accomplishes user-defined goals on webpages using keyboard and mouse actions.

[![Google Example Video](https://github.com/user-attachments/assets/00278da9-1c89-40a4-b72e-8c853c8c003c)](https://github.com/user-attachments/assets/811a64e2-b3d7-408c-bac2-c9bc3bd78f51)

## Quick Start

Install dependencies:
```bash
npm i cerebellum-ai
```

Ensure you have [Selenium Webdrivers](https://www.npmjs.com/package/selenium-webdriver) installed for the browsers you want to automate. 

```typescript
import { Builder, Browser } from 'selenium-webdriver';

import { AnthropicPlanner, BrowserAgent } from 'cerebellum-ai';


(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX).build();
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

Check out the [/example](/example) folder for more use cases, including form filling and prompt instruction tuning.

## Flexibility and Integration

Cerebellum is designed to work with a large swath of scenarios. Key features include:

1. Hybrid Control: Switch seamlessly between human, AI, and automated control during a browsing session.
2. Wide Browser Support: Compatible with any Selenium-supported browser.
3. Diverse Applications: 
   - Augment Electron applications with AI-assisted interactions.
   - Enhance human browsing sessions with intelligent automation.
   - Enable fully autonomous web navigation and task completion.
   
This flexibility makes Cerebellum a powerful tool for tasks ranging from assisting users with complex workflows to fully automating web-based processes.

## How it works

Cerebellum implicitly models web interactions as navigation through a directed graph. Each webpage represents a node, encompassing both visible elements and underlying data. User actions, like clicking or typing, serve as edges that transition between nodes.

Starting at an initial webpage, Cerebellum's objective is to find an optimal path to a target node that completes the task. It discovers new nodes by analyzing page content and identifying interactive elements.

A Large Language Model (LLM) powers decision-making, evaluating the current state and determining the next action. This approach allows Cerebellum to adapt to changing environments and make informed, real-time decisions.

The system continuously improves by learning from successful sessions, fine-tuning the LLM for similar tasks.

## Class Abstractions

Cerebellum is built on two main class abstractions: `BrowserAgent` and `ActionPlanner`. The separation of `BrowserAgent` and `Planner` allows for a clear division of responsibilities:
- The `BrowserAgent` handles the "how" of interacting with the browser
- The `ActionPlanner` decides the "what" and "why" of the actions to be taken

#### BrowserAgent

The BrowserAgent class manages interactions with the browser, including:

- Controlling the Selenium WebDriver.
- Capturing screenshots of the current webpage.
- Executing actions (e.g., clicking, typing) based on instructions from the ActionPlanner.

#### ActionPlanner

The ActionPlanner is an abstract class that defines the interface for planning strategies:

- Receives the current state of the webpage (including screenshots).
- Analyzes the state and determines the next action.
- Instructs the BrowserAgent on what action to take.
- TODO: Convert browsing sessions into training datasets.

This abstraction allows for easy integration of other planning strategies in the future, such as local models or different LLM providers.

**Currently, Cerebellum only implements `AnthropicPlanner`, using the Claude 3.5 Sonnet model from Anthropic to make decisions.**

## Roadmap

- [x] Integrate Claude 3.5 Sonnet as a `ActionPlanner`
- [x] Demonstrate successful `BrowserAgent` across a variety of tasks
- [ ] Create Python SDK
- [ ] Improve vertical scrolling behavior
- [ ] Improve horizontal scrolling behavior
- [ ] Improve system prompt performance
- [ ] Improve mouse position marking on screenshots
- [ ] Add ability for converting browser sessions into training datasets
- [ ] Support for additional LLMs as an `ActionPlanner`
- [ ] Train a local model
- [ ] Integrate local model as a `ActionPlanner`

## Contributing

We welcome contributions to Cerebellum! For details on how to get involved, please refer to our [CONTRIBUTING.md](CONTRIBUTING.md).

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
