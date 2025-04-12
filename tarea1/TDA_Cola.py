
from Exceptions import OwnEmpty
class ArrayQueue:
    """FIFO queue implementation using a Python list as underlying storage."""
    DEFAULT_CAPACITY = 10  # moderate capacity for all new queues

    def __init__(self):
        """Create an empty queue."""
        self.data = [None] * ArrayQueue.DEFAULT_CAPACITY
        self.size = 0
        self.front = 0

    def __len__(self):
        """Return the number of elements in the queue."""
        return self.size

    def is_empty(self):
        """Return True if the queue is empty."""
        return self.size == 0

    def first(self):
        """Return (but do not remove) the element at the front of the queue.
        
        Raise Empty exception if the queue is empty.
        """
        if self.is_empty():
            raise OwnEmpty("Queue is empty")
        return self.data[self.front]

    def dequeue(self):
        """Remove and return the first element of the queue (i.e., FIFO).
        
        Raise Empty exception if the queue is empty.
        """
        if self.is_empty():
            raise OwnEmpty("Queue is empty")
        answer = self.data[self.front]
        self.data[self.front] = None  # help garbage collection
        self.front = (self.front + 1) % len(self.data)
        self.size -= 1
        return answer
    
    def enqueue(self, e):
        """Add an element to the back of the queue."""
        if self.size == len(self.data):
            self.resize(2 * len(self.data))  # double the array size
        avail = (self.front + self.size) % len(self.data)
        self.data[avail] = e
        self.size += 1

    def resize(self, cap):  # we assume cap >= len(self)
        """Resize to a new list of capacity >= len(self)."""
        old = self.data  # keep track of existing list
        self.data = [None] * cap  # allocate list with new capacity
        walk = self.front
        for k in range(self.size):  # only consider existing elements
            self.data[k] = old[walk]  # intentionally shift indices
            walk = (1 + walk) % len(old)  # use old size as modulus
        self.front = 0