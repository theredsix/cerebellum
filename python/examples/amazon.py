from selenium import webdriver
from cerebellum.planners.anthropic import AnthropicPlanner
from cerebellum.browser import BrowserAgent, BrowserAgentOptions
from cerebellum.utils import pause_for_input


def main():
    driver = webdriver.Chrome()

    try:
        # Set your starting page
        driver.get("https://www.amazon.com")

        # Pause after initial navigation and use human intervention to solve CAPTCHA if necessary
        pause_for_input()

        # Define your goal
        goal = "Find a USB C to C cable that is 10 feet long and add it to cart"

        options = BrowserAgentOptions(
            additional_instructions=[
                "Do not add to cart directly from search results, click the item text to open item details and then add to cart."
            ]
        )

        # Create the Cerebellum browser agent
        planner = AnthropicPlanner()

        agent = BrowserAgent(driver, planner, goal, options)

        pause_for_input()

        # Have Cerebellum takeover website navigation
        agent.start()

        # Goal has now been reached, you may interact with the Selenium driver any way you want
        pause_for_input()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
