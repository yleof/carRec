# app/database.py
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os

class Database:
    """Database manager for car listings storage and retrieval."""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create cars table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                year INTEGER,
                make TEXT,
                model TEXT,
                price INTEGER,
                url TEXT,
                details TEXT,
                scraped_at TIMESTAMP,
                analysis TEXT,
                analysis_timestamp TIMESTAMP
            )
            ''')
            
            # Create search_criteria table to store historical searches
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_criteria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criteria TEXT NOT NULL,
                created_at TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def add_cars(self, cars: List[Dict[str, Any]]) -> int:
        """
        Add multiple car listings to the database.
        
        Args:
            cars: List of car dictionaries
            
        Returns:
            Number of cars added
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            added_count = 0
            for car in cars:
                # Convert details dict to JSON string
                if 'details' in car and isinstance(car['details'], dict):
                    car['details'] = json.dumps(car['details'])
                
                # Check if this car already exists in the database
                cursor.execute('''
                SELECT id FROM cars 
                WHERE source = ? AND year = ? AND make = ? AND model = ? AND url = ?
                ''', (
                    car.get('source', ''),
                    car.get('year', None),
                    car.get('make', ''),
                    car.get('model', ''),
                    car.get('url', '')
                ))
                
                existing = cursor.fetchone()
                if existing:
                    # Update existing record
                    cursor.execute('''
                    UPDATE cars SET
                        price = ?,
                        details = ?,
                        scraped_at = ?
                    WHERE id = ?
                    ''', (
                        car.get('price', None),
                        car.get('details', '{}'),
                        car.get('scraped_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        existing[0]
                    ))
                else:
                    # Insert new record
                    cursor.execute('''
                    INSERT INTO cars (
                        source, year, make, model, price, url, details, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        car.get('source', ''),
                        car.get('year', None),
                        car.get('make', ''),
                        car.get('model', ''),
                        car.get('price', None),
                        car.get('url', ''),
                        car.get('details', '{}'),
                        car.get('scraped_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    ))
                    added_count += 1
            
            conn.commit()
            conn.close()
            return added_count
            
        except sqlite3.Error as e:
            self.logger.error(f"Error adding cars to database: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return 0
    
    def get_cars(self, criteria: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get car listings from the database, optionally filtered by criteria.
        
        Args:
            criteria: Dictionary of search criteria
            limit: Maximum number of results to return
            
        Returns:
            List of car dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This enables column access by name
            cursor = conn.cursor()
            
            query = "SELECT * FROM cars"
            params = []
            
            # Build WHERE clause from criteria
            if criteria:
                where_clauses = []
                
                if 'make' in criteria:
                    where_clauses.append("make LIKE ?")
                    params.append(f"%{criteria['make']}%")
                
                if 'model' in criteria:
                    where_clauses.append("model LIKE ?")
                    params.append(f"%{criteria['model']}%")
                
                if 'min_year' in criteria:
                    where_clauses.append("year >= ?")
                    params.append(criteria['min_year'])
                
                if 'max_year' in criteria:
                    where_clauses.append("year <= ?")
                    params.append(criteria['max_year'])
                
                if 'max_price' in criteria:
                    where_clauses.append("price <= ?")
                    params.append(criteria['max_price'])
                
                if 'min_price' in criteria:
                    where_clauses.append("price >= ?")
                    params.append(criteria['min_price'])
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            # Add order and limit
            query += " ORDER BY scraped_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            cars = []
            for row in rows:
                car = dict(row)
                
                # Parse JSON details
                if 'details' in car and car['details']:
                    try:
                        car['details'] = json.loads(car['details'])
                    except json.JSONDecodeError:
                        car['details'] = {}
                
                cars.append(car)
            
            conn.close()
            return cars
            
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving cars from database: {str(e)}")
            if conn:
                conn.close()
            return []
    
    def update_car_analysis(self, car_id: int, analysis: str) -> bool:
        """
        Update the LLM analysis for a specific car.
        
        Args:
            car_id: Database ID of the car
            analysis: Analysis text from LLM
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE cars SET
                analysis = ?,
                analysis_timestamp = ?
            WHERE id = ?
            ''', (
                analysis,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                car_id
            ))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            self.logger.error(f"Error updating car analysis: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def save_search_criteria(self, criteria: Dict[str, Any]) -> int:
        """
        Save search criteria for future reference.
        
        Args:
            criteria: Search criteria dictionary
            
        Returns:
            ID of the saved criteria
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO search_criteria (criteria, created_at)
            VALUES (?, ?)
            ''', (
                json.dumps(criteria),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            last_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return last_id
            
        except sqlite3.Error as e:
            self.logger.error(f"Error saving search criteria: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return -1
    
    def get_car_by_id(self, car_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific car by its database ID.
        
        Args:
            car_id: Database ID of the car
            
        Returns:
            Car dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM cars WHERE id = ?", (car_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            car = dict(row)
            
            # Parse JSON details
            if 'details' in car and car['details']:
                try:
                    car['details'] = json.loads(car['details'])
                except json.JSONDecodeError:
                    car['details'] = {}
            
            conn.close()
            return car
            
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving car by ID: {str(e)}")
            if conn:
                conn.close()
            return None