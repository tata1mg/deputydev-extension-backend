import asyncio
import  asyncpg, pickle
import json
from dateutil import parser
import datetime

host = 'order_service-replicadb.1mginfra.com'
db = 'order_service_db'
user = 'order_service_user'
password = 'order_service_pass'
port = 5432

w_host = 'zeus_service-db.1mginfra.com'
w_db = 'zeus_service_db'
w_user = 'zeus_service_user'
w_password = 'zeus_service_pass'
w_port = 5432

# host = '13.126.208.32'
# db = 'order_service_db'
# user = 'order_service_user'
# password = 'order_service_pass'
# port = 5432
#
# w_host = '13.126.208.32'
# w_db = 'postgres'
# w_user = 'postgres'
# w_password = 'YnTUTRArpudPbiqTFVyx'
# w_port = 7010


map_file_name = 'reorder-widget-'

start_order_details_id = 14743186
max_order_details_id_file = 'max-order-details-id'

async def get_order_delivered_data(_db_obj, limit, offset):
    print('start id ', start_order_details_id, ' limit ', limit, ' offset ', offset)
    rows = await _db_obj.fetch("""select id, order_id, user_id, created from order_details where status = '40' and id > {} order by id limit {} offset {}""".format(start_order_details_id, limit, offset))
    # rows = await _db_obj.fetch("""select id, order_id, user_id, delivery_date from order_details where status = '40' order by id limit {} offset {}""".format(limit, offset))
    # rows = [dict(row) for row in rows]
    ret = []
    for row in rows:
        row = dict(row)
        t = row['created'].timestamp()
        row['ordered_at'] = int(t)
        ret.append(row)
    return ret

def reset_pickle_file():
    for i in range(25):
        file_name = map_file_name+str(i)
        file = open(file_name, 'wb')
        pickle.dump({}, file)
        file.close()

    print('All Pickle file reset done')

def combined_user_id_count():

    length = 0
    max_length = 0

    for i in range(25):
        file_name = map_file_name+str(i)
        file = open(file_name, 'rb')
        l = len(pickle.load(file))
        max_length = max(max_length, l)
        length += l
        file.close()

    print('Length of total user id ', length, 'max length of file ', max_length)


def find_max_id_done():
    dbfile = open(max_order_details_id_file, 'rb')
    db1 = pickle.load(dbfile)
    print('Max order details id handled', db1)
    dbfile.close()

async def main():
    cur = await asyncpg.connect(database=db, user=user, password=password, host=host, port=port)
    write_cur = await asyncpg.connect(database=w_db, user=w_user, password=w_password, host=w_host, port=w_port)
    limit = 25000
    offset = 0
    tmp_offset = 0
    reset_pickle_file()
    while(True):
        data = await get_order_delivered_data(cur, limit, tmp_offset)
        print('offset', offset, 'length', len(data))

        file_name = map_file_name + str(offset//800000)
        file = open(file_name, 'rb')
        map = pickle.load(file)
        file.close()

        for row in data:
            if row['user_id'] in map:
                map[row['user_id']].append({'order_id': row['order_id'], 'id': row['id'], 'ordered_at': row['ordered_at']})
            else:
                map[row['user_id']] = [{'order_id': row['order_id'], 'id': row['id'], 'ordered_at': row['ordered_at']}]

        file = open(file_name, 'wb')
        pickle.dump(map, file)
        file.close()

        file = open(max_order_details_id_file, 'wb')
        pickle.dump(data[-1]['id'], file)
        file.close()
        print('Done copying, filename ', file_name, ' length ', len(map))

        if len(data) < limit:
            break

        offset += limit
        tmp_offset += limit

        if offset % 800000 == 0:
            global start_order_details_id
            start_order_details_id = data[-1]['id']
            tmp_offset = 0


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    find_max_id_done()
    combined_user_id_count()
    print('done')