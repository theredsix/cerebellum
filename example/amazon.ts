import { Builder, Browser } from 'selenium-webdriver';
import { ServiceBuilder } from 'selenium-webdriver/firefox';

import { AnthropicPlanner } from '../src/anthropic';

import { BrowserAgent } from '../src/browser';
import { pauseForInput } from '../src/util';

const planner = new AnthropicPlanner(undefined);

(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX).setFirefoxService(new ServiceBuilder('/snap/bin/geckodriver')).build();
  try {
    await driver.get('https://www.amazon.com');
    const agent = new BrowserAgent(driver, planner, 'Find a USB C cable over 10 feet and add it to cart');

    await agent.start();

    await pauseForInput();
  } finally {
    await driver.quit();
  }
})();