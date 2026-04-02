from .bpf_tracked_container import BpfTrackedContainer
from multiprocessing import Queue
from threading import Lock

class BpfTrackedContainersRegistry:
    def __init__(self):
        self.containers: dict[int, BpfTrackedContainer] = {}
        self.lock = Lock()

    def add_container(self, namespace_id: int, container: BpfTrackedContainer) -> bool:
        """Adds a new container with a specific namespace id.  
        Does nothing if the namespace id is already present."""

        with self.lock:
            # don't re-add the same container
            if namespace_id in self.containers:
                return False

            self.containers[namespace_id] = container

        return True

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
        """Get the Queue for the container with the specific namespace id.  
        Does nothing if the namespace id does not exist."""

        with self.lock:
            if namespace_id in self.containers:
                return self.containers[namespace_id].queue

        return None

    def get_pod_container_id(self, pod_name) -> str | None:
        """Get the container id running in a specific pod if it exists.  
        Gets the first one if multiple containers exist per pod.
        """
        with self.lock:
            for c in self.containers.values():
                if c.pod_name == pod_name:
                    return c.container_id

        return None

    def tracks_pod(self, pod_name: str) -> bool:
        """Returns a boolean indicating if a specific pod is tracked by this registry."""
        return self.get_pod_container_id(pod_name) != None
