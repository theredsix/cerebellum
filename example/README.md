## Running Examples

1. Pull the repo from github.

    ```git clone git@github.com:theredsix/cerebellum.git```

2. `cd` into the directory

    ```cd cerebellum```

3. Install dependencies

    ```npm install```

4. Run the google.ts example.

    ```npx tsx example/google.ts```

### Initializing with a user profile

Many websites such as Amazon have bot detection and will throw up a CAPTCHA once Selenium is detected. It is recommended you use the `pauseForInput()` function for human intervention or load a human user profile to circumvent the CAPTCHA check.

To load a user profile:

* Chrome:
    ```typescript
    import { Options } from 'selenium-webdriver/chrome';

    const options = new Options();
    options.addArguments("user-data-dir=/path/to/your/custom/profile");
    let driver = await new Builder().forBrowser(Browser.CHROME)
        .setChromeOptions(options)
        .build();

    ```

* Firefox:
    ```typescript
    import { Options } from 'selenium-webdriver/firefox';

    const options = new Options();
    let profile = '/path to custom profile';
    options.setProfile(profile);
    let browser = await new Builder().forBrowser(Browser.FIREFOX)
        .setFirefoxOptions(options)
        .build();
    ```    

### Note

LLM computer use is still in its infancy and the examples in the folder may exhibit flaky behavior.