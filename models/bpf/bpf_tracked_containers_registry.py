from models import BpfTrackedContainer
from threading import Lock
from queue import Queue

class BpfTrackedContainersRegistry:
    def __init__(self):
        self.containers: dict[int, BpfTrackedContainer] = {}
        self.lock = Lock()

    def add_container(self, namespace_id: int, container: BpfTrackedContainer):
        """Adds a new container with a specific namespace id.  
        Does nothing if the namespace id is already present."""

        with self.lock:
            # don't re-add the same container
            if namespace_id in self.containers:
                return

            self.containers[namespace_id] = container

    def remove_container(self, container_id: str) -> int | None:
        """Removes a container with a specific container id.  
        Does nothing if no container with the id is not found."""

        namespace_id = None
        with self.lock:
            for c_ns_id, c in self.containers.items():
                if c.container_id == container_id:
                    namespace_id = c_ns_id
                    break

            if namespace_id == None:
                return None

            self.containers[namespace_id].stop()
            del self.containers[namespace_id]

        return namespace_id

    def get_container_queue(self, namespace_id: int) -> Queue[tuple[int, int]] | None:
        """"Get the Queue for the container with the specific namespace id.  
        Does nothing if the namespace id does not exist."""

        with self.lock:
            if namespace_id in self.containers:
                return self.containers[namespace_id].queue

        return None
