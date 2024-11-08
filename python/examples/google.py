from selenium import webdriver
from cerebellum.planners.anthropic import AnthropicPlanner, AnthropicPlannerOptions
from cerebellum.browser import BrowserAgent, BrowserAgentOptions
from cerebellum.utils import pause_for_input


def main():
    driver = webdriver.Chrome()

    try:
        # Set your starting page
        driver.get("https://www.google.com")

        # Define your goal
        goal = "Show me the wikipedia page of the creator of Bitcoin"

        # Configuration options for the planner with debug screenshot enabled
        planner_options = AnthropicPlannerOptions(debug_image_path="llmView.png")

        # Create the Cerebellum browser agent with the configured options
        planner = AnthropicPlanner(planner_options)

        # Browser agent options enabling step-by-step pause
        options = BrowserAgentOptions(
            pause_after_each_action=True  # Enable pausing after each action for manual review
        )

        agent = BrowserAgent(driver, planner, goal, options)

        # Start the automated navigation with pauses at each step
        agent.start()

        # Goal has now been reached, you may interact with the Selenium driver any way you want
        pause_for_input()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
