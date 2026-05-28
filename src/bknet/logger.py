import atexit
import queue
import sqlite3
import threading
from typing import Literal, Union


class Logger:
    def log(self, msg: str):
        pass


class LoggerWithBuffer(Logger):
    def __init__(self, log_file_path: str, buffer_size: int = 256):
        self.log_file_path = log_file_path
        self.buffer: list = [None] * buffer_size
        self.buffer_size = buffer_size
        self.buffer_index = 0
        self.fileIo = open(log_file_path, "a")

    def log(self, msg: str):
        self.buffer[self.buffer_index] = msg
        self.buffer_index += 1
        if self.buffer_index >= self.buffer_size:
            self.fileIo.writelines(self.buffer)
            self.buffer_index = 0

    def close(self):
        if self.buffer_index > 0:
            self.fileIo.writelines(self.buffer[: self.buffer_index])
        self.fileIo.flush()
        self.fileIo.close()


class LoggerThread(Logger):
    def __init__(
        self,
        log_file_path: str,
        thread_name: str = "bknet_LoggerThread",
        maxsize: int = 2048,
        use_print: bool = False,
    ):
        self.use_print = use_print
        self.log_queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self.logger_thread = threading.Thread(
            target=self._run,
            name=thread_name,
            args=(log_file_path,),
            daemon=True,
        )
        self.logger_thread.start()

        atexit.register(self.close)

    def log(self, msg: str):
        if self.use_print:
            print(msg)
        try:
            self.log_queue.put_nowait(msg)
        except queue.Full:
            pass

    def close(self):
        if self.logger_thread.is_alive():
            try:
                self.log_queue.put(None, timeout=1.0)
            except queue.Full:
                pass
            self.logger_thread.join(timeout=5.0)

    def _run(self, log_file_path: str):
        with open(log_file_path, "a", buffering=1, encoding="utf-8") as log_file:
            while True:
                try:
                    msg = self.log_queue.get()

                    if msg is None:  # signal to terminate
                        break

                    log_file.write(f"{msg}\n")

                    while (
                        not self.log_queue.empty()
                    ):  # bulk write remaining messages to minimize disk I/O
                        msg = self.log_queue.get_nowait()
                        if msg is None:
                            return  # terminate immediately if termination signal is received
                        log_file.write(f"{msg}\n")

                except queue.Empty:
                    continue
                except Exception:
                    break
            log_file.flush()


class SQLiteTradeLogger:
    def __init__(
        self,
        db_path: str,
        table_name: str,
        sys_logger: Logger,
        thread_name: str = "bknet_SQLiteLoggerThread",
        maxsize: int = 1024,
    ):
        self.db_path = db_path
        self.table_name = table_name
        self.log_queue: queue.Queue = queue.Queue(maxsize=maxsize)

        # system logger
        self.sys_logger = sys_logger

        # background thread for DB logging
        self.logger_thread = threading.Thread(
            target=self._run,
            name=thread_name,
            daemon=True,
        )
        self.logger_thread.start()

        # safe shutdown on exit
        atexit.register(self.close)

    def log(
        self,
        timestamp: str,
        symbol: str,
        side: Literal["B", "S", "A", "C"],
        exeqty: Union[int, float],
        exeprc: Union[int, float],
        prcnow: float,
    ):
        """Log a trade execution"""
        try:
            self.log_queue.put_nowait((timestamp, symbol, side, exeqty, exeprc, prcnow))
        except queue.Full:
            pass

    def close(self):
        """스레드 안전하게 종료 및 잔여 데이터 처리"""
        if self.logger_thread.is_alive():
            try:
                self.log_queue.put(None, timeout=1.0)
            except queue.Full:
                pass
            self.logger_thread.join(timeout=5.0)

    def _init_db(self, conn: sqlite3.Connection):
        """Init DB schema and performance optimizations"""
        cursor = conn.cursor()

        # activate WAL mode
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

        # create table if not exists
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                exeqty REAL NOT NULL,
                exeprc REAL NOT NULL,
                prcnow REAL NOT NULL
            )
        """)

        # create indexes
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_timestamp ON {self.table_name} (timestamp DESC);"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_symbol_time ON {self.table_name} (symbol, timestamp DESC);"
        )
        conn.commit()

    def _run(self):
        conn = sqlite3.connect(self.db_path)
        self._init_db(conn)

        cursor = conn.cursor()
        insert_query = f"""
            INSERT INTO {self.table_name} (timestamp, symbol, side, exeqty, exeprc, prcnow)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        while True:
            try:
                msg = self.log_queue.get()
                if msg is None:
                    break

                # for bulk insert
                batch = [msg]

                terminate_loop = False
                while not self.log_queue.empty():
                    next_msg = self.log_queue.get_nowait()
                    if next_msg is None:
                        terminate_loop = True
                        break
                    batch.append(next_msg)

                try:
                    cursor.executemany(insert_query, batch)
                    conn.commit()
                except sqlite3.Error as e:
                    self.sys_logger.log(f"SQLite[{self.table_name}] error: {e}")
                    conn.rollback()

                if terminate_loop:
                    break

            except queue.Empty:
                continue
            except Exception as e:
                self.sys_logger.log(
                    f"Unexpected error in SQLite[{self.table_name}] logger thread: {e}"
                )
                break

        conn.commit()
        conn.close()
