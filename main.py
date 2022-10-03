import time
import re
from playwright.sync_api import Page, expect


def test_homepage_has_Playwright_in_title_and_get_started_link_linking_to_the_intro_page(page: Page):
    # chromium.launch(headless=False, slow_mo=100)

    page.goto("https://www.instagram.com/")

    # Expect a title "to contain" a substring.
    expect(page).to_have_title(re.compile("Instagram"))

    # create a locator
    get_started = page.locator("text=Get Started")

    # Expect an attribute "to be strictly equal" to the value.
    expect(get_started).to_have_attribute("href", "/docs/intro")

    # Click the get started link.
    get_started.click()

    # Expects the URL to contain intro.
    expect(page).to_have_url(re.compile(".*intro"))


class BotInstagram():

    def __init__(self):
        self.driver = webdriver.Chrome(executable_path="chromedriver.exe")

    def entrar_link(self, link):
        self.driver.get(link)

    def pegar_link_das_fotos(self):
        os_links = self.driver.find_elements_by_tag_name('a')
        
        todos_os_links = []
        for os_link in os_links:
            href = os_link.get_attribute("href")
            if(href.startswith("https://www.instagram.com/p/")):
                todos_os_links.append(href)
        
        return todos_os_links

    def dar_like(self):
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div[1]/article/div/div[2]/div/div[2]/section[1]/span[1]/button').click()

    def comentar(self, comentario):
        textarea = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div[1]/article/div/div[2]/div/div[2]/section[3]/div/form/textarea')
        time.sleep(1)
        textarea.click()
        time.sleep(1)
        textarea = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div[1]/article/div/div[2]/div/div[2]/section[3]/div/form/textarea')
        time.sleep(1)
        textarea.clear()
        time.sleep(1)
        textarea.send_keys(comentario)
        time.sleep(2)
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div[1]/article/div/div[2]/div/div[2]/section[3]/div/form/button[2]').click()
