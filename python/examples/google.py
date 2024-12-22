from seleniumbase import get_driver
from cerebellum import vLLMPlanner, vLLMPlannerOptions, BrowserAgent, BrowserAgentOptions, pause_for_input

def main():
    driver = get_driver()

    try:
        # Set your starting page
        driver.get("https://www.google.com")

        # Define your goal
        goal = "Show me the wikipedia page of the creator of Bitcoin"

        options = vLLMPlannerOptions(
            model="Qwen2-VL-7B-Instruct",
            server="http://localhost:8000",
            debug_image_path='debug.png'
        )

        # Create the Cerebellum browser agent
        planner = vLLMPlanner(options)

        options = BrowserAgentOptions(pause_after_each_action=True)

        agent = BrowserAgent(driver, planner, goal, options)

        # pause_for_input()
        # Have Cerebellum takeover website navigation
        agent.start()

        # Goal has now been reached, you may interact with the Selenium driver any way you want
        pause_for_input()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
