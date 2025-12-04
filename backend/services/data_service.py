import hashlib
from datetime import date

class DataService:
    """
    Service to provide deterministic auxiliary data for insurance analysis.
    Uses location and date to seed generation, ensuring consistency.
    """
    
    def _get_deterministic_seed(self, lat: float, lon: float, date_val: date) -> int:
        """Generate a deterministic seed from location and date."""
        # Create a string unique to this location and month/year
        # We use month/year so data doesn't fluctuate wildly day-to-day
        key = f"{lat:.4f}_{lon:.4f}_{date_val.year}_{date_val.month}"
        # Hash it to get a seed
        return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)

    def get_context_data(self, lat: float, lon: float, agri_risk_score: float):
        """
        Get auxiliary data (weather, market, etc.) for a specific location.
        In a real system, this would call external APIs.
        Here, we generate realistic, deterministic values.
        """
        seed = self._get_deterministic_seed(lat, lon, date.today())
        import numpy as np
        rng = np.random.RandomState(seed)
        
        # 1. Weather Volatility
        # Higher in certain lat/lon bands (simplified)
        base_volatility = 0.3
        if abs(lat) < 20: # Tropics
            base_volatility += 0.2
        
        weather_volatility = base_volatility + rng.normal(0, 0.1)
        weather_volatility = np.clip(weather_volatility, 0.1, 0.9)
        
        # 2. Market Stability
        # Independent of location, more time-based (but fixed for the month via seed)
        market_stability = 0.5 + rng.normal(0, 0.15)
        market_stability = np.clip(market_stability, 0.2, 0.9)
        
        # 3. Soil Quality
        # Correlated with agri_risk (inverse) but with local variation
        base_soil = 1.0 - (agri_risk_score / 100.0)
        soil_quality = base_soil + rng.normal(0, 0.1)
        soil_quality = np.clip(soil_quality, 0.1, 0.95)
        
        # 4. Claims History
        # Higher risk -> higher claims
        claims_history = (agri_risk_score / 100.0) * 0.8 + rng.normal(0, 0.05)
        claims_history = np.clip(claims_history, 0.0, 1.0)
        
        # 5. Yield Stability
        yield_stability = 1.0 - weather_volatility * 0.6 + rng.normal(0, 0.05)
        yield_stability = np.clip(yield_stability, 0.1, 0.95)
        
        return {
            "weather_volatility": float(round(weather_volatility, 2)),
            "market_stability": float(round(market_stability, 2)),
            "soil_quality": float(round(soil_quality, 2)),
            "claims_history_index": float(round(claims_history, 2)),
            "yield_stability": float(round(yield_stability, 2))
        }

_instance = None

def get_data_service():
    global _instance
    if _instance is None:
        _instance = DataService()
    return _instance
