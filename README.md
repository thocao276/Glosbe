# Glosbe crawler
## To do: Crawl pair of example in Glosbe

## Step 1: Visit Glosbe.com then crawl all unique keywords in the left panel
    Keywords are saved in log_*/url_existed for keywords haven't crawled data or log_*/url_crawled for crawled ones.
    log_*/error_url contains keywords which occur errors when crawling
## Step 2: Go to each keyword in log_*/url_existed to crawl pair of example
    When crawled, keyword have been moved to log_*/url_crawled
    Save to: output/[en_vi or vi_en]/[index].data; index = range(from=0, to=.., step=1)
    There are 500000 lines per file.
    Format: [en]<'        '>[vi] (8 spaces)
## Loop Step 1 & 2
Sleep 10s per 5min
