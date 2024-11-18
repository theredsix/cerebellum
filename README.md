# Cerebellum

A lightweight browser using agent that accomplishes user-defined goals on webpages using keyboard and mouse actions.

## See It In Action

Goal: `Find a USB C to C cable that is 10 feet long and add it to cart`

[![Google Example Video](https://github.com/user-attachments/assets/811a64e2-b3d7-408c-bac2-c9bc3bd78f51)](https://github.com/user-attachments/assets/7a8500c9-35f4-45d3-bc0c-a765bc4aee6a)

## Setup

Please see setup directions for your language:

* [Python](/python/README.md#setup)
* [Typescript](/typescript/README.md#setup)

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

## Roadmap

- [x] Integrate Claude 3.5 Sonnet as a `ActionPlanner`
- [x] Demonstrate successful `BrowserAgent` across a variety of tasks
- [x] Create Python SDK
- [x] Handle tabbed browsing
- [ ] Handle data extraction from website
- [x] Improve vertical scrolling behavior
- [ ] Improve horizontal scrolling behavior
- [x] Improve system prompt performance
- [x] Improve mouse position marking on screenshots
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

## Maintainer

* [Han Wang](https://github.com/theredsix)

## Collaborators

* [Han Wang](https://github.com/theredsix)
* [Darwin Lo](https://github.com/thefireskater)
* [Michael Shuffett](https://github.com/mshuffett)
* [Shane Moran](https://github.com/scm-aiml)
