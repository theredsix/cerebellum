# Cerebellum

A lightweight browser using agent that accomplishes user-defined goals on webpages using keyboard and mouse actions.

[![Google Example Video](https://github.com/user-attachments/assets/811a64e2-b3d7-408c-bac2-c9bc3bd78f51)](https://github.com/user-attachments/assets/a0295ddb-6969-4946-a4ef-e0566730acee)

## How It Works

1. Web browsing is simplified to navigating a directed graph.
2. Each webpage is a node with visible elements and data.
3. User actions, such as clicking or typing, are edges that move between nodes.
4. Cerebellum starts at a webpage and aims to reach a target node that embodies the completed goal.
5. It uses a LLM to finds new nodes by analyzing page content and interactive elements.
6. The LLM decides the next action based on the current state and past actions.
7. Cerebellum executes the LLM's planned action and feeds the new state back into the LLM for next step.
8. The process ends when the LLM decides the goal has been reached or is unachieveable.

*Currently, Claude 3.5 Sonnet is the only supported LLM*

## Features

* Compatible with any Selenium-supported browser.
* Fills forms using user-provided JSON data.
* Accepts runtime instructions to dynamically adjust browsing strategies and actions.
* TODO: Create training datasets from browsing sessions

## Setup

1. Set up your Anthropic API key and add the `ANTHROPIC_API_KEY` environment variable.

2. Install Cerebellum and [Selenium](https://www.npmjs.com/package/selenium-webdriver) from npm:

    ```
    npm i cerebellum-ai selenium-webdriver
    ```

3. Setup Selenium webdriver for the browser you want to automate.
    * MacOS: 
      * Chrome: `brew install chromedriver`
      * Firefox: `brew install geckodriver`   
    * Linux/Windows:
      * Please follow the instructions on the Selenium package: https://www.npmjs.com/package/selenium-webdriver

4. Create a Selenium webdriver instance to use in your code.

    ```typescript
    import { Builder, Browser } from 'selenium-webdriver';

    const browser = await new Builder().forBrowser(Browser.CHROME).build();   
    ```

5.  Use Cerebellum to accomplish a goal on a website.

    ```typescript
    // Point the browser to a website
    await browser.get('https://www.google.com');
    
    // Define your goal
    const goal = 'Show me the wikipedia page of the creator of Bitcoin';
    
    // Set your Anthropic API key
    const anthropicApiKey = process.env.ANTHROPIC_API_KEY as string;

    // Initialize ActionPlanner with LLM
    const planner = new AnthropicPlanner({ apiKey: anthropicApiKey });

    // Initialize BrowserAgent to tie together the browser, planner and goal
    const agent = new BrowserAgent(browser, planner, goal);

    // Start the automated navigation process
    await agent.start();

    /**
     * Goal has now been accomplish on 'browser', navigation state saved in 'agent'
     **/
    ```

## Examples

Check out the [/example](/example) folder for more use cases, including form filling and prompt instruction tuning.

## Usage

Cerebellum is built on two main class abstractions: `BrowserAgent` and `ActionPlanner`.
- The `BrowserAgent` handles the "how" of interacting with the browser
- The `ActionPlanner` decides the "what" and "why" of the actions to be taken

### ActionPlanner

The ActionPlanner is an abstract class that plans navigation strategies:

- Receives the current state of the webpage (including screenshots).
- Analyzes the state and determines the next action.
- Instructs the BrowserAgent on what action to take.
- TODO: Convert browsing sessions into training datasets.

*Currently, Cerebellum only implements `AnthropicPlanner`, using the Claude 3.5 Sonnet model from Anthropic to make decisions.*

```typescript
  const planner = AnthropicPlanner(options?: AnthropicPlannerOptions)
```

#### AnthropicPlannerOptions

The `AnthropicPlannerOptions` interface provides configuration options for customizing the behavior of the `AnthropicPlanner`. These options allow you to fine-tune how the planner interacts with the Anthropic API and processes browser actions:

- **apiKey**: A string representing the API key for accessing the Anthropic services. This key is necessary for authenticating requests to the Anthropic API. 

- **client**: An instance of the `Anthropic` client. If provided, this client will be used for making API calls. If not provided, a new client will be instantiated using the `apiKey`. 

- **screenshotHistory**: A number indicating how many screenshots should be sent to the LLM. Screenshots are always counted from newest to oldest. Default: `1`

- **mouseJitterReduction**: A number that specifies the level of reduction applied to mouse jitter. A mouse movement that shifts the mouse less than `mouseJitterReduction` pixels in both horizontal and vertical directions will be translated to a `left_click` action. This helps stop infinite loops. Default: `5`

- **debugImagePath**: A string specifying the file path where debug images should be saved. This is useful for visual debugging and analysis of the planner's actions. If not set, debug images will not be saved. Default: `undefined`


### BrowserAgent

The BrowserAgent class manages interactions with the browser, including:

- Controlling the Selenium WebDriver.
- Capturing screenshots of the current webpage.
- Executing actions (e.g., clicking, typing) based on instructions from the ActionPlanner.

```typescript
  const agent = BrowserAgent(
    browser: WebDriver, 
    actionPlanner: ActionPlanner, 
    goal: string, 
    options?: BrowserAgentOptions)
```

#### BrowserAgentOptions

The `BrowserAgentOptions` interface provides several configuration options to customize the behavior of the `BrowserAgent`:

- **additionalContext**: This can be a string or an object. It represents data that should be referenced for forms or navigation. This context can be used to provide additional information that might be necessary for the `ActionPlanner` to make informed decisions. Default: `none`

- **additionalInstructions**: An array of strings that can be used to pass extra instructions to the `ActionPlanner`. These instructions can guide the planner on specific actions or strategies to employ during the browsing session. Default: `[]`

- **waitAfterStepMS**: A number representing the milliseconds to wait after each step or action is performed. This can be useful for simulating more human-like interaction speeds or for ensuring that the webpage has enough time to update after an action. Default: `500`

- **pauseAfterEachAction**: A boolean indicating whether the `BrowserAgent` should pause and wait for a keyboard input after each action. This can be useful for debugging or for scenarios where manual intervention might be needed between actions. Default: `false`


## Roadmap

- [x] Integrate Claude 3.5 Sonnet as a `ActionPlanner`
- [x] Demonstrate successful `BrowserAgent` across a variety of tasks
- [ ] Create Python SDK
- [ ] Improve vertical scrolling behavior
- [ ] Improve horizontal scrolling behavior
- [ ] Improve system prompt performance
- [ ] Improve mouse position marking on screenshots
- [ ] Add ability for converting browser sessions into training datasets
- [ ] Support for additional LLMs as an `ActionPlanner`
- [ ] Train a local model
- [ ] Integrate local model as a `ActionPlanner`

## Known Issues

* Claude 3.5 safety refusals
  * Refuses to solve CAPTCHAs
  * Refuses to navigate when political content is on the page

## Contributing

Contributions to Cerebellum are welcome. For details on how to get involved, please refer to our [CONTRIBUTING.md](CONTRIBUTING.md).

We appreciate all contributions, whether they're bug reports, feature requests, or code changes.

## License

This project is licensed under the [MIT License](LICENSE).


## Acknowledgements

This project was inspired by the following:

- [Claude Computer Use](https://www.anthropic.com/news/3-5-models-and-computer-use)
- [Agent.exe](https://github.com/corbt/agent.exe)
- [Skyvern](https://github.com/Skyvern-AI/skyvern)

## Maintainer

* [Han Wang](https://github.com/theredsix)

## Collaborators

* Han Wang
* Darwin Lo
* Michael Shuffett
