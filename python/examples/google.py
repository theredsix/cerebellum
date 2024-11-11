from seleniumbase import get_driver
from cerebellum import AnthropicPlanner, BrowserAgent, BrowserAgentOptions, pause_for_input

def main():
    driver = get_driver()

    try:
        # Set your starting page
        driver.get("https://www.google.com")

        # Define your goal
        goal = "Show me the wikipedia page of the creator of Bitcoin"

        # Create the Cerebellum browser agent
        planner = AnthropicPlanner()

        options = BrowserAgentOptions(pause_after_each_action=True)

        agent = BrowserAgent(driver, planner, goal, options)
        agent.pause_after_each_action = False

        pause_for_input()
        # Have Cerebellum takeover website navigation
        agent.start()

        # Goal has now been reached, you may interact with the Selenium driver any way you want
        pause_for_input()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
