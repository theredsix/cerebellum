import { Builder, Browser } from 'selenium-webdriver';
import { ServiceBuilder } from 'selenium-webdriver/firefox';

import { AnthropicPlanner, BrowserAgent, pauseForInput } from 'cerebellum-ai';
import { BrowserAgentOptions } from '../src/browser';


(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX).setFirefoxService(new ServiceBuilder('/snap/bin/geckodriver')).build();
  try {
    await driver.get('https://www.irs.gov/');
    await pauseForInput();
    
    // Define your goal
    const goal = 'Check my refund status.';

    // Define additional data
    const userData = {
        "social_security_number": "123-45-1425",
        "tax_year": 2023,
        "filing_status": "married",
        "refund_amount": 234
    };

    const options: BrowserAgentOptions = {
        additionalContext: userData,
        waitAfterStepMS: 1000,
    }
    
    // Create the Cerebellum browser agent
    const planner = new AnthropicPlanner(process.env.ANTHROPIC_API_KEY as string);
    const agent = new BrowserAgent(driver, planner, goal, options);

    // Have Cerebellum takeover website navigation
    await agent.start();

    // Goal has now been reached, you may interact with the Selenium driver any way you want
    await pauseForInput();
    
  } finally {
    await driver.quit();
  }
})();