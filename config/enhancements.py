"""
Enhanced Configuration Module for Flask Apps
Adds: Redis caching, compression, rate limiting, Prometheus metrics, Sentry
"""

import os
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


def setup_redis_cache(app):
    """Setup Redis caching for Flask app"""
    try:
        from flask_caching import Cache

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        cache_config = {
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_URL": redis_url,
            "CACHE_DEFAULT_TIMEOUT": 300,
            "CACHE_KEY_PREFIX": "upstox_",
        }

        cache = Cache(app, config=cache_config)
        logger.info(f"✓ Redis caching enabled: {redis_url}")
        return cache

    except ImportError:
        logger.warning("flask-caching not installed, using simple cache")
        from flask_caching import Cache

        cache = Cache(app, config={"CACHE_TYPE": "simple"})
        return cache
    except Exception as e:
        logger.error(f"Failed to setup Redis cache: {e}, using simple cache")
        from flask_caching import Cache

        cache = Cache(app, config={"CACHE_TYPE": "simple"})
        return cache


def setup_compression(app):
    """Enable gzip compression for responses"""
    try:
        from flask_compress import Compress

        Compress(app)
        logger.info("✓ Response compression enabled")
    except ImportError:
        logger.warning("flask-compress not installed, skipping compression")
    except Exception as e:
        logger.error(f"Failed to setup compression: {e}")


def setup_rate_limiting(app):
    """Setup API rate limiting"""
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=redis_url,
            default_limits=["200 per day", "50 per hour"],
            storage_options={"socket_connect_timeout": 30},
            strategy="fixed-window",
        )

        logger.info("✓ Rate limiting enabled")
        return limiter

    except ImportError:
        logger.warning("flask-limiter not installed, skipping rate limiting")
        return None
    except Exception as e:
        logger.error(f"Failed to setup rate limiting: {e}")
        return None


def setup_prometheus_metrics(app):
    """Setup Prometheus metrics endpoint"""
    try:
        from prometheus_client import (
            Counter,
            Histogram,
            Gauge,
            generate_latest,
            CONTENT_TYPE_LATEST,
        )
        from flask import Response
        import time

        # Define metrics
        request_count = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )

        request_latency = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
        )

        active_requests = Gauge(
            "http_requests_in_progress", "Active HTTP requests", ["method", "endpoint"]
        )

        # Middleware to track metrics
        @app.before_request
        def before_request():
            request._start_time = time.time()
            if hasattr(request, "endpoint") and request.endpoint:
                active_requests.labels(
                    method=request.method, endpoint=request.endpoint
                ).inc()

        @app.after_request
        def after_request(response):
            if hasattr(request, "_start_time"):
                latency = time.time() - request._start_time

                endpoint = request.endpoint or "unknown"
                request_latency.labels(
                    method=request.method, endpoint=endpoint
                ).observe(latency)

                request_count.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=response.status_code,
                ).inc()

                active_requests.labels(method=request.method, endpoint=endpoint).dec()

            return response

        # Metrics endpoint
        @app.route("/metrics")
        def metrics():
            """Prometheus metrics endpoint"""
            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

        logger.info("✓ Prometheus metrics enabled at /metrics")

    except ImportError:
        logger.warning("prometheus-client not installed, skipping metrics")
    except Exception as e:
        logger.error(f"Failed to setup Prometheus metrics: {e}")


def setup_sentry(app):
    """Setup Sentry error tracking"""
    try:
        sentry_dsn = os.getenv("SENTRY_DSN")

        if not sentry_dsn:
            logger.info("SENTRY_DSN not set, skipping Sentry integration")
            return

        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,  # Sample 10% of transactions
            environment=os.getenv("FLASK_ENV", "production"),
            release=os.getenv("APP_VERSION", "1.0.0"),
        )

        logger.info("✓ Sentry error tracking enabled")

    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry")
    except Exception as e:
        logger.error(f"Failed to setup Sentry: {e}")


def setup_csrf_protection(app):
    """Setup CSRF protection for forms"""
    try:
        from flask_wtf.csrf import CSRFProtect

        app.config["SECRET_KEY"] = os.getenv(
            "SECRET_KEY", "dev-secret-key-change-in-production"
        )
        csrf = CSRFProtect(app)

        logger.info("✓ CSRF protection enabled")
        return csrf

    except ImportError:
        logger.warning("flask-wtf not installed, skipping CSRF protection")
        return None
    except Exception as e:
        logger.error(f"Failed to setup CSRF protection: {e}")
        return None


def require_api_key(f):
    """Decorator to require API key for protected endpoints"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        expected_key = os.getenv("API_KEY")

        if not expected_key:
            # If no API key is configured, allow access
            return f(*args, **kwargs)

        if not api_key or api_key != expected_key:
            return (
                jsonify(
                    {
                        "error": "Invalid or missing API key",
                        "message": "Please provide a valid X-API-Key header",
                    }
                ),
                401,
            )

        return f(*args, **kwargs)

    return decorated_function


def setup_all_enhancements(app):
    """
    Setup all enhancements at once
    Returns: dict with all initialized components
    """
    logger.info("=" * 60)
    logger.info("Setting up application enhancements...")
    logger.info("=" * 60)

    components = {
        "cache": setup_redis_cache(app),
        "limiter": setup_rate_limiting(app),
        "csrf": setup_csrf_protection(app),
    }

    setup_compression(app)
    setup_prometheus_metrics(app)
    setup_sentry(app)

    logger.info("=" * 60)
    logger.info("✅ Application enhancements setup complete")
    logger.info("=" * 60)

    return components
