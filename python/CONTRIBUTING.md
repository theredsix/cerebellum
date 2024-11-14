# Contributing

Contributions are welcome, especially if the contribution helps to advance one or more roadmap items.

## Development

1. Clone repository

2. CD into the `/python` folder

3. Install [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#getting-pyenv) and set Python 3.11 as the local version:
   ```bash
   pyenv install 3.11.0
   pyenv virtualenv 3.11.0 cerebellum
   pyenv activate cerebellum
   ```

4. Install Poetry using pip:
   ```bash
   pip install poetry
   ```

5. Install dependencies:
   ```bash
   poetry install --with dev
   ```

6. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key'

7. Run tests:
   ```bash
   pytest
   ```

7. Run the google example
   ```bash
   python example/google.py
   ```

For more examples and detailed API documentation, refer to the [root README](../README.md).
