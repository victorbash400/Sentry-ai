"""
Perplexity AI Search Service
Provides real-time web search for agricultural intelligence
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PerplexitySearch:
    """Wrapper for Perplexity AI search API"""
    
    def __init__(self):
        """Initialize Perplexity client"""
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        # Remove quotes if present
        self.api_key = self.api_key.strip('"').strip("'")
        
        try:
            from perplexity import Perplexity
            self.client = Perplexity(api_key=self.api_key)
            print(f"✓ Perplexity AI initialized")
        except ImportError:
            print("⚠ Perplexity SDK not installed. Run: pip install perplexityai")
            self.client = None
        except Exception as e:
            print(f"✗ Failed to initialize Perplexity: {e}")
            self.client = None
    
    def search_agricultural_intelligence(
        self, 
        crop_type: str, 
        risk_factors: List[str],
        region: str = "Kenya",
        max_results: int = 5
    ) -> Dict:
        """
        Search for agricultural intelligence related to crop and risks
        """
        if not self.client:
            return self._mock_search_results(crop_type, risk_factors, region)
        
        # Build search query
        # Build search query - Focus on climatic forecast and general risks for the area
        # risk_terms = ", ".join(risk_factors)        # Build specific query for the region
        query = f"current climatic forecast {region} drought predictions crop yield outlook weather extremes 2025"
        
        try:
            print(f"  Searching: {query}")
            
            if not self.client:
                raise ValueError("Perplexity client is not initialized")
                
            # Use Perplexity client with correct search method
            response = self.client.search.create(
                query=query,
                max_results=5,
                max_tokens_per_page=1024
            )
            
            results = []
            for result in response.results:
                results.append({
                    'title': result.title,
                    'url': result.url,
                    'snippet': result.snippet,
                    'date': getattr(result, 'date', ''),
                    'last_updated': getattr(result, 'last_updated', '')
                })
            
            print(f"  ✓ Search successful: {len(results)} results")
            
            return {
                'query': query,
                'results': results,
                'id': getattr(response, 'id', 'unknown')
            }
            
        except Exception as e:
            import traceback
            print(f"  ✗ CRITICAL SEARCH ERROR: {str(e)}")
            print(f"  ✗ Traceback: {traceback.format_exc()}")
            # Return empty results with error, NO MOCKS
            return {
                'query': query,
                'results': [],
                'error': str(e)
            }


# Singleton instance
_perplexity_instance = None

def get_perplexity_instance() -> PerplexitySearch:
    """Get or create Perplexity search instance"""
    global _perplexity_instance
    if _perplexity_instance is None:
        _perplexity_instance = PerplexitySearch()
    return _perplexity_instance
