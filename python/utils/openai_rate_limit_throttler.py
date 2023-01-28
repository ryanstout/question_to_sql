# Handles keeping parallel requests to OpenAI under the request and token
# limits.
from pyrate_limiter import BucketFullException, Duration, Limiter, RequestRate


class OpenAIRateLimitThrottler:
    def __init__(self, request_limit: int, token_limit: int, max_requests_per_minute: float, max_tokens_per_minute: float, max_attempts: int = 5):
        self.request_limit = request_limit
        self.token_limit = token_limit
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self.max_attempts = max_attempts
        self.request_limiter = Limiter(RequestRate(max_requests_per_minute, Duration.MINUTE))
        self.token_limiter = Limiter(RequestRate(max_tokens_per_minute, Duration.MINUTE))
        self.request_limit

    def throttle(self, token_count: int):
        # Synchronusly block until we are under the rate limits
        pass

        # We're now under, count this request and return
