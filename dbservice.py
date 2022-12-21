import pymysql
import os


class CustomerRepository:

    @classmethod
    def _get_connection(cls):
        usr = os.environ.get("DBUSER")
        pw = os.environ.get("DBPW")
        h = os.environ.get("DBHOST")

        conn = pymysql.connect(
            user=usr,
            password=pw,
            host=h,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn

    @classmethod
    def get_customer_by_email(cls, email: str):
        sql = "SELECT * FROM customer_database.customer where email=%s";
        conn = CustomerRepository._get_connection()
        cur = conn.cursor()
        res = cur.execute(sql, args=email)
        result = cur.fetchone()

        return result

    @classmethod
    def validate_login(cls, email, password):
        sql = "SELECT password FROM customer_database.registration_info where email=%s";
        conn = CustomerRepository._get_connection()
        cur = conn.cursor()
        res = cur.execute(sql, args=email)
        result = cur.fetchone()
        conn.close()
        if not result: return False
        return password == result['password']

    @classmethod
    def register_user(cls, email, fname, lname, phone, password):
        exist = cls.get_customer_by_email(email)
        if exist: return False
        sql1 = "INSERT INTO customer_database.customer(first_name, last_name, email, phone_number) VALUES (%s, %s, %s, %s);"
        sql2 = "INSERT INTO customer_database.registration_info VALUES (%s, %s);"
        conn = CustomerRepository._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql1, args=[fname, lname, email, phone])
            if password:
                cur.execute(sql2, args=[email, password])
        except:
            conn.rollback()
            conn.close()
            return False
        else:
            conn.commit()
            conn.close()
            return True

    @classmethod
    def update_user_profile(cls, email, new):

        set_stmt_list = []
        for k, v in new.items():
            set_stmt_list.append(f"{k}='{v}'")

        sql = "UPDATE customer_database.customer SET "
        sql += ", ".join(set_stmt_list)
        sql += " WHERE email=%s"

        conn = CustomerRepository._get_connection()
        cur = conn.cursor()
        cur.execute(sql, args=email)
        conn.commit()
        row_affected = cur.rowcount
        conn.close()

        return row_affected
