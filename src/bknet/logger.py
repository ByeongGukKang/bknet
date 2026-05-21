import atexit
import queue
import threading


class LoggerWithBuffer:
    def __init__(self, log_file_path: str, buffer_size: int = 256):
        self.log_file_path = log_file_path
        self.buffer: list = [None] * buffer_size
        self.buffer_size = buffer_size
        self.buffer_index = 0
        self.fileIo = open(log_file_path, "a")

    def log(self, message: str):
        self.buffer[self.buffer_index] = message
        self.buffer_index += 1
        if self.buffer_index >= self.buffer_size:
            self.fileIo.writelines(self.buffer)
            self.buffer_index = 0

    def close(self):
        if self.buffer_index > 0:
            self.fileIo.writelines(self.buffer[: self.buffer_index])
        self.fileIo.flush()
        self.fileIo.close()


class LoggerThread:
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
            target=self._logger_thread,
            name=thread_name,
            args=(log_file_path,),
            daemon=True,
        )
        self.logger_thread.start()

        atexit.register(self.close)

    def log(self, message: str):
        if self.use_print:
            print(message)
        try:
            self.log_queue.put_nowait(message)
        except queue.Full:
            pass

    def close(self):
        if self.logger_thread.is_alive():
            try:
                self.log_queue.put(None, timeout=1.0)
            except queue.Full:
                pass
            self.logger_thread.join(timeout=5.0)

    def _logger_thread(self, log_file_path: str):
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
