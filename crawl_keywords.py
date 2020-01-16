import glob
import os
import random

from main import Glosbe


def read_proxies_file(file_name):
    """
    Read file ip proxies
    :param file_name:
    :return: list proxies
    """
    f = open(file_name, 'r').readlines()
    lst_prox = []
    for ii in f:
        lst_prox.append('http://kimnt93:147828@' + ii.strip())
    return lst_prox


DONE_url = []
save_dir = 'URL/'
files = list(filter(os.path.isfile, glob.glob('URL/*.url')))
files.sort(key=lambda x: os.path.getmtime(x))

for i in files:
    DONE_url.append('https://glosbe.com/en/vi/' + i.replace("URL/", '').replace(".url", ''))
# print(DONE_url)

proxies = read_proxies_file('proxies.txt')
rnd_proxy = random.choices(proxies, k=2)

glosbe = Glosbe(DONE_url=DONE_url, proxies=proxies, save_dir=save_dir)
driver = glosbe.create_driver(rnd_proxy, login=False, adsblock=True)
while 1:
    # Get all key words in hompage
    glosbe.recur_get_lst(driver, rnd_proxy)
    driver.quit()
    rnd_proxy = random.choices(proxies, k=2)
    driver = glosbe.create_driver(rnd_proxy, login=False, adsblock=False)
