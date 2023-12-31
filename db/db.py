import os
import sqlite3

import directory


class DBConn:
    def __init__(self):
        path = directory.get_path(True, "/db")
        exists = os.path.exists(path)
        if not exists:
            os.mkdir(path)

        file = path + "/scripts.sqlite"
        exists = os.path.exists(file)

        self.conn = sqlite3.connect(file)
        self.cursor = self.conn.cursor()

        self.cursor.execute("PRAGMA FOREIGN_KEYS = ON")
        if not exists:
            self.cursor.execute("""CREATE TABLE IP (
            ID      integer
                primary key autoincrement,
            Address TEXT not null
                unique
            );""")
            self.cursor.execute("""CREATE TABLE Script (
            ID   integer
                primary key autoincrement,
            Name TEXT not null
                unique, 
            Timeout REAL default 10.00, 
            Message TEXT not null);""")
            self.cursor.execute("""CREATE TABLE IPsInScript (
            ScriptID integer not null
                constraint IPsInScript_Script_ID_fk
                    references Script
                    on update cascade on delete cascade,
            IPID     integer not null
                constraint IPsInScript_IP_ID_fk
                    references IP
                    on update cascade on delete cascade,
            constraint IPsInScript_pk
                primary key (ScriptID, IPID));""")

        self.conn.commit()

    def select_all_ips(self):
        cursor_res = self.cursor.execute("SELECT Address FROM IP")
        return [r[0] for r in cursor_res.fetchall()]

    def insert_ip(self, address):
        return self.try_insert("INSERT INTO IP (Address) VALUES (?)", (address,))

    def try_insert(self, query, args):
        try:
            self.cursor.execute(query, args)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_ips(self, addresses):
        self.cursor.execute(f"DELETE FROM IP WHERE Address IN ({','.join('?'*len(addresses))})", addresses)
        self.conn.commit()

    def select_all_scripts(self):
        cursor_res = self.cursor.execute("SELECT Name FROM Script")
        return [r[0] for r in cursor_res.fetchall()]

    def select_script(self, name):
        cursor_res = self.cursor.execute("SELECT Name, Message, Timeout FROM Script WHERE Name = ?", (name,))
        script_fields = cursor_res.fetchone()

        if not script_fields:
            return None

        cursor_res = self.cursor.execute("""
        SELECT Address FROM IP 
        JOIN IPsInScript IPIS on ip.ID = IPIS.IPID 
        JOIN Script S on IPIS.ScriptID = S.ID 
        WHERE S.Name = ?""", (name,))

        return script_fields + ([r[0] for r in cursor_res.fetchall()],)

    def insert_script(self, name, message, timeout):
        return self.try_insert("INSERT INTO Script (Name, Message, Timeout) VALUES (?, ?, ?)", (name, message, timeout))

    def update_script(self, name, message, timeout):
        self.cursor.execute("UPDATE Script SET Message = ?, Timeout = ? WHERE Name = ?", (message, timeout, name))
        self.conn.commit()

    def delete_script(self, name):
        self.cursor.execute("DELETE FROM Script WHERE Name = ?", (name,))
        self.conn.commit()

    def insert_IPs_to_script(self, name, addresses):

        self.cursor.execute(f"""
        INSERT INTO IPsInScript (ScriptID, IPID) 
        SELECT (
            SELECT ID as SID FROM Script WHERE Name = ?
        ), ID as IID 
        FROM IP WHERE Address IN ({','.join('?'*len(addresses))})""", [name] + addresses)
        self.conn.commit()

    def remove_IPs_from_script(self, name, addresses):
        self.cursor.execute(f"""
        DELETE FROM IPsInScript 
        WHERE ScriptID = (SELECT ID FROM Script WHERE Name = ?) 
        AND IPID IN (SELECT ID FROM IP WHERE Address IN ({','.join('?'*len(addresses))}))
        """, [name] + addresses)
        self.conn.commit()
