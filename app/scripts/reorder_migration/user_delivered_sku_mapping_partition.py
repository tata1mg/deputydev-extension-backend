import psycopg2
import sys, datetime
from psycopg2.extras import NamedTupleConnection

'''
    These numbers should not be changed once deployed
'''

MASTER_TABLE = 'user_delivered_skus_mapping'
HASH_PARTITION = 2 # will go forward with 3
START_TIMESTAMP = 1539806835  # 1451586600 1st jan 2016
TIME_GAP = 20000000  # 15552000 180 days
ADD_BEFORE_TIME_GAP = 8640000  # 864000 attach partition before 10 days
DETACH_AFTER_TIME_GAP = 31536000  # 31536000 detach a partition if its beyond 365 days

TABLE_MAP = {}
MIN_MAX_MAP = {}

def _get_db_connection(database: str, user: str, password: str, host: str, port: int):
    try:
        connection = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        return connection
    except:
        sys.exit("could not connect to database: '{}'".format(database))


def _get_cursor_from_connection(connection):
    return connection.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)


def curr_time_stamp():
    return int(datetime.datetime.now().timestamp())


def table_map(connection):
    if not TABLE_MAP:
        cursor = _get_cursor_from_connection(connection)
        cursor.execute("""SELECT table_name FROM information_schema.tables
               WHERE table_schema = 'public'""")
        for table in cursor.fetchall():
            name = table.table_name
            if name.startswith(MASTER_TABLE) and len(name) - len(MASTER_TABLE) > 5:
                hash_partition_index, range_partition_index, range = name[len(MASTER_TABLE) + 1:].split('_')
                if hash_partition_index not in TABLE_MAP:
                    TABLE_MAP[hash_partition_index] = []
                    MIN_MAX_MAP[hash_partition_index] = {'min': 999999, 'max': -1}
                TABLE_MAP[hash_partition_index].append({'range': range, 'range_partition_index': range_partition_index})
                MIN_MAX_MAP[hash_partition_index]['min'] = min(MIN_MAX_MAP[hash_partition_index]['min'], int(range_partition_index))
                MIN_MAX_MAP[hash_partition_index]['max'] = max(MIN_MAX_MAP[hash_partition_index]['max'], int(range_partition_index))
    return TABLE_MAP


def check_and_add_table(connection):
    cursor = _get_cursor_from_connection(connection)
    for index in range(HASH_PARTITION):
        tables = sorted(table_map(connection)[str(index)], key = lambda i: (i['range']))
        already_created_timestamp = int(tables[len(tables)-1]['range'].split('to')[1])
        if (already_created_timestamp - curr_time_stamp()) < ADD_BEFORE_TIME_GAP:
            partition_table = "{}_{}".format(MASTER_TABLE, index)
            timestamp_range = "{}to{}".format(already_created_timestamp, already_created_timestamp + TIME_GAP)
            table = "{}_{}_{}".format(partition_table, MIN_MAX_MAP[str(index)]['max']+1, timestamp_range)
            query = "create table {} partition of {} for values from ({}) to ({});".format(table, partition_table, already_created_timestamp, already_created_timestamp+TIME_GAP)
            print(query)
            cursor.execute(query)


def check_and_detach_table(connection):
    cursor = _get_cursor_from_connection(connection)
    for index in range(HASH_PARTITION):
        tables = sorted(table_map(connection)[str(index)], key = lambda i: (i['range']))
        for name in tables:
            to_detach_timestamp = int(name['range'].split('to')[1])
            if curr_time_stamp() - to_detach_timestamp > DETACH_AFTER_TIME_GAP:
                partition_table = "{}_{}".format(MASTER_TABLE, index)
                timestamp_range = "{}to{}".format(to_detach_timestamp - TIME_GAP, to_detach_timestamp)
                table = "{}_{}_{}".format(partition_table, name['range_partition_index'], timestamp_range)
                query = "alter table {} detach partition {};".format(partition_table, table)
                try:
                    cursor.execute(query)
                    print(query)
                except:
                    print('Table already detached {}'.format(table))


def main():
    connection = _get_db_connection('sidhantmishra', 'sidhantmishra', None, 'localhost', 5432)

    check_and_add_table(connection)
    check_and_detach_table(connection)
    connection.commit()
    connection.close()

if __name__ == "__main__":
    main()