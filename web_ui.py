# app/web_ui.py
import os
from flask import Flask, render_template, request, jsonify
import json
import logging
from typing import Dict, Any, List

class WebUI:
    """Web user interface for the car recommendation application."""
    
    def __init__(self, config, database, analyzer):
        """
        Initialize web UI.
        
        Args:
            config: Application configuration
            database: Database instance
            analyzer: Car analyzer instance
        """
        self.config = config
        self.db = database
        self.analyzer = analyzer
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize Flask application
        self.app = Flask(
            __name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static')
        )
        
        # Set up routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up Flask application routes."""
        
        @self.app.route('/')
        def index():
            """Render main page."""
            return render_template('index.html')
        
        @self.app.route('/api/search', methods=['POST'])
        def search():
            """API endpoint for searching cars."""
            try:
                criteria = request.json or {}
                cars = self.db.get_cars(criteria, limit=50)
                
                # Format results for display
                results = []
                for car in cars:
                    car_dict = dict(car)
                    if 'details' in car_dict and isinstance(car_dict['details'], str):
                        try:
                            car_dict['details'] = json.loads(car_dict['details'])
                        except json.JSONDecodeError:
                            car_dict['details'] = {}
                    results.append(car_dict)
                
                return jsonify({
                    'success': True,
                    'cars': results
                })
            except Exception as e:
                self.logger.error(f"Error in search API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/analyze', methods=['POST'])
        def analyze():
            """API endpoint for analyzing cars."""
            try:
                criteria = request.json or {}
                recommendations = self.analyzer.get_recommendations(json.dumps(criteria))
                
                return jsonify({
                    'success': True,
                    'recommendations': recommendations
                })
            except Exception as e:
                self.logger.error(f"Error in analyze API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/car/<int:car_id>')
        def get_car(car_id):
            """API endpoint for getting a specific car."""
            try:
                car = self.db.get_car_by_id(car_id)
                if not car:
                    return jsonify({
                        'success': False,
                        'error': 'Car not found'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'car': car
                })
            except Exception as e:
                self.logger.error(f"Error in get_car API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/scrape', methods=['POST'])
        def scrape():
            """API endpoint for triggering a scrape operation."""
            try:
                # This would typically be a background task
                return jsonify({
                    'success': False,
                    'error': 'Scraping through the web UI is not implemented yet'
                }), 501
            except Exception as e:
                self.logger.error(f"Error in scrape API: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def run(self):
        """Run the web server."""
        host = self.config.web_ui_host
        port = self.config.web_ui_port
        
        self.logger.info(f"Starting web UI on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False)