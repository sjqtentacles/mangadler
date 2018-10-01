from pyfiglet import Figlet
from lxml import html
import requests
import time
from clint.textui import puts, indent, colored, prompt, progress
import re
import os

def get_img_from_imgholder(imgh):
    img = imgh.getchildren()[0]
    return img.attrib['src']

def get_imgholder_from_page(page):
    tree = html.fromstring(page.content)
    imgholder = tree.xpath('//*[@id="imgholder"]/a')[0]
    return imgholder

def get_data_from_page(page):
    time.sleep(0.15)
    try:
        imgholder = get_imgholder_from_page(page)
        img = get_img_from_imgholder(imgholder)
        page_num = page.url.split("/")[-1]
        img_extension = img.split('/')[-1].split(".")[-1]
        return {
            'img_url': img,
            'page_url': page.url,
            'nice_img_fname': '{}.{}'.format(page_num, img_extension)
        }
    except:
        return None

def get_page_from_url(link):
    return requests.get(link)

def get_chapters_from_contents(contents_page):
    tree = html.fromstring(contents_page.content)
    links = map(lambda i: i.getnext().attrib['href'], tree.xpath('//*[@class="chico_manga"]'))
    chapnums = map(lambda x: int(x.split('/')[-1]), links)
    return sorted(chapnums)

def gen_manga_chap_page_link(manga, chap, page = None):
    base = "https://www.mangareader.net"
    if page:
        return "{}/{}/{}/{}".format(base, manga, chap, page)
    return "{}/{}/{}".format(base, manga, chap)

def get_manga_whole_chapter_links(manga, chap):
    init_link = gen_manga_chap_page_link(manga, chap)
    content = requests.get(init_link).content
    tree = html.fromstring(content)
    chap_page_val_elems = tree.xpath('//*[@id="pageMenu"]')[0].getchildren()
    chap_pages = map(lambda x: int(x.text), chap_page_val_elems)
    return map(lambda x: gen_manga_chap_page_link(manga, chap, x), chap_pages)

def parse_chaps_user_input(manga_name, chaps_in):
    if chaps_in == 'all':
        return get_chapters_from_contents(get_page_from_url("https://www.mangareader.net/naruto"))
    elif re.match('^(\d+)-(\d+)$', chaps_in):
        start, end = map(int, re.match('^(\d+)-(\d+)$', chaps_in).groups())
        return list(range(min(start, end), max(start, end)+1))
    elif re.match('^(\d+)$', chaps_in):
        return [int(re.match('^(\d+)$', chaps_in).group())]
    else:
        return []

def greeting_text_and_guide():
    f = Figlet(font='slant')
    puts(colored.green(f.renderText('MangaDLer')))
    puts(colored.green("The mangareader.net Downloader\n"))

    with indent(2, quote=' | '):
        puts(colored.cyan("How to Use MangaDLer\n"))
        puts(colored.cyan("""
    Go to a mangareader.net link, for example: \n
    https://www.mangareader.net/naruto/11

    You see the url says 'naruto' for the manga name?
    Copy/paste the manga name 'naruto' into the manga prompt. (case insensitive)\n
        """))
    puts(colored.magenta("Example:"))
    puts(colored.green("Manga Name?: naruto\n"))
    with indent(2, quote=' | '):
        puts(colored.cyan("""
    Then when asked what chapters, you can respond one of three ways:
    *) Give a number like 374 for the 374th chapter of naruto.\n
    *) Give a range like 374-390 for the chapters 374, 375, .. 390\n
    *) Write 'all' to download all chapters.\n
        """))
    
    puts(colored.magenta("Examples:"))
    puts(colored.green("Which chapters?: 2"))
    puts(colored.green("Which chapters?: 2-10"))
    puts(colored.green("Which chapters?: all\n"))

def download_img_to_file(path, img_link):
    r = requests.get(img_link, stream=True)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in r:
                f.write(chunk)

if __name__=="__main__":
    greeting_text_and_guide()

    manga_name = prompt.query("Manga Name?:").lower().strip()
    chaps = prompt.query("Which chapters?").lower().strip()

    parsed_chaps = parse_chaps_user_input(manga_name, chaps)

    if not os.path.exists(manga_name):
        os.makedirs(manga_name)

    puts(colored.green("OKAY!\nDownload Starting Now!\n\n"))
    
    for c in parsed_chaps:
        puts(colored.green("Finding chapter {} image links...".format(c)))

        page_links = list(get_manga_whole_chapter_links(manga_name, c))
        page_contents = map(get_page_from_url, page_links)
        page_data = list(filter(None.__ne__, map(get_data_from_page, page_contents)))

        if not os.path.exists('{}/chap_{}'.format(manga_name, c)):
            os.makedirs('{}/chap_{}'.format(manga_name, c))
        
        for page_info in progress.mill(page_data, label="Downloading chapter {}... ".format(c)):
            img_url = page_info['img_url']
            save_fname = '{}/chap_{}/{}'.format(manga_name, c, page_info['nice_img_fname'])
            download_img_to_file(save_fname, img_url)
            time.sleep(0.25)
    puts(colored.cyan("\n\nFinished All Downloads, thanks for using MangaDLer!"))