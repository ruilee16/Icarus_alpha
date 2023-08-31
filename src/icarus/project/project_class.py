import sqlite3
import os


def remind_to_create_tables(missing_tables):
    for table_name in missing_tables:
        print(f"Reminder: Table '{table_name}' does not exist in the database. Please create it.")


class Project:
    def __init__(self, db_url):
        self.db_url = db_url
        self.db_conn = sqlite3.connect(db_url)
        self.db_cursor = self.db_conn.cursor()

    def connect(self):
        self.db_conn = sqlite3.connect(self.db_url)
        self.db_cursor = self.db_conn.cursor()

    def check_tables(self, table_names: list) -> list:
        """
        check if tables exist in the project database
        :param table_names: the list of tables checked
        :return: the list of tables that not exist in the database.
        """
        missing_tables = []
        self.connect()
        for table_name in table_names:
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            result = self.db_cursor.execute(query).fetchone()
            if not result:
                missing_tables.append(table_name)
        self.close_connection()
        return missing_tables

    def return_tables(self) -> list:
        """
        return a list of tables exist inside the database
        :return: list of tables inside the database
        """
        self.connect()
        result = self.db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        existing_tables = [row[0] for row in result]
        self.close_connection()
        return existing_tables

    def delete_table(self, table_name: str) -> None:
        """
        delete a table in the database
        :param table_name:
        :return: None
        """
        choice = input(
            f"Do you want to delete {table_name} from the existing project? (Yes/No) ").strip().lower()
        if choice == 'yes':
            self.connect()
            try:
                query = f"DROP TABLE {table_name}"
                self.db_cursor.execute(query)
                self.db_conn.commit()
                print(f"Table '{table_name}' deleted successfully.")
            except sqlite3.Error as e:
                print(f"Error deleting table: {e}. (table may not exist in database)")
            finally:
                self.close_connection()
        else:
            print(f"{table_name} not deleted")

    def check_data(self, table_name, required_rows):
        query = f"SELECT COUNT(*) FROM {table_name}"
        self.db_cursor.execute(query)
        rows_count = self.db_cursor.fetchone()[0]
        if rows_count < required_rows:
            return False
        return True

    def remind_to_add_data(self, table_name, required_rows):
        print(f"Reminder: Table '{table_name}' has insufficient data. Please add at least {required_rows} rows.")

    def close_connection(self):
        self.db_conn.close()


def get_project_database() -> Project:
    """
    Connect to a project (project database)
    :return: a Project class
    """
    print("Welcome to the Project Manager!")
    while True:
        choice = input("Do you want to create(c) a new project or connect(n) to an existing project? ").strip().lower()
        if choice in ['c', 'n']:
            return connect_project(choice)
        else:
            print("Invalid choice. Please enter 'c'(create) or 'n'(connect).")


def check_if_database_exit(db_file: str) -> bool:
    """
    Check if database exist
    :param db_file: url to database file
    :return: if database exit, return True, else return False.
    """
    return os.path.exists(db_file)


def connect_project(option: str) -> Project:
    """
    create or connect to an Icarus project
    :param option: str, if it's "c", means the user wanted to create a new project.
                        If it's "n" means connect to existing project.
    :return: an Icarus Project object
    """
    while True:
        if option == 'c':
            project_location = input("Enter the new project location URL and name: ")
            if not check_if_database_exit(project_location):
                break
            else:
                print('WARNING: the project already exist! Please provide a new project name')

        else:
            project_location = input("Enter the existing project location URL and name: ")
            if check_if_database_exit(project_location):
                break
            else:
                print('WARNING: the project not exist! Please provide an existing project name to connect')

    db_url = f"{project_location}"  # Assume the database file will be named 'data.db'
    project = Project(db_url)

    # Create tables, add data, etc. based on your project's requirements

    project.close_connection()
    return project
