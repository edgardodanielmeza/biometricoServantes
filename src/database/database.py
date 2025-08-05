import sqlite3
import hashlib

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return None
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()

    def _hash_password(self, password):
        salt = "SistemaBiometricoCervantes2023"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def check_credentials(self, username, password):
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_pwd FROM sys_user WHERE username=?", (username,))
            result = cursor.fetchone()

            if not result:
                return False

            stored_password = result[0]

            if len(stored_password) != 64:
                if password == stored_password:
                    hashed_password = self._hash_password(password)
                    cursor.execute("UPDATE sys_user SET user_pwd = ? WHERE username = ?", (hashed_password, username))
                    self.conn.commit()
                    return True
                else:
                    return False

            return self._hash_password(password) == stored_password
        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
            return False
        finally:
            self.close()

    def get_employees(self):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT emp_pin, emp_firstname, emp_lastname FROM hr_employee")
        employees = cursor.fetchall()
        self.close()
        return employees

    def get_daily_attendance(self, emp_pin, start_date, end_date):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', att_date), checkin, checkout
            FROM att_day_details
            WHERE employee_id = (SELECT id FROM hr_employee WHERE emp_pin = ?)
            AND att_date BETWEEN ? AND ?
        """, (emp_pin, start_date, end_date))
        attendance = cursor.fetchall()
        self.close()
        return attendance

    def get_all_employees_data(self):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, emp_pin, emp_firstname, emp_lastname FROM hr_employee")
        employees = cursor.fetchall()
        self.close()
        return employees

    def get_monthly_attendance(self, year, month):
        self.connect()
        cursor = self.conn.cursor()

        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-31"

        query = """
            SELECT
                e.emp_pin,
                e.emp_firstname,
                e.emp_lastname,
                strftime('%Y-%m-%d', p.punch_time) as fecha,
                min(strftime('%H:%M:%S', p.punch_time)),
                max(strftime('%H:%M:%S', p.punch_time))
            FROM
                hr_employee e
            LEFT JOIN
                att_punches p ON e.id = p.employee_id
            WHERE
                 e.emp_active = 1 AND strftime('%Y-%m', p.punch_time) = ?
            GROUP BY
                e.id, fecha
            ORDER BY
                e.emp_lastname, e.emp_firstname, fecha;
        """

        cursor.execute(query, (f"{year}-{month:02d}",))

        data = cursor.fetchall()
        self.close()
        return data
