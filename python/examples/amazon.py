from selenium import webdriver
from cerebellum.planners.anthropic import AnthropicPlanner, AnthropicPlannerOptions
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

        # Browser agent options with additional instructions and enabling step-by-step pause
        options = BrowserAgentOptions(
            additional_instructions=[
                "Do not add to cart directly from search results, click the item text to open item details and then add it to cart."
            ],
            pause_after_each_action=True,  # Enable pausing after each action for manual review
        )

        # Configuration options for the planner with debug and screenshot history enabled
        planner_options = AnthropicPlannerOptions(
            debug_image_path="test.jpg",
            screenshot_history=5,  # Assuming a history of 5 screenshots is sufficient for debugging
        )

        # Create the Cerebellum browser agent with the configured options
        planner = AnthropicPlanner(planner_options)

        agent = BrowserAgent(driver, planner, goal, options)

        # Start the automated navigation with pauses at each step
        agent.start()

        # Goal has now been reached, you may interact with the Selenium driver any way you want
        pause_for_input()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
