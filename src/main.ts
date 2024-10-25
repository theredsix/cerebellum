import { Builder, Browser, By, Key, until } from 'selenium-webdriver';
import { ServiceBuilder } from 'selenium-webdriver/firefox';

(async function example() {
  let driver = await new Builder().forBrowser(Browser.FIREFOX).setFirefoxService(new ServiceBuilder('/snap/bin/geckodriver')).build()
  try {
    await driver.get('https://www.google.com/ncr')
    await driver.findElement(By.name('q')).sendKeys('webdriver', Key.RETURN)
    await driver.wait(until.titleIs('webdriver - Google Search'), 1000)
  } finally {
    await driver.quit()
  }
})()