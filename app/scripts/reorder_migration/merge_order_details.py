import asyncio
import  asyncpg, pickle
import json
from dateutil import parser
import datetime

map_file_name = 'reorder-widget-'
merge_write_name = 'merged-reorder-widget-'
user_ids = set()

data_set = []
total_user_id = 0
for i in range(25):

    write_map = {}

    for j in range(25):

        file_name = map_file_name + str(j)
        file = open(file_name, 'rb')
        map = pickle.load(file)
        file.close()

        print('Reading from file ', file_name, ' for i ', i)

        for key, value in map.items():
            write_no = ord(key[-1]) % 25
            if write_no == i:
                if key in write_map:
                    write_map[key].extend(value)
                else:
                    write_map[key] = value

    file_name = merge_write_name + str(i)
    total_user_id += len(write_map)
    print('write file name ', file_name, ' length ', len(write_map))
    file = open(file_name, 'wb')
    pickle.dump(write_map, file)
    file.close()

print('Length of total user id ', total_user_id)