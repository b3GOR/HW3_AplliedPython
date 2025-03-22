import shortuuid
import psycopg2

def generate_short_link(long_link):
    gen_short_link = shortuuid.uuid()
    short_link= f'https://{gen_short_link}'
    return long_link,short_link

def post_db(long_link,short_link):
    with psycopg2.connect(
        dbname="long_short_service",
        user="postgres",
        host="localhost",
        port=5432
    ) as connection:
        with connection.cursor() as cursor:
            query = '''INSERT INTO long_short_links (long_links, short_links) 
                           VALUES (%s, %s)'''
            cursor.execute(query, (long_link, short_link))  
            connection.commit()


  