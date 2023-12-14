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


map_file_name_read = 'merged-reorder-widget-'
map_file_name_write = 'user-sku-'


def reset_pickle_file():
    for i in range(25):
        file_name = map_file_name_write+str(i)
        file = open(file_name, 'wb')
        pickle.dump({}, file)
        file.close()

    print('All Pickle file reset done')


async def get_order_delivered_data(_db_obj, order_ids):
    ids = []
    for id in order_ids:
        ids.append("'"+id+"'")
    q = """select id, quantity, order_id from order_lines where order_id in ({})""".format(','.join(ids))
    rows = await _db_obj.fetch(q)
    rows = [dict(row) for row in rows]
    return rows

def read_file_data():
    file_name = map_file_name_write + str(0)
    file = open(file_name, 'rb')
    data = pickle.load(file)
    file.close()
    max = 0
    for key, value in data.items():
        if len(value['ordered_at']) > max:
            max = len(value['ordered_at'])
            print(key, value)


async def merge_order_lines(_db_obj):
    total_length = 0
    reset_pickle_file()
    for i in range(25):
        file_name = map_file_name_read + str(i)
        file = open(file_name, 'rb')
        map = pickle.load(file)
        file.close()

        print('read', file_name)

        # map = {'abcd': [{'order_id': 'PO11524374862-308-1', 'delivery_date': 'abcd'}]}
        order_to_user_map = {}
        user_sku_map = {}
        for user_id, values in map.items():
            for value in values:
                order_to_user_map[value['order_id']] = user_id
                if len(order_to_user_map) == 10000:
                    order_ids = list(order_to_user_map.keys())
                    rows = await get_order_delivered_data(_db_obj, order_ids)
                    print('fetched rows - ', len(rows), )
                    for row in rows:
                        order_id = row['order_id']
                        user_id = order_to_user_map[order_id]
                        for m in map[user_id]:
                            if m['order_id'] == order_id:
                                key = user_id + '-' + row['id']
                                if key in user_sku_map:
                                    user_sku_map[key]['ordered_at'].append(m['ordered_at'])
                                    user_sku_map[key]['ordered_at'].sort()
                                    if m['ordered_at'] == user_sku_map[key]['ordered_at'][-1]:
                                        user_sku_map[key]['quantity'] = row['quantity']
                                else:
                                    user_sku_map[key] = {'quantity': row['quantity'], 'ordered_at': [m['ordered_at']]}
                    order_to_user_map = {}

        if order_to_user_map:
            order_ids = list(order_to_user_map.keys())
            rows = await get_order_delivered_data(_db_obj, order_ids)
            print('fetched rows - ', len(rows))
            for row in rows:
                order_id = row['order_id']
                user_id = order_to_user_map[order_id]
                for m in map[user_id]:
                    if m['order_id'] == order_id:
                        key = user_id + '-' + row['id']
                        if key in user_sku_map:
                            user_sku_map[key]['ordered_at'].append(m['ordered_at'])
                            user_sku_map[key]['ordered_at'].sort()
                            if m['ordered_at'] == user_sku_map[key]['ordered_at'][-1]:
                                user_sku_map[key]['quantity'] = row['quantity']
                        else:
                            user_sku_map[key] = {'quantity': row['quantity'], 'ordered_at': [m['ordered_at']]}


        file_name = map_file_name_write + str(i)
        file = open(file_name, 'wb')
        pickle.dump(user_sku_map, file)
        file.close()
        total_length += len(user_sku_map)
        print('saved ', file_name, 'length user sku map ', len(user_sku_map))

    print('total length user sku map ', total_length)



async def main():
    cur = await asyncpg.connect(database=db, user=user, password=password, host=host, port=port)
    write_cur = await asyncpg.connect(database=w_db, user=w_user, password=w_password, host=w_host, port=w_port)
    await merge_order_lines(cur)



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print('done')