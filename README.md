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
