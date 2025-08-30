"""
Portfolio management REST API endpoints.
Provides CRUD operations for portfolio, watchlist, notes, and analysis history.
"""

from flask import Blueprint, jsonify, request
from utils.database import db_manager
from analyzers.data_fetcher import StockDataFetcher
import logging
import os
from datetime import datetime
from typing import Dict, Any

# Create blueprint
portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

# Setup logging
logger = logging.getLogger(__name__)

# Auth will be handled by the main app's auth decorator

def _safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def _safe_int(value, default=0):
    """Safely convert value to int."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

# Portfolio endpoints
@portfolio_bp.route('/portfolio', methods=['GET'])
# @auth.login_required  # Will be handled by app.py
def get_portfolio():
    """Get all portfolio entries with current prices."""
    try:
        portfolio = db_manager.get_portfolio()
        
        # Update current prices if portfolio is not empty
        if portfolio:
            fetcher = StockDataFetcher()
            price_updates = {}
            
            for item in portfolio:
                try:
                    ticker = item['ticker']
                    if not ticker.endswith('.T'):
                        ticker += '.T'
                    
                    stock_data = fetcher.fetch_stock_data(ticker, '1d')
                    current_price = stock_data.get('current_price', 0)
                    if current_price > 0:
                        price_updates[item['ticker']] = current_price
                except Exception as e:
                    logger.warning(f"Failed to fetch price for {item['ticker']}: {e}")
            
            # Update prices in database
            if price_updates:
                db_manager.update_portfolio_prices(price_updates)
                # Refresh portfolio data
                portfolio = db_manager.get_portfolio()
        
        # Get portfolio summary
        summary = db_manager.get_portfolio_summary()
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio': portfolio,
                'summary': summary
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/portfolio', methods=['POST'])
# @auth.login_required  # Will be handled by app.py
def add_to_portfolio():
    """Add or update portfolio entry."""
    try:
        data = request.json
        ticker = data.get('ticker', '').upper()
        company_name = data.get('company_name', '')
        shares = _safe_int(data.get('shares', 0))
        average_price = _safe_float(data.get('average_price', 0.0))
        notes = data.get('notes', '')
        
        if not ticker:
            return jsonify({
                'success': False,
                'error': 'Ticker is required'
            }), 400
        
        # Remove .T suffix if present for storage
        clean_ticker = ticker.replace('.T', '')
        
        # Fetch company name if not provided
        if not company_name:
            try:
                fetcher = StockDataFetcher()
                stock_data = fetcher.fetch_stock_data(ticker if ticker.endswith('.T') else ticker + '.T', '1d')
                company_name = stock_data.get('company_name', ticker)
            except Exception as e:
                logger.warning(f"Failed to fetch company name for {ticker}: {e}")
                company_name = ticker
        
        portfolio_id = db_manager.add_to_portfolio(
            ticker=clean_ticker,
            company_name=company_name,
            shares=shares,
            average_price=average_price,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'data': {'portfolio_id': portfolio_id}
        })
        
    except Exception as e:
        logger.error(f"Error adding to portfolio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/portfolio/<int:portfolio_id>', methods=['DELETE'])
# @auth.login_required  # Will be handled by app.py
def remove_from_portfolio(portfolio_id):
    """Remove portfolio entry."""
    try:
        db_manager.remove_from_portfolio(portfolio_id)
        
        return jsonify({
            'success': True,
            'message': 'Portfolio entry removed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error removing from portfolio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Watchlist endpoints
@portfolio_bp.route('/watchlist', methods=['GET'])
# @auth.login_required  # Will be handled by app.py
def get_watchlist():
    """Get all watchlist entries."""
    try:
        watchlist = db_manager.get_watchlist()
        
        return jsonify({
            'success': True,
            'data': watchlist
        })
        
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/watchlist', methods=['POST'])
# @auth.login_required  # Will be handled by app.py
def add_to_watchlist():
    """Add ticker to watchlist."""
    try:
        data = request.json
        ticker = data.get('ticker', '').upper()
        company_name = data.get('company_name', '')
        target_price = _safe_float(data.get('target_price'))
        alert_enabled = data.get('alert_enabled', False)
        notes = data.get('notes', '')
        
        if not ticker:
            return jsonify({
                'success': False,
                'error': 'Ticker is required'
            }), 400
        
        # Remove .T suffix if present for storage
        clean_ticker = ticker.replace('.T', '')
        
        # Fetch company name if not provided
        if not company_name:
            try:
                fetcher = StockDataFetcher()
                stock_data = fetcher.fetch_stock_data(ticker if ticker.endswith('.T') else ticker + '.T', '1d')
                company_name = stock_data.get('company_name', ticker)
            except Exception as e:
                logger.warning(f"Failed to fetch company name for {ticker}: {e}")
                company_name = ticker
        
        watchlist_id = db_manager.add_to_watchlist(
            ticker=clean_ticker,
            company_name=company_name,
            target_price=target_price if target_price > 0 else None,
            alert_enabled=alert_enabled,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'data': {'watchlist_id': watchlist_id}
        })
        
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/watchlist/<int:watchlist_id>', methods=['DELETE'])
# @auth.login_required  # Will be handled by app.py
def remove_from_watchlist(watchlist_id):
    """Remove watchlist entry."""
    try:
        db_manager.remove_from_watchlist(watchlist_id)
        
        return jsonify({
            'success': True,
            'message': 'Watchlist entry removed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Investment notes endpoints
@portfolio_bp.route('/notes', methods=['GET'])
# @auth.login_required  # Will be handled by app.py
def get_investment_notes():
    """Get investment notes with optional filters."""
    try:
        ticker = request.args.get('ticker')
        note_type = request.args.get('note_type')
        
        notes = db_manager.get_investment_notes(ticker=ticker, note_type=note_type)
        
        return jsonify({
            'success': True,
            'data': notes
        })
        
    except Exception as e:
        logger.error(f"Error getting investment notes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/notes', methods=['POST'])
# @auth.login_required  # Will be handled by app.py
def add_investment_note():
    """Add investment note."""
    try:
        data = request.json
        ticker = data.get('ticker', '').upper().replace('.T', '')
        title = data.get('title', '')
        content = data.get('content', '')
        note_type = data.get('note_type', 'general')
        
        if not ticker or not title:
            return jsonify({
                'success': False,
                'error': 'Ticker and title are required'
            }), 400
        
        note_id = db_manager.add_investment_note(
            ticker=ticker,
            title=title,
            content=content,
            note_type=note_type
        )
        
        return jsonify({
            'success': True,
            'data': {'note_id': note_id}
        })
        
    except Exception as e:
        logger.error(f"Error adding investment note: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/notes/<int:note_id>', methods=['PUT'])
# @auth.login_required  # Will be handled by app.py
def update_investment_note(note_id):
    """Update investment note."""
    try:
        data = request.json
        title = data.get('title', '')
        content = data.get('content', '')
        
        if not title:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        db_manager.update_investment_note(note_id, title, content)
        
        return jsonify({
            'success': True,
            'message': 'Note updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating investment note: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/notes/<int:note_id>', methods=['DELETE'])
# @auth.login_required  # Will be handled by app.py
def archive_investment_note(note_id):
    """Archive investment note."""
    try:
        db_manager.archive_investment_note(note_id)
        
        return jsonify({
            'success': True,
            'message': 'Note archived successfully'
        })
        
    except Exception as e:
        logger.error(f"Error archiving investment note: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Analysis history endpoints
@portfolio_bp.route('/analysis-history', methods=['GET'])
# @auth.login_required  # Will be handled by app.py
def get_analysis_history():
    """Get analysis history with optional filters."""
    try:
        ticker = request.args.get('ticker')
        analysis_type = request.args.get('analysis_type')
        limit = _safe_int(request.args.get('limit', 50))
        
        history = db_manager.get_analysis_history(
            ticker=ticker,
            analysis_type=analysis_type,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Backtest history endpoints
@portfolio_bp.route('/backtest-history', methods=['GET'])
# @auth.login_required  # Will be handled by app.py
def get_backtest_history():
    """Get backtest history with optional filters."""
    try:
        ticker = request.args.get('ticker')
        strategy_name = request.args.get('strategy_name')
        limit = _safe_int(request.args.get('limit', 50))
        
        history = db_manager.get_backtest_history(
            ticker=ticker,
            strategy_name=strategy_name,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        logger.error(f"Error getting backtest history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Utility endpoints
@portfolio_bp.route('/summary', methods=['GET'])
# @auth.login_required  # Will be handled by app.py
def get_portfolio_summary():
    """Get portfolio summary statistics."""
    try:
        summary = db_manager.get_portfolio_summary()
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/backup', methods=['POST'])
# @auth.login_required  # Will be handled by app.py
def create_backup():
    """Create database backup."""
    try:
        backup_path = db_manager.backup_database()
        
        return jsonify({
            'success': True,
            'data': {'backup_path': backup_path}
        })
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/cleanup', methods=['POST'])
# @auth.login_required  # Will be handled by app.py
def cleanup_old_data():
    """Clean up old data."""
    try:
        days = _safe_int(request.json.get('days', 365))
        db_manager.cleanup_old_data(days)
        
        return jsonify({
            'success': True,
            'message': f'Data older than {days} days cleaned up'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Auto-save analysis result endpoint
@portfolio_bp.route('/save-analysis', methods=['POST'])
# @auth.login_required  # Will be handled by app.py
def save_analysis_result():
    """Save analysis result to history."""
    try:
        data = request.json
        ticker = data.get('ticker', '').upper().replace('.T', '')
        analysis_type = data.get('analysis_type', '')
        analysis_data = data.get('analysis_data', {})
        metadata = data.get('metadata', {})
        
        if not ticker or not analysis_type:
            return jsonify({
                'success': False,
                'error': 'Ticker and analysis_type are required'
            }), 400
        
        analysis_id = db_manager.save_analysis_result(
            ticker=ticker,
            analysis_type=analysis_type,
            analysis_data=analysis_data,
            metadata=metadata
        )
        
        return jsonify({
            'success': True,
            'data': {'analysis_id': analysis_id}
        })
        
    except Exception as e:
        logger.error(f"Error saving analysis result: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Auto-save backtest result endpoint
@portfolio_bp.route('/save-backtest', methods=['POST'])
# @auth.login_required  # Will be handled by app.py
def save_backtest_result():
    """Save backtest result to history."""
    try:
        data = request.json
        ticker = data.get('ticker', '').upper().replace('.T', '')
        strategy_name = data.get('strategy_name', '')
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        initial_capital = _safe_float(data.get('initial_capital', 0))
        performance_metrics = data.get('performance_metrics', {})
        trades_data = data.get('trades_data', [])
        strategy_params = data.get('strategy_params', {})
        
        if not ticker or not strategy_name:
            return jsonify({
                'success': False,
                'error': 'Ticker and strategy_name are required'
            }), 400
        
        backtest_id = db_manager.save_backtest_result(
            ticker=ticker,
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            performance_metrics=performance_metrics,
            trades_data=trades_data,
            strategy_params=strategy_params
        )
        
        return jsonify({
            'success': True,
            'data': {'backtest_id': backtest_id}
        })
        
    except Exception as e:
        logger.error(f"Error saving backtest result: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500