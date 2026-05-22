import numpy as np


class BkArr:
    idx_curr: int
    idx_next: int
    maxsize: int
    arr: np.ndarray
    isfull: bool

    def __init__(self, base_arr):
        self.idx_next = 0
        self.maxsize = base_arr.shape[0]
        self.arr = base_arr
        self.isfull = False

    def get(self):
        return self.arr[self.idx_curr]

    def update(self, val):
        self.idx_curr = self.idx_next
        self.arr[self.idx_next] = val
        self.idx_next += 1
        if self.idx_next == self.maxsize:
            self.idx_next = 0
            self.isfull = True

    def median(self, method="r"):
        """Return the median of the array.

        Args:
            method (str, optional): "r" for right median or "l" for left median. Defaults to "r".
        """
        n = self.maxsize
        mid = n // 2
        particion = np.partition(self.arr, mid)
        return particion[mid] if method == "r" else particion[mid - 1]
