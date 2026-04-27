import atexit
import multiprocessing as mp
from queue import Full

class LoggerWithBuffer:

    def __init__(self, log_file_path: str, buffer_size: int = 256):
        self.log_file_path = log_file_path
        self.buffer: list = [None] * buffer_size
        self.buffer_size = buffer_size
        self.buffer_index = 0
        self.fileIo = open(log_file_path, 'a')

    def log(self, message: str):
        self.buffer[self.buffer_index] = message
        self.buffer_index += 1
        if self.buffer_index >= self.buffer_size:
            self.fileIo.writelines(self.buffer)
            self.buffer_index = 0

    def close(self):
        if self.buffer_index > 0:
            self.fileIo.writelines(self.buffer[:self.buffer_index])
        self.fileIo.flush()
        self.fileIo.close()

class LoggerProcess:

    def __init__(self, log_file_path: str, process_name: str = 'bknet_LoggerProcess', maxsize: int = 1024):
        self.log_queue: mp.Queue[str] = mp.Queue(maxsize=maxsize)
        self.logger_process = mp.Process(
            target=self._logger_process, 
            name=process_name, 
            args=(log_file_path,), 
            daemon=True
        )
        self.logger_process.start()
        
        atexit.register(self.close)

    def log(self, message: str):
        try:
            self.log_queue.put(message, block=False)
        except Full:
            print("Warning: Log queue is full. Log message dropped.")

    def close(self):
        if self.logger_process.is_alive():
            self.log_queue.put(None) # type: ignore
            self.logger_process.join(timeout=5) 

    def _logger_process(self, log_file_path: str):
        with open(log_file_path, 'a') as log_file:
            while True:
                msg = self.log_queue.get()
                if msg is None: # signal to terminate
                    break
                log_file.write(f'{msg}\n')
            log_file.flush()
