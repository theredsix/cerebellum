import { Builder, Browser } from 'selenium-webdriver';
import { ServiceBuilder } from 'selenium-webdriver/firefox';

import { AnthropicPlanner } from '../src/planners/anthropic';

import { BrowserAgent } from '../src/browser';
import { pauseForInput } from '../src/util';

const planner = new AnthropicPlanner(undefined);

(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX).setFirefoxService(new ServiceBuilder('/snap/bin/geckodriver')).build();
  try {
    await driver.get('https://www.google.com');

    const goal = 'Show me the wikipedia page of the creator of Bitcoin';

    const agent = new BrowserAgent(driver, planner, goal);

    await agent.start();

    await pauseForInput();
    
  } finally {
    await driver.quit();
  }
})();