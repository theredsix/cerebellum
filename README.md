# Cerebellum AI

Cerebellum AI is a lightweight browser automation tool powered by large language models (LLMs) that accomplishes user-defined goals on webpages using keyboard and mouse actions.

[![Google Example Video](https://github.com/user-attachments/assets/00278da9-1c89-40a4-b72e-8c853c8c003c)](https://github.com/user-attachments/assets/811a64e2-b3d7-408c-bac2-c9bc3bd78f51)

## Quick Start

Install dependencies:
```bash
npm i cerebellum-ai
```

Ensure you have [Selenium Webdrivers](https://www.npmjs.com/package/selenium-webdriver) installed for the browser you want to automate 

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
