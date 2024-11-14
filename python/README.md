# Cerebellum (Python)

This is a Python implementation of Cerebellum, a lightweight browser automation agent that accomplishes user-defined goals using keyboard and mouse actions.

## See It In Action

Goal: `Show me the wikipedia page of the creator of Bitcoin`

[![Python Google Example Video](https://github.com/user-attachments/assets/f8b55647-9f06-4cef-81a2-ea72f4cc6e6b)](https://github.com/user-attachments/assets/f8b55647-9f06-4cef-81a2-ea72f4cc6e6b)

## Setup

1. Install the package from pypi.

   ```bash
   pip install cerebellum
   ```

2. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key'
   ```

3. Import module and use.

   ```python
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

   ```

## Running the Example

The example script demonstrates searching for Bitcoin's creator on Google and navigating to their Wikipedia page:

```bash
python examples/google.py
```

## Project Structure

The Python implementation consists of three main modules:

### browser.py
- Contains the core `BrowserAgent` class that manages browser automation
- Handles state management and action execution
- Coordinates between the webdriver and action planner

### utils.py
- Provides utility functions for keyboard input parsing
- Handles terminal input for interactive sessions
- Converts between different coordinate systems

### planners/anthropic.py
- Implements the `AnthropicPlanner` class using Claude 3.5 Sonnet
- Manages communication with Anthropic's API
- Processes screenshots and coordinates browser actions

