import time


def test_db_smoke(db_session_conn, apply_seed_fixture):
    # Create a setting and read it back
    cur = db_session_conn.cursor(dictionary=True)
    apply_seed_fixture(seed_name='common')
    ts_millis = int(round(time.time() * 1000))
    cur.execute(""
                "INSERT INTO settings"
                "(created_at, the_key, the_value, the_type)"
                "VALUES (%s, %s, %s, %s)"
                "",
                (ts_millis, 'first_key', 'hello world', 5))
    db_session_conn.commit()

    cur.execute("SELECT * FROM settings WHERE the_key=%s", ("first_key",))
    row = cur.fetchone()
    cur.close()
    print(row)
    assert row is not None
    assert row['created_at'] == ts_millis
    assert row['updated_at'] is None
    assert row['the_key'] == 'first_key'
    assert row['the_value'] == 'hello world'
    assert row['the_type'] == 5

    apply_seed_fixture(seed_name='', files='clear.sql')