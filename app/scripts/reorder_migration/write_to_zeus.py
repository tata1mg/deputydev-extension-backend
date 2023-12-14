import asyncio
import  asyncpg, pickle, datetime
import json
from dateutil import parser

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

map_file_name_write = 'user-sku-'

async def get_order_delivered_data(_db_obj, limit, offset):
    rows = await _db_obj.fetch("""select * from temp order by id limit {} offset {}""".format(limit, offset))
    return rows

async def get_order_delivered_data1(_db_obj, limit, offset):
    rows = await _db_obj.fetch("""select * from recency_logic_table""")
    return rows


async def insert_data_in_temp(con, _data):
    for d in _data:
        query = "insert into temp (user_id, data) values ('{}', '{}')".format(d['user_id'], d['data'])
        await con.execute(query)


async def insert_data_in_db(con, _data):

    arr = []
    inserted = 0

    for user_id, value in _data.items():
        # for value in values:
        sp = user_id.rsplit('-', 1)
        user_id = sp[0]
        sku_id = sp[1]
        quantity = int(value['quantity'])
        value['ordered_at'].sort(reverse=True)
        most_recent_order = value['ordered_at'][0]
        ordered_at = [str(i) for i in value['ordered_at']]
        ordered_at = ','.join(ordered_at)
        ordered_at = '{' + ordered_at + '}'
        created_at = datetime.datetime.now().strftime('%Y-%m-%d')
        combine = "('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(user_id, created_at, created_at, sku_id, quantity,
                                                                      ordered_at, most_recent_order)
        arr.append(combine)

        if arr and len(arr) == 25000:
            brr = ','.join(arr)
            query = "Insert into user_delivered_skus_mapping (user_id, created_at, updated_at, sku_id, quantity, ordered_at, most_recent_order) values " + brr
            await con.execute(query)
            arr = []
            inserted += 25000
            print(inserted)
    if arr:
        brr = ','.join(arr)
        query = "Insert into user_delivered_skus_mapping (user_id, created_at, updated_at, sku_id, quantity, ordered_at, most_recent_order) values " + brr
        await con.execute(query)


async def insert_data_in_db1(con, _data):
    for d in _data:
        query = "insert into recency_logic_table (lower_limit, value) values ('{}','{}')".format(d['lower_limit'], d['value'])
        await con.execute(query)

async def main():
    # cur = await asyncpg.connect(database=db, user=user, password=password, host=host, port=port)
    write_cur = await asyncpg.connect(database=w_db, user=w_user, password=w_password, host=w_host, port=w_port)

    for i in range(25):
        file_name = map_file_name_write + str(i)
        file = open(file_name, 'rb')
        data = pickle.load(file)
        print(file_name)
        await insert_data_in_db( write_cur, data)
        file.close()





if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print('done')