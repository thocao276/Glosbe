import datetime
import glob
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
 Sleep 10s per 5min
 
 FILES EXPLAINS:
    main.py             Class Glosbe
    crawl_glosbe.py     [Current file] - crawl data config
    url_crawled.txt     Crawled all data
    url_empty.txt       Urls haven't data
    url_errors.txt      Occur some errors (Ex: 502 respond)
    url_existed.txt     Contain new urls but haven't crawled yet
"""

from main import Glosbe, read_proxies_file


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
for line in open(LOG_FOLDER + 'url_errors.txt', 'r').readlines():
    if line.strip():
        url_crawled.append(line)
for line in open(LOG_FOLDER + 'url_empty.txt', 'r').readlines():
    if line.strip():
        url_crawled.append(line)

f = open(LOG_FOLDER + 'url_existed.txt', 'w')
for line in url_existed:
    f.write(line + '\n')
f.close()

wr_crawled = open('url_crawled.txt', 'a')

proxies = read_proxies_file('proxies.txt')
rnd_proxy = random.choice(proxies)
counter_file_name = find_file_name(save_dir)

writer = open(create_file_name(save_dir, counter_file_name), 'a')
line_in_file = len(open(create_file_name(save_dir, counter_file_name), 'r').readlines())

for i in url_existed:
    if i in url_crawled:
        url_existed.pop(url_existed.index(i))

rnd_proxy = random.choice(proxies)
print(rnd_proxy)
glosbe = Glosbe(existed=url_existed, crawled=url_crawled, proxies=proxies, save_dir=save_dir)
driver = glosbe.create_driver(rnd_proxy, login=False, adsblock=False)
index = 0

if len(glosbe.existed_url) == 0:
    glosbe.get_new_keywords(driver, goto=glosbe.crawled_url[-1])
    # raise TypeError("There aren't URLs to crawl!")

while index < len(glosbe.existed_url):
    try:
        # Get new keywords on current page
        glosbe.get_new_keywords(driver, goto=glosbe.existed_url[index])

        # Get data on current keywords page
        content, status = glosbe.get_content(driver, goto=glosbe.existed_url[index])
        # Process result
        print(glosbe.existed_url[index].strip(), len(content))
        open(LOG_FOLDER + 'url_visited.log', 'a+').write(datetime.now().strftime("%d/%M/%Y, %H:%M:%S") + '    ' + str(len(content)) + '    ' + glosbe.existed_url[index].strip())
        # Process result)
        # Empty
        if status == 0 or len(content) == 0:  # status == 0
            open(LOG_FOLDER + 'url_empty.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")
            # OK
        elif status == 1:
            open(LOG_FOLDER + 'url_crawled.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")
            # ERROR
        else:
            open(LOG_FOLDER + 'url_errors.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")

        glosbe.crawled_url.append(glosbe.existed_url[index])
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
            time.sleep(10)
            f.close()

        rnd_proxy = random.choice(proxies)
        driver = glosbe.create_driver(rnd_proxy, login=True, adsblock=False)
    except:
        f = open(LOG_FOLDER + 'url_existed.txt', 'w')
        for line in set(glosbe.existed_url):
            f.write(line.strip() + '\n')

        f.close()
        driver.quit()

        glosbe.crawled_url.append(glosbe.existed_url[index])
        wr_errors.write(glosbe.existed_url[index].strip() + "\n")
        glosbe.existed_url.pop(index)

        driver = glosbe.create_driver(rnd_proxy, login=True, adsblock=False)
    finally:
        f = open(LOG_FOLDER + 'url_existed.txt', 'w')
        for line in set(glosbe.existed_url):
            f.write(line.strip() + '\n')
        f.close()

raise TypeError("There aren't URLs to crawl!")
