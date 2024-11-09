# Cerebellum (Python)

This is a Python port of the TypeScript implementation of Cerebellum, a lightweight browser automation agent that accomplishes user-defined goals using keyboard and mouse actions.

## See It In Action

Goal: `Show me the wikipedia page of the creator of Bitcoin`

<video src="etc/screencast/python_bitcoin.mp4" controls></video>

## Setup

1. First, follow the Selenium setup instructions in the [README](../README.md#setup) to install the appropriate webdriver for your browser.

2. Create and activate a conda environment with Python 3.11:
   ```bash
   conda create -n cerebellum python=3.11
   conda activate cerebellum
   ```

3. Install Poetry using pip:
   ```bash
   pip install poetry
   ```

4. Install dependencies:
   ```bash
   poetry install
   ```

   For development dependencies:
   ```bash
   poetry install --with dev
   ```

5. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key'
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

## Development

To run tests:
```bash
poetry run pytest
```

For more examples and detailed API documentation, refer to the [root README](../README.md).
