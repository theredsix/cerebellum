# Cerebellum AI

Cerebellum AI is a lightweight LLM-based browser automation tool that accomplishes plain text goals on webpages. 

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

import { AnthropicPlanner } from '../src/planners/anthropic';

import { BrowserAgent } from '../src/browser';

const planner = new AnthropicPlanner(undefined);

(async function example() {
  // Setup Selenium  
  let driver = await new Builder().forBrowser(Browser.FIREFOX).build();
  try {
    // Navigate to your inital page
    await driver.get('https://www.google.com');

    // Declare the goal you want to accomplish in this browser session
    const goal = 'Show me the wikipedia page of the creator of Bitcoin'

    // Create the agent
    const agent = new BrowserAgent(driver, planner, goal);

    // Hand over control to Cerebellum
    await agent.start();

    // Do more things with driver now that the goal has been accomplished
    
  } finally {
    await driver.quit();
  }
})();
```

## Example Breakdown

The `example/google.ts` file showcases the basic usage of Cerebellum AI:

## License

MIT

## Maintainer

* [Han Wang](mailto:han.wang.2718@gmail.com)

## Collaborators

* Han Wang
* Darwin Lo
* Michael Shuffett