import os, sys
from datetime import datetime
import glob
import time
from pyvirtualdisplay import Display

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
    try:
        counter = max(name)
    except:
        return 0

    if len(open(path + str(counter) + '.data', 'r').readlines()) >= 500000:
        counter += 1

    return counter


def create_file_name(path, num):
    return path + str(num) + '.data'


arg = sys.argv
if len(arg) != 4:
    raise TypeError('Must be: python3 crawl_glosbe.py [from] [translate to] [skip proxy]')

ORI = arg[1]
TRANS = arg[2]
try:
    skip = int(arg[3])
    if skip > 10:
        raise TypeError('Must be Integer and less than 10')
except:
    raise TypeError('Must be Integer')

display = Display(visible=0, size=(800, 600))
display.start()

# Create folder
LOG_FOLDER = 'log/' + ORI + '_' + TRANS + '/'
save_dir = 'output/' + ORI + '_' + TRANS + '/'

if not os.path.isdir('log/' + ORI + '_' + TRANS):
    os.mkdir('log/' + ORI + '_' + TRANS)
    open(LOG_FOLDER + 'url_crawled.txt', 'w+')
    open(LOG_FOLDER + 'url_existed.txt', 'w+')
    open(LOG_FOLDER + 'url_errors.txt', 'w+')
    open(LOG_FOLDER + 'url_empty.txt', 'w+')
    open(LOG_FOLDER + 'url_visited.log', 'w+')
if not os.path.isdir('output/' + ORI + '_' + TRANS):
    os.mkdir('output/' + ORI + '_' + TRANS)
    open(save_dir + '0.data', 'w+')

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
for line in set(url_existed):
    f.write(line + '\n')
f.close()

wr_crawled = open(LOG_FOLDER + 'url_crawled.txt', 'a')

proxies = read_proxies_file('proxies.txt')
rnd_proxy = proxies[skip]
counter_file_name = find_file_name(save_dir)

writer = open(create_file_name(save_dir, counter_file_name), 'a')
line_in_file = len(open(create_file_name(save_dir, counter_file_name), 'r').readlines())

for i in url_existed:
    if i in url_crawled:
        url_existed.pop(url_existed.index(i))

# rnd_proxy = random.choice(proxies)
# print(rnd_proxy)
glosbe = Glosbe(existed=url_existed, crawled=url_crawled, proxies=proxies, save_dir=save_dir)
driver = glosbe.create_driver(proxies[0], adsblock=True)
index = 0
"""
When there isn't any url in existed_url to crawl, get new keywords from last keyword in crawled_url
"""
idx = -1
if len(glosbe.existed_url) == 0 and len(glosbe.crawled_url) == 0:
    glosbe.existed_url.append('https://glosbe.com/' + ORI + '/' + TRANS + '/-')

while len(glosbe.existed_url) == 0 and len(glosbe.crawled_url) > 0:
    glosbe.get_new_keywords(driver, goto=glosbe.crawled_url[idx])
    idx -= 1
    # raise TypeError("There aren't URLs to crawl!")
del idx

if "%2F%2F" in glosbe.existed_url[index] or "%252F%252F" in glosbe.existed_url[index]:
    open(LOG_FOLDER + 'url_errors.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")
    # print(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + '    ' + str(len(content)) + '\t' + glosbe.existed_url[index][18:])
    glosbe.crawled_url.append(glosbe.existed_url[index])
    glosbe.existed_url.pop(index)

while index < len(glosbe.existed_url):
    for i in range(10):
        try:
            # driver.get('https://whatismyipaddress.com/')

            # Get new keywords on current page
            glosbe.get_new_keywords(driver, goto=glosbe.existed_url[index])

            # Get data on current keywords page
            content, status = glosbe.get_content(driver, goto=glosbe.existed_url[index])

            # Process result
            # print(glosbe.existed_url[index].strip()[25:], len(content))
            open(LOG_FOLDER + 'url_visited.log', 'a+').write(
                datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + '    ' + str(len(content)) + '    ' +
                glosbe.existed_url[
                    index].strip() + '\n')
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

            print(
                datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + '    ' + str(len(content)) + '\t' + glosbe.existed_url[
                                                                                                        index][18:])
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
            # driver.quit()
            # index += 1

            if round(time.time() % 300) < 5:
                f = open(LOG_FOLDER + 'url_existed.txt', 'w')
                for line in set(glosbe.existed_url):
                    f.write(line.strip() + "\n")
                time.sleep(10)
                f.close()
        except Exception as e:
            print(e)
            # print(proxies[idx % len(proxies)], glosbe.existed_url[index])
            f = open(LOG_FOLDER + 'url_existed.txt', 'w')
            for line in set(glosbe.existed_url):
                f.write(line.strip() + '\n')

            f.close()
            # print('Except')
            driver.quit()
            driver = glosbe.create_driver(rnd_proxy, adsblock=True)

            glosbe.crawled_url.append(glosbe.existed_url[index])
            wr_errors.write(glosbe.existed_url[index].strip() + "\n")
            glosbe.existed_url.pop(index)
        finally:
            f = open(LOG_FOLDER + 'url_existed.txt', 'w')
            for line in set(glosbe.existed_url):
                f.write(line.strip() + '\n')
            f.close()

    skip += 4
    rnd_proxy = proxies[skip % len(proxies)]
    # print('out loop')
    driver.quit()
    driver = glosbe.create_driver(rnd_proxy, adsblock=False)


display.stop()
raise TypeError("There aren't URLs to crawl!")
