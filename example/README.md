## Running Examples

1. Pull the repo from github.

    ```git clone git@github.com:theredsix/cerebellum.git```

2. `cd` into the directory

    ```cd cerebellum```

3. Install dependencies

    ```npm install```

4. Run the google.ts example.

    ```npx tsx example/google.ts```

### CAPTCHA Issues

Many websites such as Amazon have bot detection and will throw up a CAPTCHA once Selenium is detected. It is recommended you use the `pauseForInput()` function for human intervention or load a user profile to circumvent the CAPTCHA check.

E.g. `chrome` supports loading of user profiles with the `--profile-directory` argument. https://developer.chrome.com/docs/chromedriver/capabilities



### Note

LLM computer use is still in its infancy and the examples in the folder may exhibit flaky behavior.