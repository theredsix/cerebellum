import { Builder, Browser } from 'selenium-webdriver';
import { ServiceBuilder } from 'selenium-webdriver/firefox';

import { AnthropicPlanner } from '../src/planners/anthropic';

import { BrowserAgent } from '../src/browser';
import { pauseForInput } from '../src/util';

const planner = new AnthropicPlanner(undefined);

(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX).setFirefoxService(new ServiceBuilder('/snap/bin/geckodriver')).build();
  try {
    await driver.get('https://www.amazon.com');

    const goal = 'Find a USB C cable that is 10 feet long and add it to cart';

    const agent = new BrowserAgent(driver, planner, goal);

    await agent.start();

    await pauseForInput();
  } finally {
    await driver.quit();
  }
})();