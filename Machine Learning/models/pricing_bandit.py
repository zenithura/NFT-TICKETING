"""
Pricing Bandit - Multi-Armed Bandit for Dynamic Pricing
Adaptive pricing optimization using epsilon-greedy strategy.
"""

import numpy as np
import random
from typing import Dict, Optional, List
from datetime import datetime
import json
from pathlib import Path


class PricingBandit:
    """
    Epsilon-greedy Multi-Armed Bandit for dynamic pricing optimization.
    
    Arms represent different pricing strategies:
    - standard: Base price (control)
    - premium_+10pct: 10% premium pricing
    - discount_-10pct: 10% discount
    - dynamic_peak: Demand-based dynamic pricing
    """
    
    ARM_NAMES = ['standard', 'premium_+10pct', 'discount_-10pct', 'dynamic_peak']
    
    def __init__(self, epsilon: float = 0.15, state_path: Optional[Path] = None):
        """
        Initialize pricing bandit.
        
        Args:
            epsilon: Exploration rate (0.0 = pure exploitation, 1.0 = pure exploration)
            state_path: Path to save/load bandit state
        """
        self.epsilon = epsilon
        self.state_path = state_path or Path(__file__).parent.parent / "artifacts" / "pricing_bandit_state.json"
        
        # Initialize arms
        self.arms = {
            arm: {
                'count': 0,
                'total_reward': 0.0,
                'avg_reward': 0.0,
                'rewards': []  # Keep last 1000 for analysis
            }
            for arm in self.ARM_NAMES
        }
        
        # Load state if exists
        self.load_state()
    
    def load_state(self) -> bool:
        """Load bandit state from disk."""
        try:
            if self.state_path.exists():
                with open(self.state_path, 'r') as f:
                    data = json.load(f)
                    self.arms = data.get('arms', self.arms)
                    self.epsilon = data.get('epsilon', self.epsilon)
                print(f"✅ Loaded pricing bandit state from {self.state_path}")
                return True
        except Exception as e:
            print(f"⚠️  Could not load state: {e}")
        
        return False
    
    def save_state(self):
        """Save bandit state to disk."""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Limit rewards list size for storage
            arms_save = {}
            for arm_name, arm_data in self.arms.items():
                arms_save[arm_name] = {
                    'count': arm_data['count'],
                    'total_reward': arm_data['total_reward'],
                    'avg_reward': arm_data['avg_reward'],
                    'rewards': arm_data['rewards'][-100:]  # Keep last 100
                }
            
            data = {
                'arms': arms_save,
                'epsilon': self.epsilon,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.state_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save state: {e}")
    
    def select_arm(self, context: Optional[Dict] = None) -> Dict:
        """
        Select pricing arm using epsilon-greedy strategy.
        
        Args:
            context: Optional context (event_id, user_cluster, time_until_event, current_demand)
            
        Returns:
            Dict with selected_arm, expected_reward, exploration_flag
        """
        # Exploration: random selection
        is_exploring = random.random() < self.epsilon
        
        if is_exploring:
            selected_arm = random.choice(self.ARM_NAMES)
        else:
            # Exploitation: select arm with highest average reward
            # Only consider arms that have been tried at least once
            tried_arms = {
                arm: data for arm, data in self.arms.items()
                if data['count'] > 0
            }
            
            if not tried_arms:
                # If no arms tried yet, use exploration
                selected_arm = random.choice(self.ARM_NAMES)
                is_exploring = True
            else:
                best_arm = max(
                    tried_arms.items(),
                    key=lambda x: x[1]['avg_reward']
                )
                selected_arm = best_arm[0]
        
        expected_reward = self.arms[selected_arm]['avg_reward']
        
        return {
            'selected_arm': selected_arm,
            'expected_reward': round(expected_reward, 4),
            'exploration_flag': is_exploring,
            'epsilon': self.epsilon,
            'arm_stats': {
                arm: {
                    'count': data['count'],
                    'avg_reward': round(data['avg_reward'], 4)
                }
                for arm, data in self.arms.items()
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def update_reward(self, arm_name: str, reward: float, metadata: Optional[Dict] = None):
        """
        Update reward for an arm after observing outcome.
        
        Args:
            arm_name: Arm that was selected
            reward: Observed reward (e.g., revenue per transaction)
            metadata: Optional metadata (transaction_id, event_id, etc.)
        """
        if arm_name not in self.arms:
            return
        
        arm = self.arms[arm_name]
        
        # Update statistics
        arm['count'] += 1
        arm['total_reward'] += reward
        
        # Incremental average update
        n = arm['count']
        old_avg = arm['avg_reward']
        new_avg = old_avg + (reward - old_avg) / n
        arm['avg_reward'] = new_avg
        
        # Store reward history (keep last 1000)
        arm['rewards'].append({
            'reward': reward,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        if len(arm['rewards']) > 1000:
            arm['rewards'] = arm['rewards'][-1000:]
        
        # Save state periodically (every 10 updates)
        if arm['count'] % 10 == 0:
            self.save_state()
    
    def calculate_price(self, base_price: float, arm_name: str, 
                       event_features: Optional[Dict] = None) -> float:
        """
        Calculate final price based on selected arm.
        
        Args:
            base_price: Base ticket price
            arm_name: Selected arm
            event_features: Optional event features (popularity, days_until_event, etc.)
            
        Returns:
            Final calculated price
        """
        if arm_name == 'standard':
            return base_price
        
        elif arm_name == 'premium_+10pct':
            return base_price * 1.10
        
        elif arm_name == 'discount_-10pct':
            return base_price * 0.90
        
        elif arm_name == 'dynamic_peak':
            # Dynamic pricing based on demand/popularity
            popularity = event_features.get('popularity_score', 0.5) if event_features else 0.5
            days_until = event_features.get('days_until_event', 30) if event_features else 30
            
            # Higher popularity → higher price (up to +20%)
            # Fewer days until event → higher price (up to +15%)
            popularity_multiplier = 0.90 + (popularity * 0.30)  # 0.90 to 1.20
            time_multiplier = 1.0 if days_until > 7 else (1.0 + (7 - days_until) * 0.021)  # +15% max
            
            return base_price * popularity_multiplier * time_multiplier
        
        return base_price
    
    def get_arm_stats(self) -> Dict:
        """
        Get statistics for all arms.
        
        Returns:
            Dict with arm statistics
        """
        stats = {}
        for arm_name, arm_data in self.arms.items():
            stats[arm_name] = {
                'count': arm_data['count'],
                'avg_reward': round(arm_data['avg_reward'], 4),
                'total_reward': round(arm_data['total_reward'], 4),
                'n_rewards': len(arm_data['rewards'])
            }
        return stats
    
    def get_cumulative_regret(self, optimal_reward: float) -> float:
        """
        Calculate cumulative regret (difference from optimal).
        
        Args:
            optimal_reward: Known optimal reward (for evaluation)
            
        Returns:
            Cumulative regret
        """
        regret = 0.0
        for arm_data in self.arms.values():
            if arm_data['count'] > 0:
                regret += arm_data['count'] * (optimal_reward - arm_data['avg_reward'])
        return regret


# Singleton instance
_pricing_bandit = None

def get_pricing_bandit(epsilon: float = 0.15) -> PricingBandit:
    """Get singleton pricing bandit instance."""
    global _pricing_bandit
    if _pricing_bandit is None:
        _pricing_bandit = PricingBandit(epsilon=epsilon)
    return _pricing_bandit


if __name__ == "__main__":
    # Example usage
    bandit = PricingBandit(epsilon=0.15)
    
    # Simulate some pulls
    for i in range(10):
        decision = bandit.select_arm()
        print(f"Selected arm: {decision['selected_arm']} (exploring: {decision['exploration_flag']})")
        
        # Simulate reward (higher reward for premium, lower for discount)
        reward_map = {
            'standard': 50.0,
            'premium_+10pct': 55.0,  # Higher revenue
            'discount_-10pct': 45.0,  # Lower revenue
            'dynamic_peak': 52.0
        }
        reward = reward_map[decision['selected_arm']] + random.uniform(-2, 2)
        bandit.update_reward(decision['selected_arm'], reward)
    
    print("\nArm Statistics:")
    stats = bandit.get_arm_stats()
    for arm, data in stats.items():
        print(f"  {arm}: count={data['count']}, avg_reward={data['avg_reward']}")

