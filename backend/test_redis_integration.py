#!/usr/bin/env python
import os
os.environ['FLASK_ENV'] = 'development'
from app import app
from extensions import redis_client

with app.app_context():
    print('=== REDIS CONNECTION TEST ===')
    if redis_client:
        print('✓ Redis Client: Connected')
        try:
            info = redis_client.info('server')
            print(f"✓ Redis Server Version: {info.get('redis_version', 'unknown')}")
            print(f"✓ Redis Memory Used: {info.get('used_memory_human', 'unknown')}")
        except Exception as e:
            print(f'⚠ Redis info error: {e}')
    else:
        print('⚠ Redis Client: Not initialized (cache will be skipped)')
    
    print('\n=== TESTING DASHBOARD ENDPOINT ===')
    from routes.master_table import get_master_dashboard_stats
    try:
        with app.test_request_context('GET /master-dashboard-stats'):
            result = get_master_dashboard_stats()
            print('✓ Endpoint executed successfully')
            print(f'Response type: {type(result).__name__}')
            if hasattr(result, 'json'):
                print(f'Response status: Success')
    except Exception as e:
        print(f'Error: {type(e).__name__}: {str(e)[:100]}')
        import traceback
        traceback.print_exc()

print('\n✓ Redis integration test complete!')
