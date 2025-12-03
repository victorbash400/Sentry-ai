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
            print("⚠ Perplexity SDK not installed. Run: pip install perplexity-python")
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
        
        Args:
            crop_type: Type of crop (e.g., "Maize", "Coffee")
            risk_factors: List of risk factors (e.g., ["Drought", "Pests"])
            region: Geographic region
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results and citations
        """
        if not self.client:
            return self._mock_search_results(crop_type, risk_factors, region)
        
        # Build search query
        risk_terms = ", ".join(risk_factors)
        query = f"{crop_type} farming {risk_terms} risks {region} 2024 latest updates"
        
        try:
            print(f"  Searching: {query}")
            
            search = self.client.search.create(
                query=query,
                max_results=max_results,
                max_tokens_per_page=1024
            )
            
            # Transform results
            results = []
            for result in search.results:
                results.append({
                    'title': result.title,
                    'url': result.url,
                    'snippet': result.snippet[:300] + "..." if len(result.snippet) > 300 else result.snippet,
                    'date': getattr(result, 'date', None),
                    'last_updated': getattr(result, 'last_updated', None)
                })
            
            print(f"  ✓ Found {len(results)} results")
            
            return {
                'query': query,
                'results': results,
                'id': getattr(search, 'id', None)
            }
            
        except Exception as e:
            print(f"  ✗ Search failed: {e}")
            return self._mock_search_results(crop_type, risk_factors, region)
    
    def _mock_search_results(self, crop_type: str, risk_factors: List[str], region: str) -> Dict:
        """Fallback mock results when API is unavailable"""
        return {
            'query': f"{crop_type} farming {', '.join(risk_factors)} risks {region}",
            'results': [
                {
                    'title': f'{crop_type} Farming Best Practices in {region}',
                    'url': 'https://example.com/agriculture',
                    'snippet': f'Latest guidelines for {crop_type.lower()} cultivation addressing {risk_factors[0].lower()} challenges...',
                    'date': '2024-11-15',
                    'last_updated': '2024-12-01'
                },
                {
                    'title': f'Climate Resilience for {crop_type} Crops',
                    'url': 'https://example.com/climate',
                    'snippet': f'Strategies to mitigate {risk_factors[0].lower()} impact on {crop_type.lower()} yields...',
                    'date': '2024-10-20',
                    'last_updated': '2024-11-28'
                }
            ],
            'id': 'mock-search-id'
        }


# Singleton instance
_perplexity_instance = None

def get_perplexity_instance() -> PerplexitySearch:
    """Get or create Perplexity search instance"""
    global _perplexity_instance
    if _perplexity_instance is None:
        _perplexity_instance = PerplexitySearch()
    return _perplexity_instance
