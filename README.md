# Cerebellum AI

Cerebellum AI is a lightweight browser automation tool powered by large language models (LLMs) that accomplishes user-defined goals on webpages using keyboard and mouse actions.

[![Google Example Video](/etc/image/bitcoin.png)](/etc/screencast/bitcoin.mp4)

## Quick Start

Install dependencies:
```bash
npm i cerebellum-ai
```

Set up your environment:
   - Ensure you have [Selenium Webdrivers](https://www.npmjs.com/package/selenium-webdriver) installed for the browser you want to automate 
   - Set up your Anthropic API key as an environment variable:
     ```
     export ANTHROPIC_API_KEY=your_api_key_here
     ```

Run the example:
```typescript
import { Builder, Browser } from 'selenium-webdriver';
import { ServiceBuilder } from 'selenium-webdriver/firefox';

import { AnthropicPlanner, BrowserAgent, pauseForInput } from 'cerebellum-ai';

const planner = new AnthropicPlanner(process.);

(async function example() {
  // Setup Selenium  
  let driver = await new Builder().forBrowser(Browser.FIREFOX).build(); // Choose your browser
  try {
    // Navigate to your inital page
    await driver.get('https://www.google.com');

    // Declare the goal you want to accomplish in this browser session
    const goal = 'Show me the wikipedia page of the creator of Bitcoin'

    // Create the Cerebellum browser agent
    const planner = new AnthropicPlanner(process.env.ANTHROPIC_API_KEY as string);
    const agent = new BrowserAgent(driver, planner, goal);

    // Have Cerebellum takeover website navigation
    await agent.start();

    // Do more things with driver now that the goal has been accomplished
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