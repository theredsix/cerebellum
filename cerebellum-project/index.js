import("dotenv/config");
import { Builder, Browser } from "selenium-webdriver";
import { AnthropicPlanner, BrowserAgent } from "cerebellum-ai";

(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX).build();
  try {
    await driver.get("https://www.google.com");

    // Define your goal
    const goal = "Show me the wikipedia page of the creator of Bitcoin";

    // Create the Cerebellum browser agent
    const planner = new AnthropicPlanner(process.env.ANTHROPIC_API_KEY);
    const agent = new BrowserAgent(driver, planner, goal);

    // Have Cerebellum takeover website navigation
    await agent.start();

    // Goal has now been reached, you resume control over the browser
    // ...
  } finally {
    await driver.quit();
  }
})();
