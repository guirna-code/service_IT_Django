import psycopg2
import sys
import traceback

params = dict(dbname='db_service_IT', user='postgres', password='yahya', host='localhost', port='7777')
for k, v in params.items():
    print(k, type(v), repr(v))
    try:
        print('utf8:', v.encode('utf-8'))
    except Exception as e:
        print('encode error', e)

try:
    conn = psycopg2.connect(dbname=params['dbname'], user=params['user'], password=params['password'], host=params['host'], port=params['port'])
    print('connected')
    conn.close()
except Exception as e:
    print('EXC:', type(e), e)
    traceback.print_exc()
