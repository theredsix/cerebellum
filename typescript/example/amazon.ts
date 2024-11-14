import { Builder, Browser } from 'selenium-webdriver';

import { AnthropicPlanner, BrowserAgentOptions, BrowserAgent, pauseForInput } from 'cerebellum-ai';


(async function example() {
  let driver = await new Builder().forBrowser(Browser.CHROME).build();

  try {
    // Set your starting page
    await driver.get('https://www.amazon.com');

    // Pause after initial navigation and use human intervention to solve CAPTCHA if necessary
    await pauseForInput();
    
    // Define your goal
    const goal = 'Find a USB C to C cable that is 10 feet long and add it to cart.';

    const options: BrowserAgentOptions = {
      additionalInstructions: [
        'Do not add to cart directly from search results, click the item text to open item details and then add to cart.'
      ]
    }
    
    // Create the Cerebellum browser agent
    const planner = new AnthropicPlanner({ 
      apiKey: process.env.ANTHROPIC_API_KEY as string,
      mouseJitterReduction: 10,
    });

    const agent = new BrowserAgent(driver, planner, goal, options);

    await pauseForInput();

    // Have Cerebellum takeover website navigation
    await agent.start();

    // Goal has now been reached, you may interact with the Selenium driver any way you want
    await pauseForInput();
  } finally {
    await driver.quit();
  }
})();