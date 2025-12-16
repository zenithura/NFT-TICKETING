"""Multi-Armed Bandit (MAB) for Dynamic Pricing and A/B Testing."""
import numpy as np
import random
from typing import Dict, List, Optional
from datetime import datetime
import json
from data_control.db_connection import get_redis_client


class MultiArmedBandit:
    """
    Epsilon-greedy Multi-Armed Bandit for traffic routing.
    
    Arms:
    - baseline: Fixed pricing
    - surge_pricing: Demand-based surge pricing
    - early_bird: Early-bird discount strategy
    - ml_pricing: ML-predicted optimal pricing
    """
    
    def __init__(self, epsilon: float = 0.15):
        """
        Initialize MAB.
        
        Args:
            epsilon: Exploration rate (0.0 = pure exploitation, 1.0 = pure exploration)
        """
        self.epsilon = epsilon
        self.arms = {
            'baseline': {'count': 0, 'rewards': [], 'avg_reward': 0.0, 'weight': 1.0},
            'surge_pricing': {'count': 0, 'rewards': [], 'avg_reward': 0.0, 'weight': 1.0},
            'early_bird': {'count': 0, 'rewards': [], 'avg_reward': 0.0, 'weight': 1.0},
            'ml_pricing': {'count': 0, 'rewards': [], 'avg_reward': 0.0, 'weight': 1.0}
        }
        self.redis_client = get_redis_client()
    
    def _load_from_redis(self):
        """Load MAB state from Redis."""
        if not self.redis_client:
            return
        
        try:
            for arm_name in self.arms.keys():
                key = f"mab:{arm_name}"
                data = self.redis_client.get(key)
                if data:
                    arm_data = json.loads(data)
                    self.arms[arm_name].update(arm_data)
        except Exception as e:
            print(f"Error loading MAB state from Redis: {e}")
    
    def _save_to_redis(self):
        """Save MAB state to Redis."""
        if not self.redis_client:
            return
        
        try:
            for arm_name, arm_data in self.arms.items():
                key = f"mab:{arm_name}"
                # Don't save rewards list (can be large), just summary
                save_data = {
                    'count': arm_data['count'],
                    'avg_reward': arm_data['avg_reward'],
                    'weight': arm_data['weight']
                }
                self.redis_client.set(key, json.dumps(save_data))
        except Exception as e:
            print(f"Error saving MAB state to Redis: {e}")
    
    def select_arm(self, context: Optional[Dict] = None) -> str:
        """
        Select an arm using epsilon-greedy strategy.
        
        Args:
            context: Optional context (event_id, user_features, etc.)
            
        Returns:
            Selected arm name
        """
        # Load current state
        self._load_from_redis()
        
        # Exploration: random selection
        if random.random() < self.epsilon:
            selected_arm = random.choice(list(self.arms.keys()))
        else:
            # Exploitation: select arm with highest average reward
            best_arm = max(
                self.arms.items(),
                key=lambda x: x[1]['avg_reward'] if x[1]['count'] > 0 else -1
            )
            selected_arm = best_arm[0]
        
        return selected_arm
    
    def update_reward(self, arm_name: str, reward: float, metadata: Optional[Dict] = None):
        """
        Update reward for an arm after observing outcome.
        
        Args:
            arm_name: Arm that was selected
            reward: Observed reward (e.g., revenue, conversion rate)
            metadata: Optional metadata (transaction_id, event_id, etc.)
        """
        if arm_name not in self.arms:
            return
        
        arm = self.arms[arm_name]
        
        # Update statistics
        arm['count'] += 1
        arm['rewards'].append({
            'reward': reward,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        
        # Update average reward (incremental update)
        n = arm['count']
        old_avg = arm['avg_reward']
        new_avg = old_avg + (reward - old_avg) / n
        arm['avg_reward'] = new_avg
        
        # Keep only last 1000 rewards in memory
        if len(arm['rewards']) > 1000:
            arm['rewards'] = arm['rewards'][-1000:]
        
        # Save to Redis
        self._save_to_redis()
    
    def get_arm_stats(self) -> Dict:
        """
        Get statistics for all arms.
        
        Returns:
            Dict with arm statistics
        """
        self._load_from_redis()
        
        stats = {}
        for arm_name, arm_data in self.arms.items():
            stats[arm_name] = {
                'count': arm_data['count'],
                'avg_reward': round(arm_data['avg_reward'], 4),
                'weight': arm_data['weight'],
                'total_reward': sum(r['reward'] for r in arm_data['rewards'])
            }
        
        return stats
    
    def route_request(self, request_id: str, event_id: Optional[int] = None,
                     user_features: Optional[Dict] = None) -> Dict:
        """
        Route a request to an arm and return decision.
        
        Args:
            request_id: Unique request identifier
            event_id: Optional event ID
            user_features: Optional user feature dict
            
        Returns:
            Dict with selected_arm, pricing_strategy, decision_path
        """
        context = {
            'request_id': request_id,
            'event_id': event_id,
            'user_features': user_features or {}
        }
        
        selected_arm = self.select_arm(context)
        
        # Determine pricing strategy based on arm
        pricing_strategies = {
            'baseline': {'type': 'fixed', 'multiplier': 1.0},
            'surge_pricing': {'type': 'dynamic', 'multiplier': 1.15, 'condition': 'demand_high'},
            'early_bird': {'type': 'time_based', 'early_multiplier': 0.9, 'late_multiplier': 1.2},
            'ml_pricing': {'type': 'ml_predicted', 'model': 'xgboost_pricing_v1'}
        }
        
        decision_path = {
            'selected_arm': selected_arm,
            'exploration': random.random() < self.epsilon,
            'epsilon': self.epsilon,
            'arm_stats': {
                arm: {'count': self.arms[arm]['count'], 'avg_reward': self.arms[arm]['avg_reward']}
                for arm in self.arms.keys()
            }
        }
        
        return {
            'selected_arm': selected_arm,
            'pricing_strategy': pricing_strategies[selected_arm],
            'decision_path': decision_path,
            'request_id': request_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_pricing(self, base_price: float, arm_name: str, 
                         event_features: Optional[Dict] = None) -> float:
        """
        Calculate final price based on selected arm and event features.
        
        Args:
            base_price: Base ticket price
            arm_name: Selected arm
            event_features: Optional event features (popularity, days_until, etc.)
            
        Returns:
            Final calculated price
        """
        if arm_name == 'baseline':
            return base_price
        
        elif arm_name == 'surge_pricing':
            popularity = event_features.get('popularity_score', 0.5) if event_features else 0.5
            if popularity > 0.7:
                return base_price * 1.15  # 15% surge
            return base_price
        
        elif arm_name == 'early_bird':
            days_until = event_features.get('days_until_event', 30) if event_features else 30
            if days_until > 30:
                return base_price * 0.9  # 10% early bird discount
            elif days_until < 3:
                return base_price * 1.2  # 20% late premium
            return base_price
        
        elif arm_name == 'ml_pricing':
            # Simplified ML pricing (would use actual model in production)
            popularity = event_features.get('popularity_score', 0.5) if event_features else 0.5
            demand_factor = 0.85 + (popularity * 0.3)  # 0.85 to 1.15 multiplier
            return base_price * demand_factor
        
        return base_price


# Singleton instance
_mab_instance = None

def get_mab(epsilon: float = 0.15) -> MultiArmedBandit:
    """Get singleton MAB instance."""
    global _mab_instance
    if _mab_instance is None:
        _mab_instance = MultiArmedBandit(epsilon=epsilon)
    return _mab_instance

