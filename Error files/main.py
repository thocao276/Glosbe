import datetime
import glob, shutil, os
import json
import random
import re
import time
import zipfile
from builtins import print
from urllib.parse import urlparse

import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from seleniumwire import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.options import Options


def read_proxies_file(file_name):
    """
    Read file ip proxies
    :param file_name:
    :return: list proxies
    """

    lst_prox = []
    for ii in open(file_name, 'r').readlines():
        # lst_prox.append('https://kimnt93:147828@' + ii.strip())
        a = {
            'proxy_host': ii.split(":")[0],
            'proxy_port': ii.split(":")[-1].strip(),
            'proxy_user': 'kimnt93',
            'proxy_pass': '147828'
        }
        lst_prox.append(a)
    return lst_prox

class Glosbe:
    def __init__(self, existed, crawled, proxies, save_dir):
        self.existed_url = existed
        self.crawled_url = crawled
        # self.error_url = error
        # self.empty_url = empty
        self.proxies = proxies
        self.save_dir = save_dir

    def getPlugin(self, proxy_host, proxy_port, proxy_user, proxy_pass):
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy_host, proxy_port, proxy_user, proxy_pass)
        pluginfile = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        return pluginfile

    def create_driver(self, random_proxy, login):
        """
        Create config firefox browser
        :param random_proxy: list includes 2 ip proxies
        :param login: Need to login? If True, config email, password, url login under
        :return:
        """

        # proxyArgsList = read_proxies_file('proxies.txt')
        # proxy = random.choice(proxyArgsList)
        chrome_options = webdriver.ChromeOptions()

        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--proxy-auto-detect")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument('--disable-gpu')

        chrome_options.add_argument('--ignore-certificate-errors')
        # chrome_options.add_extension('lib/extension_4_1_0_0.crx')
        chrome_options.add_extension(self.getPlugin(proxy_host=random_proxy['proxy_host'], proxy_port=random_proxy['proxy_port'], proxy_user='kimnt93',
                      proxy_pass='147828'))


        web_driver = webdriver.Chrome(executable_path="lib/chromedriver",
                                      options=chrome_options)

        if login == True:
            account = [i.split("\t") for i in open('account.txt', 'r').readlines()]
            # LOGIN by temp-mail
            web_driver.get('https://auth2.glosbe.com/login')
            while 1:
                acc = random.choice(account)
                try:
                    web_driver.find_element_by_css_selector('#username').send_keys(str(acc[0]))
                    web_driver.find_element_by_css_selector('#password').send_keys(str(acc[1]))
                    web_driver.find_element_by_name('submit').click()
                    break
                except NoSuchElementException as a:
                    web_driver.get('https://auth2.glosbe.com/login')

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
                if key_word not in self.existed_url and key_word not in self.crawled_url:
                    added += 1
                    self.existed_url.append(key_word)
                    # open(save_to + str(key_word).replace('https://glosbe.com/en/vi/', '') + '.url', 'a+', encoding='utf-8')
            except Exception as e:
                print('Check keyword in list urls', e)
                pass
        # print('Added ' + str(added) + '/' + str(len(words)) + ' words')
        time.sleep(0.1)

    def recur_get_lst(self, random_proxy):
        """
        Recursive get new keywords in current page then append list need to crawl
        :param web_driver:
        :param random_proxy: list includes 2 ip proxies
        :return:
        """
        idx = len(self.existed_url) - random.choice(range(1, 9))
        web_driver = self.create_driver(random_proxy=random_proxy, login=False)
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
                error:  0: Empty data
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
            print('Check amount of elements - pair', e)
            return [], 0

        while page > 0:
            try:
                pairs = web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')
                for pair in pairs:
                    text = pair.find_elements_by_css_selector('div.span6')
                    en = str(text[0].text).strip()
                    vi = str(text[1].text).strip()
                    content.append(en + '        ' + vi)
            except NoSuchElementException as e:
                print(e, goto)
                break

            web_driver.get(goto + '?page=' + str(page))
            try:
                try:
                    if len(web_driver.find_elements_by_css_selector('#tm-tab-cont > #tmTable > .tableRow')) > 0:
                        page += 1
                    else:
                        return [line.strip() for line in set(content)], 1
                except NoSuchElementException:
                    return [line.strip() for line in set(content)], 1
            except Exception as e:
                print(goto, e)
                return [line.strip() for line in set(content)], 2

        return [line.strip() for line in set(content)], 1
