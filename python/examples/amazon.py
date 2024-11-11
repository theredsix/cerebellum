from seleniumbase import get_driver
from cerebellum import AnthropicPlanner, BrowserAgent, BrowserAgentOptions, pause_for_input

def main():
    driver = get_driver(
        undetectable=True,
    )

    try:
        # Set your starting page
        driver.uc_open_with_reconnect("https://www.google.com", 4)

        # Create the planner
        planner = AnthropicPlanner()

        # Define your goal
        goal1 = "Search for amazon.com and click a link for the Amazon homepage."
        options = BrowserAgentOptions(pause_after_each_action=False)
        agent1 = BrowserAgent(driver, planner, goal1, options)
        agent1.start()
        # Page is now at www.amazon.com

        # Find a USB cable
        goal2= "Find a USB C to C cable that is 10 feet long and the overall pick and show the item details."
        agent2 = BrowserAgent(driver, planner, goal2, options)
        agent2.start()

        # Add it to cart
        goal3 = "Add the shown item to cart"
        agent3 = BrowserAgent(driver, planner, goal3, options)
        agent3.start()

        # Goal has now been reached, you may interact with the Selenium driver any way you want
        pause_for_input()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
