# app/analyzer.py
import logging
import json
from typing import List, Dict, Any, Optional
import time

class CarAnalyzer:
    """Analyzer for car listings using LLM capabilities."""
    
    def __init__(self, database, llm_service):
        """
        Initialize car analyzer.
        
        Args:
            database: Database instance for data access
            llm_service: LLM service for analysis
        """
        self.db = database
        self.llm_service = llm_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_recommendations(self, criteria_str: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get car recommendations based on search criteria.
        
        Args:
            criteria_str: JSON string with search criteria
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended cars with analysis
        """
        # Parse criteria
        criteria = {}
        if criteria_str:
            try:
                criteria = json.loads(criteria_str)
            except json.JSONDecodeError:
                self.logger.error("Invalid JSON criteria provided")
        
        # Get cars from database matching criteria
        cars = self.db.get_cars(criteria, limit=50)  # Get more cars than needed for analysis
        
        if not cars:
            self.logger.warning("No cars found matching criteria")
            return []
        
        # Analyze cars that don't have analysis yet
        self._analyze_cars(cars, criteria)
        
        # Rank cars based on analysis
        ranked_cars = self._rank_cars(cars, criteria)
        
        # Return top recommendations
        return ranked_cars[:limit]
    
    def _analyze_cars(self, cars: List[Dict[str, Any]], preferences: Dict[str, Any]) -> None:
        """
        Analyze individual cars without existing analysis.
        
        Args:
            cars: List of car dictionaries
            preferences: User preferences for analysis
        """
        for car in cars:
            # Skip cars that already have analysis
            if car.get('analysis'):
                continue
            
            try:
                # Get analysis from LLM
                analysis = self.llm_service.analyze_car(car, preferences)
                
                # Update car in database with analysis
                self.db.update_car_analysis(car['id'], analysis)
                
                # Update in-memory object
                car['analysis'] = analysis
                
                # Sleep briefly to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error analyzing car {car.get('id')}: {str(e)}")
    
    def _rank_cars(self, cars: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank cars based on LLM analysis.
        
        Args:
            cars: List of car dictionaries with analysis
            preferences: User preferences for ranking
            
        Returns:
            Ranked list of cars
        """
        try:
            # Get cars with analysis
            analyzed_cars = [car for car in cars if car.get('analysis')]
            
            if len(analyzed_cars) <= 1:
                # No need to rank if there's only one car
                return analyzed_cars
            
            # If there are more than 10 cars, use LLM to help rank them
            if len(analyzed_cars) > 10:
                # Get ranking from LLM
                ranking_text = self.llm_service.rank_cars(analyzed_cars[:30], preferences)
                
                # Extract car IDs from ranking text using simple heuristics
                # This is a simplified approach - in a real application, you'd use more robust parsing
                ranked_cars = []
                
                for car in analyzed_cars:
                    # Calculate a score for each car based on mentions in ranking
                    car_identifier = f"{car.get('year')} {car.get('make')} {car.get('model')}"
                    
                    # Check how prominently the car is mentioned in the ranking
                    # Higher score for earlier mentions
                    score = 0
                    if car_identifier in ranking_text:
                        # Position in text (earlier is better)
                        position = ranking_text.find(car_identifier)
                        score -= position / 1000
                        
                        # Positive sentiment words near the car mention
                        positive_words = ['recommend', 'excellent', 'good', 'best', 'top', 'value']
                        for word in positive_words:
                            if word in ranking_text[position:position+200]:
                                score += 10
                        
                        # Negative sentiment words near the car mention
                        negative_words = ['avoid', 'poor', 'worst', 'concern', 'issue', 'problem']
                        for word in negative_words:
                            if word in ranking_text[position:position+200]:
                                score -= 10
                    
                    car['rank_score'] = score
                
                # Sort cars by rank score
                ranked_cars = sorted(analyzed_cars, key=lambda x: x.get('rank_score', 0), reverse=True)
                return ranked_cars
            else:
                # For a small number of cars, we can use a simple ranking based on price
                # In a real application, you'd use more sophisticated ranking logic
                return sorted(analyzed_cars, key=lambda x: x.get('price', float('inf')))
                
        except Exception as e:
            self.logger.error(f"Error ranking cars: {str(e)}")
            # Fall back to sorting by price if ranking fails
            return sorted(cars, key=lambda x: x.get('price', float('inf')))