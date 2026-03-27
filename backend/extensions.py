from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_migrate import Migrate
import redis

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
mail = Mail()
migrate = Migrate()

# Redis client for caching
redis_client = None

def init_redis(app):
    """Initialize Redis client from config with retry logic"""
    global redis_client
    import os
    import time
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/2")
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            redis_client = redis.from_url(
                redis_url, 
                decode_responses=True, 
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            redis_client.ping()
            app.logger.info(f"✓ Redis connected: {redis_url} (attempt {attempt + 1})")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                app.logger.warning(f"⚠ Redis connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
            else:
                app.logger.warning(f"⚠ Redis unavailable. Cache disabled. URL: {redis_url}")
                redis_client = None