import datetime
import random
import re
import time
from builtins import print
from datetime import datetime
from urllib.parse import unquote

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver


def write_log(filename, content, istimestone):
    if istimestone:
        open(filename, 'a+').write(content.strip() + '\n')
    else:
        open(filename, 'a+').write(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + '    ' + content.strip() + '\n')


def read_proxies_file(file_name):
    """
    Read file ip proxies
    :param file_name:
    :return: list proxies
    """

    lst_prox = []
    for ii in open(file_name, 'r').readlines():
        lst_prox.append(['http://kimnt93:147828@' + ii.strip(), 'https://kimnt93:147828@' + ii.strip()])
    return lst_prox


def process_content(content):
    """
    Clean content before write file
    :param content:
    :return:
    """
    content = re.sub(r'\[\d+\]', '', content)
    content = re.sub(r'\n+', '\n', content)
    content = re.sub(r'Bài liên quan:.*\n', '', content)
    return content.strip()


def login(web_driver):
    account = [i.split("\t") for i in open('account.txt', 'r').readlines()]
    # LOGIN by temp-mail
    web_driver.get('https://auth2.glosbe.com/login')
    while 1:
        acc = random.choice(account)
        try:
            web_driver.find_element_by_css_selector('#username').send_keys(str(acc[0]))
            web_driver.find_element_by_css_selector('#password').send_keys(str(acc[1]))
            web_driver.find_element_by_name('submit').click()
            # pickle.dump( web_driver.get_cookies() , open("cookies.pkl","wb"))
            break

        except NoSuchElementException:
            time.sleep(5)
            web_driver.get('https://auth2.glosbe.com/login')


class Glosbe:
    def __init__(self, existed, crawled, proxies, save_dir):
        self.existed_url = existed
        self.crawled_url = crawled
        self.proxies = proxies
        self.save_dir = save_dir

    def create_driver(self, proxies, indx, adsblock):
        """
        Create config firefox browser
        :param indx: index to get proxy in list
        :param adsblock: Just install first time
        :param proxies: list ip proxies
        :return:
        """
        # print(random_proxy)
        random_proxy = self.proxies[indx % len(proxies)]
        profile = webdriver.FirefoxProfile()
        profile.set_preference("http.response.timeout", 13)
        profile.set_preference("dom.max_script_run_time", 13)

        # try:
        #     response = requests.get('https://glosbe.com/en/vi/-', proxies={
        #         'http': random_proxy[0],
        #         'https': random_proxy[1]
        #     }).status_code
        # except Exception as e:
        #     print(e)
        #     response = 403
        #     print(random_proxy[0])
        #
        # while response != 200:
        #     indx += 2
        #     random_proxy = proxies[indx % len(proxies)]
        #     try:
        #         response = requests.get('https://glosbe.com/', proxies={
        #             'http': random_proxy[0],
        #             'https': random_proxy[1]
        #         }).status_code
        #     except Exception as e:
        #         print(e)
        #         response = 403
        #         print(random_proxy[0])

        options = {
            'proxy': {
                'http': random_proxy[0],
                'https': random_proxy[1],
                'no_proxy': 'localhost,127.0.0.1:8080'
            },
            'connection_timeout': 10,
            'verify_ssl': False
        }

        # caps = DesiredCapabilities().FIREFOX
        # caps["pageLoadStrategy"] = "eager"

        if not adsblock:
            profile.add_extension('lib/adblock_plus-3.7-an+fx.xpi')

        web_driver = webdriver.Firefox(
            # desired_capabilities=capabilities,
            # capabilities=caps,
            seleniumwire_options=options,
            firefox_profile=profile,
            executable_path=r'lib/geckodriver-v0.26.0-linux64')

        # web_driver.get('https://glosbe.com/')
        # print(random_proxy, web_driver.find_element_by_css_selector('#ipv4 > a').get_attribute('href'))

        # for request in web_driver.requests:
        #     if request.response:
        #         if request.response.status_code == 502:
        #             print('Error 502', random_proxy[0])
        #             web_driver.quit()
        #             self.create_driver(proxies, indx + 2, False)
        return web_driver

    def get_new_keywords(self, web_driver, goto):
        """
        Get all new keyword in current page then save them
        :param web_driver:
        :param goto: url
        :return: save in file and append to list
        """
        # while requests.get(goto).status_code > 499:
        #     print(requests.get(goto).status_code)
        #     web_driver.quit()
        #     web_driver = self.create_driver(random.choices(self.proxies, k=2), login=False, adsblock=False)

        errors = []
        try:
            web_driver.get(goto)
        except TimeoutException:
            webdriver.ActionChains(web_driver).send_keys(Keys.ESCAPE).perform()

        try:
            if web_driver.find_element_by_css_selector('.g-recaptcha'):
                return ['recaptcha']
        except NoSuchElementException:
            pass

        try:
            if web_driver.find_element_by_css_selector('h1').text == 'Error response':
                web_driver.refresh()
                time.sleep(2)
                if web_driver.find_element_by_css_selector('h1').text == 'Error response':
                    return ['502']
        except NoSuchElementException:
            pass

        words = web_driver.find_elements_by_css_selector('#wordListContainer > li')
        for loop in range(5):
            if len(words) > 0:
                break
            web_driver.refresh()
            time.sleep(2)
            # web_driver = self.create_driver(web_driver, login=False, adsblock=False)
            # web_driver.get(goto)
            words = web_driver.find_elements_by_css_selector('#wordListContainer > li')
        # added = 0
        for word in words:
            try:
                key_word = unquote(word.find_element_by_css_selector('a').get_attribute('href'))
                if "%252F%252F" in key_word:
                    continue
                if key_word not in self.existed_url and key_word not in self.crawled_url:
                    # added += 1
                    # print('New word: ' + key_word)
                    self.existed_url.append(key_word)
                    # open(save_to + str(key_word).replace('https://glosbe.com/en/vi/', '') + '.url', 'a+', encoding='utf-8')
            except Exception as e:
                # print('Check keyword in list urls', e)
                errors.append(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") +
                              '    main.py     get_new_keywords()    Loop get new word    ' + goto + ' ' + str(e))
                pass
        # print('Added ' + str(added) + '/' + str(len(words)) + ' words')
        time.sleep(1)
        return errors

    def move_crawled(self, index):
        pop = self.existed_url.pop(index)
        self.crawled_url.append(pop)
        # self.crawled_url = [i.strip() for i in set(self.crawled_url)]
        # self.existed_url = [i.strip() for i in set(self.existed_url)]

        # for i in self.existed_url:
        #     if i in self.crawled_url:
        #         self.existed_url.pop(self.existed_url.index(i))

    def get_content(self, web_driver, goto):
        """
        :param web_driver:
        :param goto: url
        :return: list format ["en \t vi", ...]
                error:  0: Empty data
                        1: Success
                        2: Time out
        """
        errors = []
        content = []
        page = 2
        # web_driver.get(goto)
        try:
            if web_driver.find_element_by_css_selector('.g-recaptcha'):
                return [], 2, ['recaptcha']
        except NoSuchElementException:
            pass

        try:
            # web_driver.set_page_load_timeout(15)
            WebDriverWait(web_driver, 10).until(EC.presence_of_element_located((By.ID, "tm-tab-cont")))
        except TimeoutException:
            errors.append(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") +
                          '    main.py     get_content()    Timeout    ' + goto)
            # web_driver.quit()
            return [], 2, errors

        try:
            if len(web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')) < 1:
                return [], 0, errors
        except Exception as e:
            print('Check amount of elements - pair', e)
            errors.append(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") +
                          '    main.py     get_content()    Find pairs of sentences.1    ' + goto + ' ' + str(e))
            return [], 0, errors

        while page > 0:
            try:
                pairs = web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')
                for pair in pairs:
                    text = pair.find_elements_by_css_selector('div.span6')
                    ori = str(text[0].find_element_by_css_selector('span span').text).strip()
                    trans = str(text[1].find_element_by_css_selector('span span').text).strip()
                    # print(ori, '***=***', trans)
                    content.append(ori + '        ' + trans)
            except NoSuchElementException as e:
                # print(e, goto)
                errors.append(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") +
                              '    main.py     get_content()    Find pairs of sentences-loop page   ' + goto + ' ' + str(
                    e))
                return [line.strip() for line in set(content)], 1, errors
            try:
                web_driver.get(goto + '?page=' + str(page))
            except TimeoutException:
                webdriver.ActionChains(web_driver).send_keys(Keys.ESCAPE).perform()
            try:
                try:
                    if len(web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')) > 0:
                        page += 1
                        if page == 4 and '>>' in web_driver.find_element_by_css_selector(
                                '#translationExamples > div.pagination').text:
                            try:
                                if web_driver.find_element_by_css_selector(
                                        '#topCollapseNavContainer > ul > li:nth-child(3) > a').text == 'My profile':
                                    pass
                                else:
                                    login(web_driver)
                            except NoSuchElementException:
                                login(web_driver)
                    else:
                        return [line.strip() for line in set(content)], 1, errors
                except NoSuchElementException:
                    return [line.strip() for line in set(content)], 1, errors
            except Exception as e:
                # print(goto, e)
                errors.append(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") +
                              '    main.py     get_content()    general try-catch next page   ' + ' ' + goto + ' ' + str(
                    e))
                if len(content) > 0:
                    return [line.strip() for line in set(content)], 1, errors
                else:
                    return [line.strip() for line in set(content)], 2, errors

        return [line.strip() for line in set(content)], 1, errors
