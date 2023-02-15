# TODO there's got to be a package that can do this for us rather than us maintaining this
# TODO this needs to use redis in the future so it supports multi-process

# A simple class to rate limit api requests using the leaky bucket algorithm.
import math
import time
from contextlib import contextmanager
from threading import Lock
from typing import Dict

from python.utils.logging import log


class MultiBucketLimiter:
    def __init__(self, max_resources_per_minute: Dict[str, float]):
        self.max_resources_per_minute = max_resources_per_minute
        self.resources = max_resources_per_minute.keys()

        # A dict of resource name and the number of consumed but not cleared
        # resources. (requests, tokens, etc...)
        self.resources_count = {}
        for resource in self.resources:
            self.resources_count[resource] = 0

        self.last_clear_time = None
        self.lock = Lock()

    def clear_leaked(self):
        # Using the leaky bucket analogy, remove any resources that have been
        # cleared since time passed.
        if self.last_clear_time is None:
            self.last_clear_time = time.time()
            return

        minutes_since_last_clear = math.floor((time.time() - self.last_clear_time) / 60)

        for resource in self.resources:
            remove_tokens = minutes_since_last_clear * self.max_resources_per_minute[resource]
            self.resources_count[resource] = max(0, self.resources_count[resource] - remove_tokens)

    def consume_resources(self, request_resources: Dict[str, int]):
        for resource in self.resources:
            self.resources_count[resource] += request_resources[resource]

    @contextmanager
    def request_when_available(self, request_resources: Dict[str, int], consume_resources: bool = True):
        for resource in self.resources:
            if request_resources[resource] >= self.max_resources_per_minute[resource]:
                raise ValueError(
                    f"Requested {request_resources[resource]} {resource} but max is {self.max_resources_per_minute[resource]}"
                )

        # Takes in the number of resource units (can be more than one if we're
        # limiting LLM tokens or something.
        #
        # Uses a Lock (mutex) to enfoce a synchronus api
        #
        # returns the number of seconds until we can make the next request
        with self.lock:
            if consume_resources:
                self.consume_resources(request_resources)

            self.clear_leaked()

            # How many seconds until resources_count goes below max_resources_per_minute
            seconds_until_next_request = 0.0
            for resource in self.resources:
                remaining_time = (
                    max(0.0, (float(self.resources_count[resource]) - self.max_resources_per_minute[resource]))
                    / self.max_resources_per_minute[resource]
                ) * 60.0

                # Take the max on the remaining seconds until the next request
                seconds_until_next_request = max(seconds_until_next_request, remaining_time)

            # Sleep until the next token is available
            if seconds_until_next_request > 0:
                log.warn("waiting for token window", seconds=seconds_until_next_request)
                time.sleep(seconds_until_next_request)

            # Yield to the block, giving it a chance to consume the resouces
            # while locked in the mutex (by calling consume_resources)
            yield

        return seconds_until_next_request
