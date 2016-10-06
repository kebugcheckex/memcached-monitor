# A tool for monitoring memcached stats
# Written by Xinyu Chen

import argparse
import memcache
import shutil
import time

from colorama import Fore


def compute_ratio(stats, name):
    hits = int(stats[name + '_hits'])
    misses = int(stats[name + '_misses'])
    total = hits + misses
    if total == 0:
        res = 0
    else:
        res = hits / total
    return "{:6.2f}".format(res * 100)


def convert_bytes(n_bytes):
    if n_bytes < 1024:
        return n_bytes
    if n_bytes < 1024**2:
        return "{0:.2f}k".format(n_bytes / 1024)
    if n_bytes < 1024**3:
        return "{0:.2f}M".format(n_bytes / (1024**2))
    return "{0:.2}G".format(n_bytes / (1024**3))


def convert_decimal(n_dec):
    if n_dec < 1000:
        return n_dec
    if n_dec < 1000**2:
        return "{0:.2f}k".format(n_dec / 1000)
    if n_dec < 1000**3:
        return "{0:.2f}M".format(n_dec / 1000**2)
    return "{0:.2f}G".format(n_dec / 1000**3)


# Column tuple format:
# 0:entry_type, 1:key_name, 2:display_name, 3:verbosity, 4:text_color
# Note
#   - entry_type: 0 (simple), 1 (compute), 2 (special), 3 (bytes)
columns = [(2, 'time',              '  time ', 1, Fore.WHITE),
           (0, 'curr_connections',  'cur_con', 1, Fore.WHITE),
           (0, 'total_connections', 'tot_con', 3, Fore.WHITE),
           (0, 'cmd_get',           'cmd_get', 3, Fore.BLUE),
           (0, 'cmd_set',           'cmd_set', 3, Fore.BLUE),
           (0, 'get_hits',          'get_hit', 2, Fore.RED),
           (0, 'get_misses',        'get_mis', 2, Fore.RED),
           (1, 'get',               ' get % ', 1, Fore.RED),
           (0, 'delete_hits',       'del_hit', 2, Fore.MAGENTA),
           (0, 'delete_misses',     'del_mis', 2, Fore.MAGENTA),
           (1, 'delete',            ' del % ', 1, Fore.MAGENTA),
           (0, 'incr_hits',         'inc_hit', 3, Fore.GREEN),
           (0, 'incr_misses',       'inc_mis', 3, Fore.GREEN),
           (1, 'incr',              ' inc % ', 2, Fore.GREEN),
           (0, 'decr_hits',         'dec_hit', 3, Fore.YELLOW),
           (0, 'decr_misses',       'dec_mis', 3, Fore.YELLOW),
           (1, 'decr',              ' dec % ', 2, Fore.YELLOW),
           (0, 'curr_items',        'cur_itm', 1, Fore.CYAN),
           (0, 'total_items',       'tot_itm', 3, Fore.CYAN),
           (3, 'bytes',             ' bytes ', 1, Fore.RED),
           (0, 'evictions',         ' evict ', 1, Fore.RED)]


def print_table_header(verbosity):
    print('+', end='')
    for col in columns:
        if verbosity >= col[3]:
            print('-------', end='+')
    print('\n|', end='')
    for col in columns:
        if verbosity >= col[3]:
            print(col[4] + col[2] + Fore.RESET, end='|')
    print('\n+', end='')
    for col in columns:
        if verbosity >= col[3]:
            print('-------', end='+')
    print()


def print_table_row(stats, verbosity):
    print('|', end='')
    for col in columns:
        if verbosity >= col[3]:
            print(col[4], end='')
            if col[0] == 0:
                print('{0:>6} '.format(convert_decimal(int(stats[col[1]]))), end='')
            elif col[0] == 1:
                print('{0:7}'.format(compute_ratio(stats, col[1])), end='')
            elif col[0] == 2:
                print(' {0} '.format(time.strftime("%M:%S")), end='')
            elif col[0] == 3:
                print('{0:>6} '.format(convert_bytes(int(stats[col[1]]))), end='')
            print(Fore.RESET, end='|')
    print()

parser = argparse.ArgumentParser(description='A memcached stats monitoring tool')
parser.add_argument('-o', '--host', help='host name or IP address of the memcached server', default='127.0.0.1')
parser.add_argument('-p', '--port', help='port number of the memcached server', type=int, default=11211)
parser.add_argument('-r', '--refresh', help='refreshing rate in seconds', type=int, default=3)
parser.add_argument('-v', '--verbosity', action='count', default=1)
args = parser.parse_args()

mc = memcache.Client(["{0}:{1}".format(args.host, args.port)], debug=0)
count = 0
print_table_header(args.verbosity)
while True:
    mc_stats = mc.get_stats()
    if len(mc_stats) == 0:
        print('Memcached does not return stats data. Probably lost connection.')
        break
    stats_data = mc_stats[0][1]
    rows = shutil.get_terminal_size((60, 20)).lines
    if count > rows - 3:
        count = 0
        print_table_header(args.verbosity)
    print_table_row(stats_data, args.verbosity)
    count += 1
    time.sleep(args.refresh)

