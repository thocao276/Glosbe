import glob
import os
import random
import time

"""
 Crawl pair of bilingual sentences en <=> vi from Glosbe.com
 Start at keyword "-" OR urls in url_existed.txt
 Append new keywords on current page to Existed_url
 Crawl all pair of bilingual sentences and write to "output / [en_vi/vi_en] / <file_number>.data" 
    * File_number: int[0, 1,..]
    * There are maximum 500.000 lines per file
    * Format: [en]<'        '>[vi] (8 spaces)
 Loop with new url in Existed_url
 Sleep 2 sec per 5 min
 
 FILES EXPLAINS:
    main.py             Class Glosbe
    crawl_glosbe.py     [Current file] - crawl data config
    url_crawled.txt     Crawled all data
    url_empty.txt       Urls haven't data
    url_errors.txt      Occur some errors (Ex: 502 respond)
    url_existed.txt     Contain new urls but haven't crawled yet
"""

from main import Glosbe


def read_proxies_file(file_name):
    """
    Read file ip proxies
    :param file_name:
    :return: list proxies
    """

    lst_prox = []
    for ii in open(file_name, 'r').readlines():
        lst_prox.append('https://kimnt93:147828@' + ii.strip())
    return lst_prox


def find_file_name(path):
    """
    find last file to write
    :return: INT - file name can write in it
    """
    name = []
    for file in glob.glob(path + '*.data'):
        name.append(int(file.split(path)[-1].replace('.data', '')))
    counter = max(name)

    if len(open(path + str(counter) + '.data', 'r').readlines()) >= 500000:
        counter += 1

    return counter


def create_file_name(path, num):
    return path + str(num) + '.data'


LOG_FOLDER = 'log_en_vi/'
save_dir = 'output/en_vi/'

wr_errors = open(LOG_FOLDER + 'url_errors.txt', 'w')
wr_empty = open(LOG_FOLDER + 'url_empty.txt', 'w')

url_existed = [line for line in open(LOG_FOLDER + 'url_existed.txt', 'r').readlines() if line.strip()]
url_crawled = [line for line in open(LOG_FOLDER + 'url_crawled.txt', 'r').readlines() if line.strip()]
url_errors = [line for line in open(LOG_FOLDER + 'url_errors.txt', 'r').readlines() if line.strip()]
url_empty = [line for line in open(LOG_FOLDER + 'url_empty.txt', 'r').readlines() if line.strip()]

f = open(LOG_FOLDER + 'url_existed.txt', 'w')
for line in url_existed:
    f.write(line + '\n')
f.close()
# wr_crawled = open('url_crawled.txt', 'a')
if len(url_existed) == 0:
    raise TypeError("There aren't URLs to crawl!")

proxies = read_proxies_file('proxies.txt')
rnd_proxy = random.choices(proxies, k=2)
counter_file_name = find_file_name(save_dir)

writer = open(create_file_name(save_dir, counter_file_name), 'a')
line_in_file = len(open(create_file_name(save_dir, counter_file_name), 'r').readlines())

for i in url_existed:
    if i in url_crawled or i in url_empty or i in url_errors:
        url_existed.pop(url_existed.index(i))

# for i in url_existed:
#     DONE_url.append('https://glosbe.com/en/vi/' + i.replace("URL/", '').replace(".url", ''))
# print(DONE_url)

glosbe = Glosbe(existed=url_existed, crawled=url_crawled, empty=url_empty, error=url_errors, proxies=proxies,
                save_dir=save_dir)
driver = glosbe.create_driver(rnd_proxy, login=True, adsblock=True)
index = 0

while index < len(glosbe.existed_url):
    try:
        # Get new keywords on current page
        glosbe.get_new_keywords(driver, goto=glosbe.existed_url[index])

        # Get data on current keywords page
        content, status = glosbe.get_content(driver, goto=glosbe.existed_url[index])
        # Process result
            # ERROR
        if status == 2:
            glosbe.error_url.append(glosbe.existed_url[index])
            wr_errors.write(glosbe.existed_url[index].strip() + "\n")
            # OK
        elif status == 1:
            glosbe.crawled_url.append(glosbe.existed_url[index])
            open(LOG_FOLDER + 'url_crawled.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")
            # Empty
        else:  # status == 0
            glosbe.empty_url.append(glosbe.existed_url[index])
            wr_empty.write(glosbe.existed_url[index].strip() + "\n")
        glosbe.existed_url.pop(index)

        # Write to file
        for line in content:
            if line_in_file <= 500000:
                if line.strip() != '':
                    writer.write(line.strip() + '\n')
                    line_in_file += 1
            else:
                line_in_file = 0
                writer.close()
                counter_file_name += 1
                writer = open(create_file_name(save_dir, counter_file_name), 'a')
                writer.write(line.strip() + '\n')
        driver.quit()
        # index += 1

        if round(time.time() % 300) < 5:
            f = open(LOG_FOLDER + 'url_existed.txt', 'w')
            for line in set(glosbe.existed_url):
                f.write(line.strip() + "\n")
            time.sleep(2)

        rnd_proxy = random.choices(proxies, k=2)
        driver = glosbe.create_driver(rnd_proxy, login=True, adsblock=True)
    except:
        f = open(LOG_FOLDER + 'url_existed.txt', 'w')
        for line in set(glosbe.existed_url):
            f.write(line.strip() + '\n')

        driver.quit()
        driver = glosbe.create_driver(rnd_proxy, login=True, adsblock=True)

        glosbe.error_url.append(glosbe.existed_url[index])
        wr_errors.write(glosbe.existed_url[index].strip() + "\n")
        glosbe.existed_url.pop(index)
raise TypeError("There aren't URLs to crawl!")
