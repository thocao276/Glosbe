import os, sys
from datetime import datetime
import glob
import time
from pyvirtualdisplay import Display
import threading
from main import Glosbe, read_proxies_file

"""
 Crawl pair of bilingual sentences from Glosbe.com
 Start at keyword "-" OR the first url in url_existed.txt
 Append new keywords on current page to Existed_url
 Crawl all pair of bilingual sentences and write to "output / original_destination / <file_number>.data" 
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


def write_log(filename, content, istimestone):
    if istimestone:
        open(filename, 'a+').write(content.strip() + '\n')
    else:
        open(filename, 'a+').write(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + '    ' + content.strip() + '\n')


def run(arg):
    # if len(arg) != 4:
    #     # raise TypeError('Must be: python3 crawl_glosbe.py [original] [destination] [step proxy] \n Ex: python3 crawl_glosbe.py en vi 1')
    #     arg = ['', 'zh', 'vi', '1']
    original = arg[1]
    destination = arg[2]
    # start_at = 0
    try:
        start_at = int(arg[3])
        if start_at > 10 or start_at < 1:
            raise TypeError('Must be Integer and between 1 and 10')
    except:
        raise TypeError('Must be Integer')

    display = Display(visible=0, size=(800, 600))
    display.start()
    try:
        # Create folder
        LOG_FOLDER = 'log/' + original + '_' + destination + '/'
        save_dir = 'output/' + original + '_' + destination + '/'

        if not os.path.isdir('log/' + original + '_' + destination):
            os.mkdir('log/' + original + '_' + destination)
            open(LOG_FOLDER + 'url_crawled.txt', 'w+')
            open(LOG_FOLDER + 'url_existed.txt', 'w+')
            open(LOG_FOLDER + 'url_errors.txt', 'w+')
            open(LOG_FOLDER + 'url_empty.txt', 'w+')
            open(LOG_FOLDER + 'url_visited.log', 'w+')
        if not os.path.isdir('output/' + original + '_' + destination):
            os.mkdir('output/' + original + '_' + destination)
            open(save_dir + '0.data', 'w+')

        # wr_errors = open(LOG_FOLDER + 'url_errors.txt', 'a+')
        # wr_empty = open(LOG_FOLDER + 'url_empty.txt', 'a+')
        # wr_crawled = open(LOG_FOLDER + 'url_crawled.txt', 'a+')

        url_existed = [line.strip() for line in set(open(LOG_FOLDER + 'url_existed.txt', 'r').readlines()) if
                       line.strip()]
        url_crawled = [line.strip() for line in set(open(LOG_FOLDER + 'url_crawled.txt', 'r').readlines()) if
                       line.strip()]
        for line in set(open(LOG_FOLDER + 'url_errors.txt', 'r').readlines()):
            if line.strip():
                url_crawled.append(line.strip())
        for line in set(open(LOG_FOLDER + 'url_empty.txt', 'r').readlines()):
            if line.strip():
                url_crawled.append(line.strip())

        f = open(LOG_FOLDER + 'url_existed.txt', 'w')
        for line in set(url_existed):
            f.write(line + '\n')
        f.close()

        proxies = read_proxies_file('proxies.txt')
        # rnd_proxy = proxies[start_at]
        counter_file_name = find_file_name(save_dir)

        writer = open(create_file_name(save_dir, counter_file_name), 'a')
        line_in_file = len(open(create_file_name(save_dir, counter_file_name), 'r').readlines())

        for i in url_existed:
            if i in url_crawled:
                url_existed.pop(url_existed.index(i))

        # rnd_proxy = random.choice(proxies)
        # print(rnd_proxy)
        glosbe = Glosbe(existed=url_existed, crawled=url_crawled, proxies=proxies, save_dir=save_dir)
        driver = glosbe.create_driver(proxies, start_at, adsblock=True)
        index = 0
        """
        When there isn't any url in existed_url to crawl, get new keywords from last keyword in crawled_url
        """
        idx = -1
        if len(glosbe.existed_url) == 0 and len(glosbe.crawled_url) == 0:
            glosbe.existed_url.append('https://glosbe.com/' + original + '/' + destination + '/-')

        while len(glosbe.existed_url) == 0 and len(glosbe.crawled_url) > 0:
            error = glosbe.get_new_keywords(driver, goto=glosbe.crawled_url[idx])
            if len(error) > 0:
                if error[0] == 'recaptcha':
                    start_at += 2
                    driver.quit()
                    # os.system('killall firefox')
                    write_log(LOG_FOLDER + 'errors.log', 'crawl_glosbe.py    run()    RECAPTCHA get new words    ' +
                              proxies[start_at % len(proxies)][0], False)
                    driver = glosbe.create_driver(proxies, start_at % len(proxies), adsblock=True)
                elif error[0] == '502':
                    write_log(LOG_FOLDER + 'errors.log',
                              'crawl_glosbe.py    run()    502    ' +
                              proxies[start_at % len(proxies)][0], False)
                    break
                else:
                    for i in error:
                        write_log(LOG_FOLDER + 'errors.log', i, True)
            idx -= 1
        # raise TypeError("There aren't URLs to crawl!")
        del idx
        print("Start ", original, destination)
        if "%252F%252F" in glosbe.existed_url[index]:
            open(LOG_FOLDER + 'url_errors.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")
            # print(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + '    ' + str(len(content)) + '\t' + glosbe.existed_url[index][18:])
            # print('Popped1 ', url_existed[index])
            glosbe.move_crawled(index)

        while index < len(glosbe.existed_url):
            for j in range(15):
                try:
                    # driver.get('https://whatismyipaddress.com/')

                    # Get new keywords on current page
                    error = glosbe.get_new_keywords(driver, goto=glosbe.existed_url[index])
                    if len(error) > 0:
                        if error[0] == 'recaptcha':
                            write_log(LOG_FOLDER + 'errors.log',
                                      'crawl_glosbe.py    run()    RECAPTCHA get new words    ' +
                                      proxies[start_at % len(proxies)][0], False)
                            break
                        elif error[0] == '502':
                            write_log(LOG_FOLDER + 'errors.log',
                                      'crawl_glosbe.py    run()    502    ' +
                                      proxies[start_at % len(proxies)][0], False)
                            break
                        else:
                            for i in error:
                                write_log(LOG_FOLDER + 'errors.log', i, True)

                    # Get data on current keywords page
                    content, status, error = glosbe.get_content(driver, goto=glosbe.existed_url[index])
                    if len(error) > 0:
                        if error[0] == 'recaptcha':
                            write_log(LOG_FOLDER + 'errors.log',
                                      'crawl_glosbe.py    run()    RECAPTCHA get content    ' +
                                      proxies[start_at % len(proxies)][0], False)
                            break
                        for i in error:
                            write_log(LOG_FOLDER + 'errors.log', i, True)

                    # Process result
                    # print(glosbe.existed_url[index].strip()[25:], len(content))
                    write_log(LOG_FOLDER + 'url_visited.log',
                              str(len(content)) + '    ' + glosbe.existed_url[index].strip() + '\n', False)
                    # Process result)
                    # Empty
                    if status == 0 or len(content) == 0:  # status == 0
                        open(LOG_FOLDER + 'url_empty.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")
                    # OK
                    elif len(content) > 1:
                        open(LOG_FOLDER + 'url_crawled.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")
                    # ERROR
                    else:
                        open(LOG_FOLDER + 'url_errors.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")

                    # print(datetime.now().strftime("%d/%m/%Y, %H:%M:%S") + '    ' + str(len(content)) + '\t' + glosbe.existed_url[index][18:])
                    # print('Popped2 ', url_existed[index])
                    glosbe.move_crawled(index)

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

                # if round(time.time() % 300) < 5:
                # 	f = open(LOG_FOLDER + 'url_existed.txt', 'w')
                # 	for line in set(glosbe.existed_url):
                # 		f.write(line.strip() + "\n")
                # 	time.sleep(60)
                # 	f.close()
                except Exception as e1:
                    write_log(LOG_FOLDER + 'errors.log',
                              'crawl_glosbe.py    run()    main loop    ' + str(e1) + ' - Proxy: ' +
                              proxies[start_at % len(proxies)][0], False)
                    # print(e)
                    # print(proxies[idx % len(proxies)], glosbe.existed_url[index])

                    # print('Popped3 ', url_existed[index])
                    glosbe.move_crawled(index)

                    f = open(LOG_FOLDER + 'url_existed.txt', 'w')
                    for line in set(glosbe.existed_url):
                        f.write(line.strip() + '\n')

                    f.close()
                    # print('Except')
                    driver.quit()
                    # os.system('killall firefox')
                    driver = glosbe.create_driver(proxies, start_at % len(proxies), adsblock=True)
                    open(LOG_FOLDER + 'url_errors.txt', 'a+').write(glosbe.existed_url[index].strip() + "\n")

                finally:
                    f = open(LOG_FOLDER + 'url_existed.txt', 'w')
                    for line in set(glosbe.existed_url):
                        f.write(line.strip() + '\n')
                    f.close()
            time.sleep(30)

            start_at += 2
            rnd_proxy = proxies[start_at % len(proxies)]
            # print('out loop')
            driver.quit()
            # os.system('killall firefox')
            time.sleep(90)
            driver = glosbe.create_driver(proxies, start_at % len(proxies), adsblock=True)
    except KeyboardInterrupt:
        os.system('killall firefox')
        # try:
        #     display.stop()
        # except:
        #     pass
    except SystemExit:
        os.system('killall firefox')
        try:
            display.stop()
        except:
            pass
    # display.stop()
    # raise TypeError("There aren't URLs to crawl!")

# run(["",'vi', 'en', 1])


argument = sys.argv
if len(argument) != 3:
    raise TypeError('Must be: python3 crawl_glosbe.py [language 1] [language 2] \n Ex: python3 crawl_glosbe.py en vi. \nTo crawl English to Vietnamese and Vietnamese to English')
    # argument = ['', 'zh', 'vi', '1']
original_th = argument[1]
destination_th = argument[2]

vi_en = threading.Thread(target=run, args=[['', original_th, destination_th, 1]])
en_vi = threading.Thread(target=run, args=[['', destination_th, original_th, 2]])
try:
    en_vi.start()
    vi_en.start()
    en_vi.join()
    vi_en.join()
except Exception as e:
    print(e)

# run(argument)
