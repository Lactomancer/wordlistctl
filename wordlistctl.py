#!/usr/bin/env python3
# -*- coding: latin-1 -*- ######################################################
#                                                                              #
# wordlistctl - Fetch, install and search wordlist archives from websites and  #
# torrent peers.                                                               #
#                                                                              #
# DESCRIPTION                                                                  #
# Script to fetch, install, update and search wordlist archives from websites  #
# offering wordlists with more than 1800 wordlists available.                  #
#                                                                              #
# AUTHORS                                                                      #
# sepehrdad.dev@gmail.com                                                      #
#                                                                              #
################################################################################

__author__ = 'Sepehrdad Sh'
__organization__ = 'blackarch.org'
__license__ = 'GPLv3'
__version__ = '0.6.9'
__project__ = 'wordlistctl'

__wordlist_path__ = '/usr/share/wordlists'
__urls_file_name__ = ''
__categories_file_name__ = ''
__category__ = ''
__urls__ = {}
__categories__ = {}
__decompress__ = False
__remove__ = False
__prefer_http__ = False

__trds__ = []
__max_trds__ = 10
__session__ = None
__useragent__ = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:63.0) Gecko/20180101 Firefox/63.0'


def err(string, ex=''):
    if ex == '':
        print(colored("[-]", 'red', attrs=['bold']) + " {0}".format(string), file=sys.stderr)
    else:
        print(colored("[-]", 'red', attrs=['bold']) + " {0}: {1}".format(string, ex), file=sys.stderr)


def warn(string):
    print(colored("[!]", 'yellow', attrs=['bold']) + " {0}".format(string))

def info(string):
    print(colored("[*]", 'blue', attrs=['bold']) + " {0}".format(string))

def success(string):
    print(colored("[+]", 'green', attrs=['bold']) + " {0}".format(string))


def usage():
    __usage__ = "usage:\n\n"
    __usage__ += "  {0} -f <arg> [options] | -s <arg> [options] | -S <arg> | <misc>\n\n"
    __usage__ += "options:\n\n"
    __usage__ += "  -f <num>   - download chosen wordlist - ? to list wordlists with id\n"
    __usage__ += "  -d <dir>   - wordlists base directory (default: {1})\n"
    __usage__ += "  -c <num>   - change wordlists category - ? to list wordlists categories\n"
    __usage__ += "  -s <regex> - wordlist to search using <regex> in base directory\n"
    __usage__ += "  -S <regex> - wordlist to search using <regex> in sites\n"
    __usage__ += "  -h         - prefer http\n"
    __usage__ += "  -X         - decompress wordlist\n"
    __usage__ += "  -F <str>   - list wordlists in categories given\n"
    __usage__ += "  -r         - remove compressed file after decompression\n"
    __usage__ += "  -t <num>   - max download threads (default: {0})\n\n".format(__max_trds__)
    __usage__ += "misc:\n\n"
    __usage__ += "  -U         - update config files\n"
    __usage__ += "  -V         - print version of wordlistctl and exit\n"
    __usage__ += "  -H         - print this help and exit\n\n"
    __usage__ += "example:\n\n"
    __usage__ += "  # download and decompress all wordlists and remove archive\n"
    __usage__ += "  $ wordlistctl -f 0 -Xr\n\n"
    __usage__ += "  # download all wordlists in username category\n"
    __usage__ += "  $ wordlistctl -f 0 -c 0\n\n"
    __usage__ += "  # list all wordlists in password category with id\n"
    __usage__ += "  $ wordlistctl -f ? -c 1\n\n"
    __usage__ += "  # download and decompress all wordlists in misc category\n"
    __usage__ += "  $ wordlistctl -f 0 -c 4 -X\n\n"
    __usage__ += "  # download all wordlists in filename category using 20 threads\n"
    __usage__ += "  $ wordlistctl -c 3 -f 0 -t 20\n\n"
    __usage__ += "  # download wordlist with id 2 to \"~/wordlists\" directory using http\n"
    __usage__ += "  $ wordlistctl -f 2 -d ~/wordlists -h\n\n"
    __usage__ += "  # print wordlists in username and password categories\n"
    __usage__ += "  $ wordlistctl -F username,password\n"


    print(__usage__.format(__project__, __wordlist_path__))


def version():
    __str_version__ = "{0} v{1}".format(__project__, __version__)
    print(__str_version__)


def banner():
    __str_banner__ = "--==[ {0} by {1} ]==--\n".format(__project__, __organization__)
    print(colored(__str_banner__, 'red', attrs=['bold']))


def decompress_gbl(infilename):
    filename = os.path.basename(infilename)
    try:
        infile = None
        __outfile__ = os.path.splitext(infilename)[0]
        if os.path.isfile(__outfile__):
            warn("{0} already exists -- skipping".format(os.path.basename(__outfile__)))
        else:
            if re.fullmatch(r"^.*\.(gz)$", infilename.lower()):
                infile = gzip.GzipFile(infilename, 'rb')
            elif re.fullmatch(r"^.*\.(bz|bz2)$", infilename.lower()):
                infile = bz2.BZ2File(infilename, 'rb')
            elif re.fullmatch(r"^.*\.(lzma|xz)$", infilename.lower()):
                infile = lzma.LZMAFile(infilename, 'rb')
            else:
                raise ValueError('unknown file type')
            info("decompressing {0}".format(filename))
            outfile = open(__outfile__, 'wb')
            copyfileobj(infile, outfile)
            outfile.close()
            success("decompressing {0} completed".format(filename))
    except Exception as ex:
        err('Error while decompressing {0}'.format(filename), str(ex))
        return -1


def decompress_archive(infilename):
    filename = os.path.basename(infilename)
    try:
        os.chdir(os.path.dirname(infilename))
        info("decompressing {0}".format(filename))
        if re.fullmatch(r"^.*\.(rar)$", filename.lower()):
            infile = rarfile.RarFile(infilename)
            infile.extractall()
        else:
            libarchive.extract_file(infilename)
        success("decompressing {0} completed".format(filename))
    except Exception as ex:
        err('Error while decompressing {0}'.format(filename), str(ex))
        return -1


def decompress(infilename):
    filename = os.path.basename(infilename)

    if (not __decompress__) or (infilename.endswith('.torrent')):
        return
    try:
        if re.fullmatch(r"^.*\.(rar|zip|7z|tar|tar.gz|tar.xz|tar.bz2)$", filename.lower()):
            return decompress_archive(infilename)
        elif re.fullmatch(r"^.*\.(gz|bz|bz2|lzma)$", filename.lower()):
            return decompress_gbl(infilename)
        else:
            return -1
    except Exception as ex:
        err('Error while decompressing {0}'.format(filename), str(ex))
        return -1


def clean(filename):
    if __remove__ and not re.fullmatch(r"^.*\.(txt|lst|torrent)$", filename.lower()):
        remove(filename)


def remove(filename):
    try:
        os.remove(filename)
    except:
        pass


def resolve_mediafire(link):
    resolved = ''
    try:
        page = requests.get(link, headers={'User-Agent': __useragent__})
        html = BeautifulSoup(page.text, 'html.parser')
        for i in html.find_all('a'):
            if str(i.text).startswith('Download ('):
                resolved = i['href']
    except:
        pass
    finally:
        return resolved


def run_threaded(func):
    def wrapper(url, path):
        if func.__name__ == 'fetch_torrent':
            global __session__
            if __session__ is None:
                __session__ = libtorrent.session({'listen_interfaces': '0.0.0.0:6881'})
                __session__.start_dht()
        elif str(path).endswith('.torrent'):
            func(url, path)
            return
        try:
            while True:
                if __trds__.__len__() >= __max_trds__:
                    for i in __trds__:
                        if not i.isAlive():
                            __trds__.remove(i)
                    time.sleep(0.01)
                else:
                    break
            t = threading.Thread(target=func, args=(url, path))
            t.start()
            __trds__.append(t)
        except KeyboardInterrupt:
            exit(0)
        except:
            pass
    return wrapper


@run_threaded
def fetch_file(url, path):
    filename = os.path.basename(path)
    str_url = url
    try:
        if check_file(path):
            warn("{0} already exists -- skipping".format(filename))
        else:
            info("downloading {0}".format(filename))
            if str(url).startswith('http://www.mediafire.com/file/'):
                str_url = resolve_mediafire(url)
            chunk_size = 1024
            rq = requests.get(str_url, stream=True, headers={'User-Agent': __useragent__})
            fp = open(path, 'wb')
            for data in rq.iter_content(chunk_size=chunk_size):
                fp.write(data)
            fp.close()
            success("downloading {0} completed".format(filename))
        if decompress(path) != -1:
            clean(path)
    except KeyboardInterrupt:
        return
    except Exception as ex:
        err("Error while downloading {0}".format(url), str(ex))
        remove(path)


@run_threaded
def fetch_torrent(url, path):
    global __session__
    magnet = False
    if str(url).startswith('magnet:?'):
        magnet = True
    handle = None
    try:
        if magnet:
            handle = libtorrent.add_magnet_uri(__session__, url,
                                               {'save_path': os.path.dirname(path), 'storage_mode': libtorrent.storage_mode_t(2),
                                                'paused': False, 'auto_managed': True, 'duplicate_is_error': True}
                                               )
            info('downloading metadata\n')
            while not handle.has_metadata():
                time.sleep(0.1)
            success('downloaded metadata')
        else:
            fetch_file(url, path)

            if os.path.isfile(path):
                handle = __session__.add_torrent({'ti': libtorrent.torrent_info(path), 'save_path': os.path.dirname(path)})
                remove(path)
            else:
                err("{0} not found".format(path))
                exit(-1)
        __outfilename__ = "{0}/{1}".format(os.path.dirname(path), handle.name())
        if check_file(__outfilename__):
            warn("{0} already exists -- skipping".format(handle.name()))
            __session__.remove_torrent(handle)
        else:
            info("downloading {0}".format(handle.name()))
            while not handle.is_seed():
                time.sleep(0.1)
            __session__.remove_torrent(handle)
            success('downloading {0} completed'.format(handle.name()))
        if decompress(__outfilename__) != -1:
            clean(__outfilename__)
    except KeyboardInterrupt:
        return
    except Exception as ex:
        err("Error while downloading {0}".format(url), str(ex))
        remove(path)


def download_wordlist(config, wordlistname):

    __filename__ = ''
    __file_directory__ = ''
    __file_path__ = ''

    if __category__ != '':
        check_dir("{0}/{1}".format(__wordlist_path__, __category__))
        __file_directory__ = "{0}/{1}".format(__wordlist_path__, __category__)
    else:
        for i in __categories__:
            if wordlistname in __categories__[i]:
                check_dir("{0}/{1}".format(__wordlist_path__, i))
                __file_directory__ = "{0}/{1}".format(__wordlist_path__, i)
                break

    try:
        if (__prefer_http__ and config['http'] != "") or (config['torrent'] == "" and config['http'] != ""):
            __filename__ = config['http'].split('/')[-1]
            __file_path__ = "{0}/{1}".format(__file_directory__, __filename__)
            fetch_file(config['http'], __file_path__)

        elif config['torrent'] != "":
            __filename__ = config['torrent'].split('/')[-1]
            __file_path__ = "{0}/{1}".format(__file_directory__, __filename__)
            fetch_torrent(config['torrent'], __file_path__)

        else:
            raise ValueError("unable to find wordlist's url")


    except Exception as ex:
        err('unable to download wordlist', str(ex))
        return -1

def download_wordlists(code):
    __wordlist_id__ = 0

    check_dir(__wordlist_path__)

    __wordlist_id__ = to_int(code)
    try:
        if (__wordlist_id__ >= __urls__.__len__() + 1) or __wordlist_id__ < 0:
            raise IndexError('{0} is not a valid wordlist id'.format(code))
        elif __wordlist_id__ == 0:
            if __category__ == '':
                for i in __urls__:
                    download_wordlist(__urls__[i], i)
            else:
                for i in __categories__[__category__]:
                    download_wordlist(__urls__[i], i)
        elif __category__ != '':
            i = __urls__[__categories__[__category__][__wordlist_id__ - 1]]
            download_wordlist(i, __categories__[__category__][__wordlist_id__ - 1])
        else:
            i = list(__urls__.keys())[__wordlist_id__ - 1]
            download_wordlist(__urls__[i], list(__urls__.keys())[__wordlist_id__ - 1])
    except Exception as ex:
        err("Error unable to download wordlist", str(ex))
        return -1
    return 0


def print_wordlists(categories=''):
    if categories == '':
        index = 1
        success("available wordlists:")
        print("    > 0  - all wordlists")
        urls = {}
        if __category__ != '':
            urls = __categories__[__category__]
        else:
            urls = __urls__.keys()
        for i in urls:
            print("    > {0}  - {1}".format(index, i))
            index += 1
        print("")
    else:
        categories_list = set([i.strip() for i in categories.split(',')])
        for i in categories_list:
            if i not in __categories__.keys():
                err("category {0} is unavailable".format(i))
                exit(-1)
        for i in categories_list:
            success("{0}:".format(i))
            for j in __categories__[i]:
                print("    > {0}".format(j))
            print("")

def search_dir(regex):
    info('searching for {0} in {1}\n'.format(regex, __wordlist_path__))
    os.chdir(__wordlist_path__)
    files = glob.glob("{0}".format(str(regex)))
    if files.__len__() <= 0:
        err("wordlist not found")
        return
    for file in files:
        success("wordlist found: {0}".format(os.path.join(__wordlist_path__, file)))


def search_sites(regex):
    urls = []
    if __category__ != '':
        urls = list(__categories__[__category__])
    else:
        urls = list(__urls__.keys())
    try:
        info('searching for {0} in urls.json\n'.format(regex))
        count = 0
        for i in urls:
            if re.match(regex, i):
                success('wordlist {0} found: id={1}'.format(i, urls.index(i) + 1))
                count += 1

        if count == 0:
            err('no wordlist found')
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        err('Error while searching', str(ex))
        return -1


def check_dir(dir_name):
    try:
        if os.path.isdir(dir_name):
            pass
        else:
            info("creating directory {0}".format(dir_name))
            os.mkdir(dir_name)
    except Exception as ex:
        err("unable to change base directory", str(ex))
        exit(-1)


def check_file(path):
    return glob.glob("{0}*".format(str(path).split('.')[0])).__len__() > 0


def load_json(infilename):
    try:
        return json.load(open(infilename, 'r'))
    except Exception as ex:
        err('unable to load {0}'.format(infilename), str(ex))
        return {}


def change_category(code):
    global __category__
    global __categories__
    __category_id__ = 0
    if __categories__.__len__() <= 0:
        load_config()

    __category_id__ = to_int(code)

    try:
        if (__category_id__ >= __categories__.__len__()) or __category_id__ < 0:
            raise IndexError('{0} is not a valid category id'.format(code))
        __category__ = list(__categories__.keys())[__category_id__]
    except Exception as ex:
        err('Error while changing category', str(ex))
        exit(-1)


def print_categories():
    index = 0
    success("available wordlists category:")
    for i in __categories__:
        print("    > {0}  - {1} ({2} wordlists)".format(index, i, list(__categories__[i]).__len__()))
        index += 1
    print("")


def update_config():
    global __urls__
    global __categories__
    __base_url__ = 'https://raw.githubusercontent.com/BlackArch/wordlistctl/master'
    files = [__urls_file_name__, __categories_file_name__]
    try:
        info('updating config files\n')
        for i in files:
            if os.path.isfile(i):
                remove(i)
            fetch_file('{0}/{1}'.format(__base_url__, os.path.basename(i)), i)
        for i in __trds__:
            i.join()
        load_config()
        success('updating config files completed')
    except Exception as ex:
        err('Error while updating', str(ex))
        exit(-1)


def load_config():
    global __urls__
    global __categories__
    files = [__urls_file_name__, __categories_file_name__]
    if __urls__.__len__() <= 0 or __categories__.__len__() <= 0:
        try:
            for i in files:
                if not os.path.isfile(i):
                    raise FileNotFoundError('Config files not found please update')
            __urls__ = load_json(__urls_file_name__)
            __categories__ = load_json(__categories_file_name__)
        except Exception as ex:
            err('Error while loading config files', str(ex))
            exit(-1)


def to_int(string):
    try:
        return int(string)
    except:
        err('{0} is not a valid number'.format(string))
        exit(-1)


def arg_parse(argv):
    global __wordlist_path__
    global __decompress__
    global __remove__
    global __prefer_http__
    global __max_trds__
    __operation__ = None
    __arg__ = None
    opFlag = 0

    try:
        opts, _ = getopt.getopt(argv[1:], "HVUXhrd:c:f:s:S:t:F:")

        if opts.__len__() <= 0:
            __operation__ = usage
            return __operation__, None

        for opt, arg in opts:
            if opFlag and re.fullmatch(r"^-([VfsSUF])", opt):
                raise getopt.GetoptError("multiple operations selected")
            if opt == '-H':
                __operation__ = usage
                return __operation__, None
            elif opt == '-V':
                __operation__ = version
                opFlag += 1
            elif opt == '-d':
                dirname = os.path.abspath(arg)
                check_dir(dirname)
                __wordlist_path__ = dirname
            elif opt == '-f':
                if arg == '?':
                    __operation__ = print_wordlists
                else:
                    __operation__ = download_wordlists
                    __arg__ = arg
                opFlag += 1
            elif opt == '-s':
                __operation__ = search_dir
                __arg__ = arg
                opFlag += 1
            elif opt == '-X':
                __decompress__ = True
            elif opt == '-r':
                __remove__ = True
            elif opt == '-U':
                __operation__ = update_config
                opFlag += 1
            elif opt == '-S':
                __operation__ = search_sites
                __arg__ = arg
                opFlag += 1
            elif opt == '-c':
                if arg == '?':
                    __operation__ = print_categories
                    return __operation__, None
                else:
                    change_category(arg)
            elif opt == '-h':
                __prefer_http__ = True
            elif opt == '-t':
                __max_trds__ = to_int(arg)
                if __max_trds__ <= 0:
                    raise Exception("threads number can't be less than 1")
            elif opt == '-F':
                __operation__ = print_wordlists
                __arg__ = arg
                opFlag += 1
    except getopt.GetoptError as ex:
        err("Error while parsing arguments", str(ex))
        warn("-H for help and usage")
        exit(-1)
    except Exception as ex:
        err("Error while parsing arguments", str(ex))
        exit(-1)
    return __operation__, __arg__


def main(argv):
    global __urls_file_name__
    global __categories_file_name__
    banner()
    __base_name__ = os.path.dirname(os.path.realpath(__file__))
    __urls_file_name__ = '{0}/urls.json'.format(__base_name__)
    __categories_file_name__ = '{0}/categories.json'.format(__base_name__)

    __operation__, __arg__ = arg_parse(argv)

    try:
        if __operation__ not in [update_config, version, usage]:
            load_config()
        if __operation__ is not None:
            if __arg__ is not None:
                __operation__(__arg__)
            else:
                __operation__()
        else:
            raise getopt.GetoptError("no operation selected")
        return 0
    except getopt.GetoptError as ex:
        err("Error while running operation", str(ex))
        warn("-H for help and usage")
        return -1
    except Exception as ex:
        err("Error while running operation", str(ex))
        return -1


if __name__ == '__main__':
    try:
        import sys
        import os
        import getopt
        import requests
        import glob
        import re
        import threading
        import libtorrent
        import libarchive
        import time
        import gzip
        import bz2
        import lzma
        import rarfile
        from shutil import copyfileobj
        import json
        from bs4 import BeautifulSoup
        from termcolor import colored
    except Exception as ex:
        err("Error while loading dependencies", str(ex))
        exit(-1)

    sys.exit(main(sys.argv))
