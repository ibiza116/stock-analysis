"""
Database management module for portfolio management features.
Provides SQLite database operations with automatic backup functionality.
"""

import sqlite3
import json
import shutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

class DatabaseManager:
    """Manages SQLite database operations for portfolio management."""
    
    def __init__(self, db_path: str = "data/database/analysis.db"):
        """Initialize database manager with specified database path."""
        self.db_path = db_path
        self.backup_dir = "data/database/backups"
        
        # Setup logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self._ensure_directories()
        self._init_database()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _init_database(self):
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Portfolio table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    company_name TEXT,
                    shares INTEGER DEFAULT 0,
                    average_price REAL DEFAULT 0.0,
                    current_price REAL DEFAULT 0.0,
                    total_investment REAL DEFAULT 0.0,
                    current_value REAL DEFAULT 0.0,
                    profit_loss REAL DEFAULT 0.0,
                    profit_loss_pct REAL DEFAULT 0.0,
                    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Watchlist table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL UNIQUE,
                    company_name TEXT,
                    target_price REAL,
                    alert_enabled BOOLEAN DEFAULT 0,
                    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Analysis history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analysis_data TEXT,
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Investment notes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investment_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    note_type TEXT DEFAULT 'general',
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_archived BOOLEAN DEFAULT 0
                )
            ''')
            
            # Backtest history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    initial_capital REAL,
                    final_value REAL,
                    total_return_pct REAL,
                    total_trades INTEGER,
                    win_rate REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    strategy_params TEXT,
                    performance_metrics TEXT,
                    trades_data TEXT,
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Comparison list table for multi-stock analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparison_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL UNIQUE,
                    company_name TEXT,
                    category TEXT DEFAULT 'general',
                    priority INTEGER DEFAULT 0,
                    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_analyzed DATETIME,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def backup_database(self) -> str:
        """Create a backup of the database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"analysis_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backup created: {backup_path}")
            
            # Clean old backups (keep last 10)
            self._cleanup_old_backups()
            
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("analysis_backup_") and file.endswith(".db"):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getctime(file_path)))
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for file_path, _ in backup_files[keep_count:]:
                os.remove(file_path)
                self.logger.info(f"Removed old backup: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
    
    # Portfolio operations
    def add_to_portfolio(self, ticker: str, company_name: str = "", shares: int = 0, 
                        average_price: float = 0.0, notes: str = "") -> int:
        """Add or update portfolio entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if ticker already exists
            cursor.execute("SELECT id FROM portfolio WHERE ticker = ? AND is_active = 1", (ticker,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing entry
                cursor.execute('''
                    UPDATE portfolio 
                    SET shares = shares + ?, 
                        total_investment = total_investment + ?,
                        average_price = (total_investment + ?) / (shares + ?),
                        last_updated = CURRENT_TIMESTAMP,
                        notes = COALESCE(NULLIF(?, ''), notes)
                    WHERE id = ?
                ''', (shares, shares * average_price, shares * average_price, shares, notes, existing[0]))
                return existing[0]
            else:
                # Insert new entry
                cursor.execute('''
                    INSERT INTO portfolio (ticker, company_name, shares, average_price, 
                                         total_investment, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ticker, company_name, shares, average_price, shares * average_price, notes))
                return cursor.lastrowid
    
    def update_portfolio_prices(self, price_updates: Dict[str, float]):
        """Update current prices for portfolio items."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for ticker, current_price in price_updates.items():
                cursor.execute('''
                    UPDATE portfolio 
                    SET current_price = ?,
                        current_value = shares * ?,
                        profit_loss = (shares * ?) - total_investment,
                        profit_loss_pct = CASE 
                            WHEN total_investment > 0 
                            THEN ((shares * ?) - total_investment) / total_investment * 100
                            ELSE 0 
                        END,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE ticker = ? AND is_active = 1
                ''', (current_price, current_price, current_price, current_price, ticker))
    
    def get_portfolio(self) -> List[Dict[str, Any]]:
        """Get all active portfolio entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM portfolio 
                WHERE is_active = 1 
                ORDER BY last_updated DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def remove_from_portfolio(self, portfolio_id: int):
        """Remove (deactivate) portfolio entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE portfolio SET is_active = 0 WHERE id = ?", (portfolio_id,))
    
    # Watchlist operations
    def add_to_watchlist(self, ticker: str, company_name: str = "", target_price: float = None,
                        alert_enabled: bool = False, notes: str = "") -> int:
        """Add ticker to watchlist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO watchlist 
                (ticker, company_name, target_price, alert_enabled, notes, date_added)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (ticker, company_name, target_price, alert_enabled, notes))
            
            return cursor.lastrowid
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get all active watchlist entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM watchlist 
                WHERE is_active = 1 
                ORDER BY date_added DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def remove_from_watchlist(self, watchlist_id: int):
        """Remove (deactivate) watchlist entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE watchlist SET is_active = 0 WHERE id = ?", (watchlist_id,))

    
    # Comparison list operations
    def add_to_comparison_list(self, ticker: str, company_name: str = "", category: str = 'general',
                              priority: int = 0, notes: str = "") -> int:
        """Add ticker to comparison list."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO comparison_list 
                (ticker, company_name, category, priority, notes, date_added)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (ticker, company_name, category, priority, notes))
            
            return cursor.lastrowid
    
    def get_comparison_list(self, category: str = None) -> List[Dict[str, Any]]:
        """Get all active comparison list entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM comparison_list WHERE is_active = 1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY priority DESC, date_added DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_comparison_item(self, comparison_id: int, **kwargs):
        """Update comparison list item."""
        if not kwargs:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for field, value in kwargs.items():
                if field in ['company_name', 'category', 'priority', 'notes']:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if set_clauses:
                query = f"UPDATE comparison_list SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(comparison_id)
                cursor.execute(query, params)
    
    def remove_from_comparison_list(self, comparison_id: int):
        """Remove (deactivate) comparison list entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE comparison_list SET is_active = 0 WHERE id = ?", (comparison_id,))
    
    def update_last_analyzed(self, ticker: str):
        """Update last analyzed timestamp for comparison item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE comparison_list 
                SET last_analyzed = CURRENT_TIMESTAMP 
                WHERE ticker = ? AND is_active = 1
            ''', (ticker,))
    
    # Analysis history operations
    def save_analysis_result(self, ticker: str, analysis_type: str, analysis_data: Dict[str, Any],
                           metadata: Dict[str, Any] = None) -> int:
        """Save analysis result to history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_history (ticker, analysis_type, analysis_data, metadata)
                VALUES (?, ?, ?, ?)
            ''', (ticker, analysis_type, json.dumps(analysis_data, default=str), 
                  json.dumps(metadata or {}, default=str)))
            
            return cursor.lastrowid
    
    def get_analysis_history(self, ticker: str = None, analysis_type: str = None, 
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Get analysis history with optional filters."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM analysis_history"
            params = []
            conditions = []
            
            if ticker:
                conditions.append("ticker = ?")
                params.append(ticker)
            
            if analysis_type:
                conditions.append("analysis_type = ?")
                params.append(analysis_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY date_created DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                try:
                    result['analysis_data'] = json.loads(result['analysis_data'])
                    result['metadata'] = json.loads(result['metadata'] or '{}')
                except json.JSONDecodeError:
                    pass
                results.append(result)
            
            return results
    
    # Investment notes operations
    def add_investment_note(self, ticker: str, title: str, content: str, 
                          note_type: str = 'general') -> int:
        """Add investment note."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO investment_notes (ticker, title, content, note_type)
                VALUES (?, ?, ?, ?)
            ''', (ticker, title, content, note_type))
            
            return cursor.lastrowid
    
    def update_investment_note(self, note_id: int, title: str, content: str):
        """Update investment note."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE investment_notes 
                SET title = ?, content = ?, date_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (title, content, note_id))
    
    def get_investment_notes(self, ticker: str = None, note_type: str = None) -> List[Dict[str, Any]]:
        """Get investment notes with optional filters."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM investment_notes WHERE is_archived = 0"
            params = []
            
            if ticker:
                query += " AND ticker = ?"
                params.append(ticker)
            
            if note_type:
                query += " AND note_type = ?"
                params.append(note_type)
            
            query += " ORDER BY date_updated DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def archive_investment_note(self, note_id: int):
        """Archive investment note."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE investment_notes SET is_archived = 1 WHERE id = ?", (note_id,))
    
    # Backtest history operations
    def save_backtest_result(self, ticker: str, strategy_name: str, start_date: str, 
                           end_date: str, initial_capital: float, performance_metrics: Dict[str, Any],
                           trades_data: List[Dict[str, Any]], strategy_params: Dict[str, Any]) -> int:
        """Save backtest result to history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            basic_stats = performance_metrics.get('basic_stats', {})
            
            cursor.execute('''
                INSERT INTO backtest_history 
                (ticker, strategy_name, start_date, end_date, initial_capital, 
                 final_value, total_return_pct, total_trades, win_rate, sharpe_ratio, 
                 max_drawdown, strategy_params, performance_metrics, trades_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticker, strategy_name, start_date, end_date, initial_capital,
                basic_stats.get('final_value', 0),
                basic_stats.get('total_return_pct', 0),
                basic_stats.get('total_trades', 0),
                basic_stats.get('win_rate', 0),
                performance_metrics.get('risk_metrics', {}).get('sharpe_ratio', 0),
                performance_metrics.get('risk_metrics', {}).get('max_drawdown_pct', 0),
                json.dumps(strategy_params, default=str),
                json.dumps(performance_metrics, default=str),
                json.dumps(trades_data, default=str)
            ))
            
            return cursor.lastrowid
    
    def get_backtest_history(self, ticker: str = None, strategy_name: str = None, 
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Get backtest history with optional filters."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM backtest_history"
            params = []
            conditions = []
            
            if ticker:
                conditions.append("ticker = ?")
                params.append(ticker)
            
            if strategy_name:
                conditions.append("strategy_name = ?")
                params.append(strategy_name)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY date_created DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                try:
                    result['strategy_params'] = json.loads(result['strategy_params'] or '{}')
                    result['performance_metrics'] = json.loads(result['performance_metrics'] or '{}')
                    result['trades_data'] = json.loads(result['trades_data'] or '[]')
                except json.JSONDecodeError:
                    pass
                results.append(result)
            
            return results
    
    # Utility methods
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary statistics."""
        portfolio = self.get_portfolio()
        
        if not portfolio:
            return {
                'total_stocks': 0,
                'total_investment': 0.0,
                'current_value': 0.0,
                'total_profit_loss': 0.0,
                'total_profit_loss_pct': 0.0
            }
        
        total_investment = sum(item['total_investment'] or 0 for item in portfolio)
        current_value = sum(item['current_value'] or 0 for item in portfolio)
        total_profit_loss = current_value - total_investment
        total_profit_loss_pct = (total_profit_loss / total_investment * 100) if total_investment > 0 else 0
        
        return {
            'total_stocks': len(portfolio),
            'total_investment': total_investment,
            'current_value': current_value,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_pct': total_profit_loss_pct
        }
    
    def cleanup_old_data(self, days: int = 365):
        """Clean up old data older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clean old analysis history
            cursor.execute(
                "DELETE FROM analysis_history WHERE date_created < ?",
                (cutoff_date,)
            )
            
            # Clean old backtest history (keep longer)
            old_backtest_cutoff = datetime.now() - timedelta(days=days * 2)
            cursor.execute(
                "DELETE FROM backtest_history WHERE date_created < ?",
                (old_backtest_cutoff,)
            )
            
            conn.commit()
            self.logger.info(f"Cleaned up data older than {days} days")

# Global database instance
db_manager = DatabaseManager()