from django.core.cache import cache
from django.http import HttpResponse
from functools import wraps


RATE_LIMIT_MESSAGE = "Too many requests. Please try again later."


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def get_rate_limit_identity(request, key_type="user_or_ip"):
    if key_type == "ip":
        return get_client_ip(request)
    if key_type == "user":
        if request.user.is_authenticated:
            return f"user:{request.user.pk}"
        return "anonymous"
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    return f"ip:{get_client_ip(request)}"


def parse_rate(rate):
    amount, window = rate.split("/")
    amount = int(amount)
    seconds = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }[window]
    return amount, seconds


def rate_limit_response(retry_after):
    response = HttpResponse(RATE_LIMIT_MESSAGE, status=429)
    response["Retry-After"] = str(retry_after)
    return response


def check_rate_limit(request, *, scope, rate, key_type="user_or_ip"):
    limit, window = parse_rate(rate)
    identity = get_rate_limit_identity(request, key_type=key_type)
    cache_key = f"ratelimit:{scope}:{identity}"
    added = cache.add(cache_key, 1, timeout=window)

    if added:
        return None

    try:
        current_count = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=window)
        return None

    if current_count > limit:
        return rate_limit_response(window)

    return None


class RateLimitMixin:
    rate_limit = None
    rate_limit_scope = None
    rate_limit_key = "user_or_ip"
    rate_limit_methods = None

    def dispatch(self, request, *args, **kwargs):
        methods = self.rate_limit_methods or {"GET", "POST"}
        if (
            self.rate_limit
            and self.rate_limit_scope
            and request.method.upper() in methods
        ):
            limited_response = check_rate_limit(
                request,
                scope=self.rate_limit_scope,
                rate=self.rate_limit,
                key_type=self.rate_limit_key,
            )
            if limited_response:
                return limited_response

        return super().dispatch(request, *args, **kwargs)


def rate_limit(*, scope, rate, key_type="user_or_ip", methods=None):
    allowed_methods = {method.upper() for method in (methods or {"GET", "POST"})}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if hasattr(args[0], "method"):
                request = args[0]
            else:
                request = args[1]

            if request.method.upper() in allowed_methods:
                limited_response = check_rate_limit(
                    request,
                    scope=scope,
                    rate=rate,
                    key_type=key_type,
                )
                if limited_response:
                    return limited_response
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
