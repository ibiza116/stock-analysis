#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import cgitb
cgitb.enable()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment for production
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'qnap-stock-analysis-production-key-2025'

from app import app

def application(environ, start_response):
    """WSGI application callable for Web Server deployment"""
    return app.wsgi_app(environ, start_response)

if __name__ == '__main__':
    # CGI mode
    print("Content-Type: text/html\n")
    
    # Import and run Flask app
    try:
        from wsgiref.handlers import CGIHandler
        CGIHandler().run(app)
    except Exception as e:
        print(f"<h1>Application Error</h1><p>{str(e)}</p>")