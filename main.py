import datetime
import glob, shutil, os
import json
import random
import re
import time
from builtins import print
from urllib.parse import urlparse

import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from seleniumwire import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

class Glosbe:
    def __init__(self, existed, crawled, error, empty, proxies, save_dir):
        self.existed_url = existed
        self.crawled_url = crawled
        self.error_url = error
        self.empty_url = empty
        self.proxies = proxies
        self.save_dir = save_dir

    def create_driver(self, random_proxy, login, adsblock):
        """
        Create config firefox browser
        :param adsblock: Just install first time
        :param random_proxy: list includes 2 ip proxies
        :param login: Need to login? If True, config email, password, url login under
        :return:
        """
        profile = webdriver.FirefoxProfile()
        # profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("http.response.timeout", 13)
        profile.set_preference("dom.max_script_run_time", 13)
        # profile.set_preference("browser.private.browsing.autostart", False)
        #  Off images
        # profile.set_preference("permissions.default.image", 2)
        # profile.set_preference("browser.download.manager.showWhenStarting", False)
        # profile.set_preference("pdfjs.disabled", True)
        # profile.set_preference("browser.download.dir", '/home/thocao/Documents/Data_TrichYeu/DongThap/')
        # profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")

        # Unable open pdf files in browser
        # profile.set_preference("plugin.scan.Acrobat", "99.0")
        # profile.set_preference("plugin.scan.plid.all", False)

        if adsblock == True:
            profile.add_extension('lib/adblock_plus-3.7-an+fx.xpi')
        # options = {
        #     'proxy': {
        #         'https': random_proxy[0],
        #         'http': random_proxy[1]
        #     }
        # }
        print(random_proxy)
        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = random_proxy[0]
        proxy.ssl_proxy = random_proxy[1]

        capabilities = webdriver.DesiredCapabilities.FIREFOX
        proxy.add_to_capabilities(capabilities)

        web_driver = webdriver.Firefox(
            desired_capabilities=capabilities,
            # seleniumwire_options=options,
            firefox_profile=profile,
            executable_path=r'lib/geckodriver-v0.26.0-linux64')

        account = [i.split("\t") for i in open('account.txt', 'r').readlines()]

        if login == True:
            # LOGIN by temp-mail
            web_driver.get('https://auth2.glosbe.com/login?returnUrl=http%3A%2F%2Fglosbe.com%2FloginRedirectInternal')
            while 1:
                acc = random.choice(account)
                try:
                    web_driver.find_element_by_css_selector('#username').send_keys(str(acc[0]))
                    web_driver.find_element_by_css_selector('#password').send_keys(str(acc[1]))
                    web_driver.find_element_by_name('submit').click()
                    break
                except NoSuchElementException as a:
                    web_driver.get('https://auth2.glosbe.com/login?returnUrl=http%3A%2F%2Fglosbe.com%2FloginRedirectInternal')

        return web_driver

    def get_new_keywords(self, web_driver, goto):
        """
        Get all new keyword in current page then save them
        :param web_driver:
        :param goto: url
        :param save_to: directory
        :return: save in file and append to list
        """
        # while requests.get(goto).status_code > 499:
        #     print(requests.get(goto).status_code)
        #     web_driver.quit()
        #     web_driver = self.create_driver(random.choices(self.proxies, k=2), login=False, adsblock=False)

        web_driver.get(goto)
        words = web_driver.find_elements_by_css_selector('#wordListContainer > li')
        while len(words) == 0:
            web_driver.refresh()
            # web_driver = self.create_driver(web_driver, login=False, adsblock=False)
            # web_driver.get(goto)
            words = web_driver.find_elements_by_css_selector('#wordListContainer > li')
        added = 0
        for word in words:
            try:
                key_word = word.find_element_by_css_selector('a').get_attribute('href')
                if key_word not in self.existed_url and key_word not in self.crawled_url and key_word not in self.empty_url and key_word not in self.error_url:
                    added += 1
                    self.existed_url.append(key_word)
                    # open(save_to + str(key_word).replace('https://glosbe.com/en/vi/', '') + '.url', 'a+', encoding='utf-8')
            except Exception as e:
                print(e)
                pass
        print('Added ' + str(added) + '/' + str(len(words)) + ' words')
        time.sleep(0.1)

    def recur_get_lst(self, random_proxy):
        """
        Recursive get new keywords in current page then append list need to crawl
        :param web_driver:
        :param random_proxy: list includes 2 ip proxies
        :return:
        """
        idx = len(self.existed_url) - random.choice(range(1, 9))
        web_driver = self.create_driver(random_proxy=random_proxy, login=False, adsblock=False)
        try:
            try:
                if web_driver.find_element_by_css_selector('.g-recaptcha').get_attribute('data-sitekey'):
                    f = open('URL_crawled.txt', 'w', encoding='utf-8')
                    for ix in self.existed_url:
                        f.write(ix + "\n")
                    f.close()
                    web_driver.quit()
                    print('IP is blocked.')
                    open('proxy_err.txt', 'a+').write(str(datetime.datetime.now()) + '\t' + ','.join(random_proxy) + '\n')
                    return
            except:
                pass
            loop = 0
            while round(time.time() % 60) > 4 or loop < 5:
                while idx >= len(self.existed_url):
                    idx -= random.choice(range(1, 4))
                if self.get_new_keywords(web_driver, goto=self.existed_url[idx]) == 0:
                    idx -= 1
                    loop += 1
                else:
                    idx += 10
                #  Write proxies when can't get elements 4 times
                if loop > 4:
                    open('proxy_err.txt', 'a+').write(str(datetime.datetime.now()) + '\t' + ','.join(random_proxy) + '\n')

        except:
            f = open('URL_crawled.txt', 'w', encoding='utf-8')
            for ix in self.existed_url:
                f.write(ix + "\n")
            f.close()

    def process_content(self, content):
        """
        Clean content before write file
        :param content:
        :return:
        """
        content = re.sub('\[\d+\]', '', content)
        content = re.sub('\n+', '\n', content)
        content = re.sub(r'Bài liên quan:.*\n', '', content)
        return content.strip()

    def get_content(self, web_driver, goto):
        """

        :param web_driver:
        :param goto: url
        :return: list format ["en \t vi", ...]
                error:  0: Empty comments
                        1: Success
                        2: Time out
        """
        content = []
        page = 2
        # web_driver.get(goto)
        try:
            web_driver.set_page_load_timeout(6)
        except TimeoutException:
            web_driver.quit()
            return [], 2

        try:
            if len(web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')) > 0:
                pass
            else:
                return [], 0
        except Exception as e:
            print(e)
            return [], 0

        while page > 0:
            try:
                pairs = web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')
                for pair in pairs:
                    text = pair.find_elements_by_css_selector('div.span6')
                    en = str(text[0].text).strip()
                    vi = str(text[1].text).strip()
                    content.append(en + '\t' + vi)
            except Exception as e:
                print(e, goto)

            web_driver.get(goto + '?page=' + str(page))
            for i in range(5):
                try:
                    web_driver.set_page_load_timeout(6)
                except TimeoutException:
                    web_driver.refresh()
                    time.sleep(3)

            try:
                if len(web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')) > 0:
                    page += 1
                else:
                    return [line.strip() for line in set(content)], 1
            except Exception as e:
                print(e)
                return [line.strip() for line in set(content)], 2

        return [line.strip() for line in set(content)], 1

# DONE_url = []
# save_dir = 'URL/'
#
# files = list(filter(os.path.isfile, glob.glob('URL/*.url')))
# files.sort(key=lambda x: os.path.getmtime(x))
# for i in files:
#     DONE_url.append('https://glosbe.com/en/vi/' + i.replace("URL/", '').replace(".url", ''))
# print(DONE_url)
#
# proxies = read_proxies_file('proxies.txt')
# rnd_proxy = random.choices(proxies, k=2)
#
# while 1:
#     driver = create_driver(rnd_proxy, login=False, adsblock=True)
#     # Get all key words in hompage
#     recur_get_lst(driver, rnd_proxy)
#     driver.quit()
#     rnd_proxy = random.choices(proxies, k=2)

# Get Example with keyword
# need_to_crawl = []
# done = [('https://glosbe.com/en/vi/' + i.replace("DONE/", '').replace(".url", '')) for i in glob.glob('DONE/*.url')]
# for i in DONE_url:
#     if i not in done:
#         need_to_crawl.append(i)
# need_to_crawl.sort()
# for i in need_to_crawl:
#     .get_content(i, save_dir + i.replace('https://glosbe.com/en/vi/', '') + '.url')

# Delete 25 first rows
# for i in glob.glob('DONE/*.url'):
#     with open(i, 'r') as data_file:
#         data = json.load(data_file)
#
#     for j in range(25):
#         data.pop(str(j), None)
#
#     with open(i, 'w') as data_file:
#         data = json.dump(data, data_file)
