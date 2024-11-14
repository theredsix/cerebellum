import { Builder, Browser } from 'selenium-webdriver';

import { AnthropicPlanner, BrowserAgent, pauseForInput } from 'cerebellum-ai';


(async function example() {
  let driver = await new Builder().forBrowser(Browser.CHROME).build();

  try {
    await driver.get('https://www.google.com');
    
    // Define your goal
    const goal = 'Find flights from Seattle to SF for next Tuesday to Thursday';
    
    // Create the Cerebellum browser agent
    const planner = new AnthropicPlanner({ apiKey: process.env.ANTHROPIC_API_KEY as string});
    const agent = new BrowserAgent(driver, planner, goal, {
      pauseAfterEachAction: false,
    });

    // Have Cerebellum takeover website navigation
    await agent.start();

    // Goal has now been reached, you may interact with the Selenium driver any way you want
    await pauseForInput();
    
  } finally {
    await driver.quit();
  }
})();