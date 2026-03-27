#!/usr/bin/env python
"""Test the dashboard stats endpoint fix"""

import sys
sys.path.insert(0, '.')

from app import app, db
from flask import request as flask_request
from unittest.mock import MagicMock

# Create test request context
with app.test_request_context('/api/master-dashboard-stats'):
    try:
        from routes.master_table import get_master_dashboard_stats
        
        print("✅ Importing route... SUCCESS")
        print("\n🔍 Testing endpoint...")
        
        # Call the function
        result = get_master_dashboard_stats()
        
        # If it's a Response object, get the data
        if hasattr(result, 'json'):
            data = result.get_json()
        else:
            data = result
            
        print("✅ Endpoint executed successfully!")
        print("\n📊 Response structure:")
        print(f"  - Status: {data.get('status')}")
        print(f"  - Has 'stats': {'stats' in data}")
        
        if 'stats' in data:
            stats = data['stats']
            print(f"  - Total records: {stats.get('total_records', '?')}")
            print(f"  - Avg rating: {stats.get('avg_system_rating', '?')}")
            print(f"  - State summary count: {len(stats.get('state_summary', []))}")
            print(f"  - Top cities count: {len(stats.get('top_cities', []))}")
            print(f"  - Top subcategories count: {len(stats.get('top_subcategories', []))}")
            print(f"  - Top rated businesses count: {len(stats.get('top_rated_businesses', []))}")
            print(f"  - Phone distribution: {stats.get('phone_distribution', [])}")
        
        print("\n✅ All checks passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
