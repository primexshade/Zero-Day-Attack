"""
Synthetic Network Traffic Data Generator for X-IDS Framework

Generates realistic network traffic data matching CICIDS2017 and UNSW-NB15 schema
for framework testing and development without requiring actual dataset downloads.

Features:
- Mimics CICIDS2017 and UNSW-NB15 feature distributions
- Generates normal and attack traffic patterns
- Configurable class imbalance (typical 99.3% normal, 0.7% attack)
- Supports various attack types: DoS, Port Scan, Botnet, Web Attack, etc.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')


@dataclass
class SyntheticDatasetConfig:
    """Configuration for synthetic data generation."""
    n_normal_samples: int = 50000
    n_attack_samples: int = 5000
    random_seed: int = 42
    test_split: float = 0.2
    feature_noise: float = 0.05
    

class SyntheticNetworkTrafficGenerator:
    """Generate synthetic network traffic data with realistic patterns."""
    
    # CICIDS2017 feature set (85 features)
    CICIDS2017_FEATURES = [
        'Flow Duration', 'Total Fwd Packets', 'Total Bwd Packets', 'Total Length of Fwd Packets',
        'Total Length of Bwd Packets', 'Fwd Packet Length Max', 'Fwd Packet Length Min',
        'Fwd Packet Length Mean', 'Fwd Packet Length Std', 'Bwd Packet Length Max',
        'Bwd Packet Length Min', 'Bwd Packet Length Mean', 'Bwd Packet Length Std',
        'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max',
        'Flow IAT Min', 'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Std', 'Fwd IAT Max',
        'Fwd IAT Min', 'Bwd IAT Total', 'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max',
        'Bwd IAT Min', 'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags',
        'Fwd Header Length', 'Bwd Header Length', 'Fwd Packets/s', 'Bwd Packets/s',
        'Min Packet Length', 'Max Packet Length', 'Packet Length Mean', 'Packet Length Std',
        'Packet Length Variance', 'FIN Flag Count', 'SYN Flag Count', 'RST Flag Count',
        'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count', 'CWE Flag Count',
        'ECE Flag Count', 'Down/Up Ratio', 'Average Packet Size', 'Avg Fwd Segment Size',
        'Avg Bwd Segment Size', 'Fwd Header Length.1', 'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk',
        'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate',
        'Subflow Fwd Packets', 'Subflow Fwd Bytes', 'Subflow Bwd Packets', 'Subflow Bwd Bytes',
        'Init Fwd Win Bytes', 'Init Bwd Win Bytes', 'Fwd Act Data Pkts', 'Fwd Seg Size Min',
        'Active Mean', 'Active Std', 'Active Max', 'Active Min', 'Idle Mean', 'Idle Std',
        'Idle Max', 'Idle Min', 'Label'
    ]
    
    # UNSW-NB15 features (49 features)
    UNSWNB15_FEATURES = [
        'srcip', 'sport', 'dstip', 'dsport', 'proto', 'state', 'dur', 'sbytes', 'dbytes',
        'sttl', 'dttl', 'sloss', 'dloss', 'service', 'sload', 'dload', 'spkts', 'dpkts',
        'swin', 'dwin', 'stcpb', 'dtcpb', 'smeansz', 'dmeansz', 'trans_depth', 'response_body_len',
        'sjit', 'djit', 'stime', 'ltime', 'sintpkt', 'dintpkt', 'tcprtt', 'synack', 'ackdat',
        'is_sm_ips_ports', 'ct_state_ttl', 'ct_flw_http_mthd', 'is_ftp_login', 'ct_ftp_cmd',
        'ct_srv_src', 'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ltm', 'ct_src_dport_ltm',
        'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'attack_cat', 'Label'
    ]
    
    # Attack types and their characteristics
    ATTACK_PATTERNS = {
        'DoS': {
            'Flow Duration': (10, 1000),
            'Flow Packets/s': (100, 10000),
            'Total Fwd Packets': (1000, 100000),
            'Fwd Packet Length Mean': (40, 100),
        },
        'PortScan': {
            'Flow Duration': (5, 300),
            'Total Fwd Packets': (5, 50),
            'Bwd Packet Length Mean': (0, 10),
            'Flow IAT Mean': (1, 100),
        },
        'Botnet': {
            'Flow Duration': (60, 3600),
            'Flow Bytes/s': (1000, 50000),
            'Fwd Packet Length Mean': (100, 1000),
            'ACK Flag Count': (10, 100),
        },
        'WebAttack': {
            'Flow Duration': (30, 600),
            'Total Length of Fwd Packets': (1000, 10000),
            'Fwd Packet Length Mean': (500, 1500),
            'Total Fwd Packets': (10, 100),
        },
        'Infiltration': {
            'Flow Duration': (300, 7200),
            'Flow Bytes/s': (100, 5000),
            'Total Fwd Packets': (50, 500),
            'Fwd IAT Mean': (100, 1000),
        },
    }
    
    def __init__(self, config: SyntheticDatasetConfig = None):
        """Initialize generator with configuration."""
        self.config = config or SyntheticDatasetConfig()
        np.random.seed(self.config.random_seed)
        
    def generate_cicids2017_like(self) -> pd.DataFrame:
        """Generate CICIDS2017-like synthetic data."""
        print(f"Generating {self.config.n_normal_samples} normal samples...")
        normal_data = self._generate_normal_traffic(self.config.n_normal_samples)
        
        print(f"Generating {self.config.n_attack_samples} attack samples...")
        attack_data = self._generate_attack_traffic(self.config.n_attack_samples)
        
        # Combine normal and attack data
        df = pd.concat([normal_data, attack_data], ignore_index=True)
        df = df.sample(frac=1, random_state=self.config.random_seed).reset_index(drop=True)
        
        print(f"Generated {len(df)} total samples")
        print(f"Class distribution:\n{df['Label'].value_counts()}")
        
        return df
    
    def generate_unswnb15_like(self) -> pd.DataFrame:
        """Generate UNSW-NB15-like synthetic data."""
        print(f"Generating {self.config.n_normal_samples} normal samples (UNSW-NB15 format)...")
        normal_data = self._generate_unswnb15_normal(self.config.n_normal_samples)
        
        print(f"Generating {self.config.n_attack_samples} attack samples (UNSW-NB15 format)...")
        attack_data = self._generate_unswnb15_attack(self.config.n_attack_samples)
        
        # Combine
        df = pd.concat([normal_data, attack_data], ignore_index=True)
        df = df.sample(frac=1, random_state=self.config.random_seed).reset_index(drop=True)
        
        print(f"Generated {len(df)} total samples")
        print(f"Class distribution:\n{df['Label'].value_counts()}")
        
        return df
    
    def _generate_normal_traffic(self, n_samples: int) -> pd.DataFrame:
        """Generate normal network traffic patterns."""
        data = {}
        
        # Flow characteristics for normal traffic
        for feature in self.CICIDS2017_FEATURES[:-1]:  # Exclude Label
            if 'Duration' in feature:
                data[feature] = np.random.exponential(10, n_samples)
            elif 'Packets' in feature or 'Flags' in feature or 'Count' in feature:
                data[feature] = np.random.poisson(5, n_samples).astype(float)
            elif 'Length' in feature or 'Bytes' in feature:
                data[feature] = np.random.gamma(2, 100, n_samples)
            elif 'IAT' in feature or 'Mean' in feature or 'Std' in feature:
                data[feature] = np.random.lognormal(2, 1, n_samples)
            elif 'Ratio' in feature or 'Rate' in feature:
                data[feature] = np.random.beta(2, 5, n_samples) * 10
            else:
                data[feature] = np.random.normal(10, 5, n_samples)
        
        # Add label
        data['Label'] = 'BENIGN'
        
        return pd.DataFrame(data)
    
    def _generate_attack_traffic(self, n_samples: int) -> pd.DataFrame:
        """Generate attack traffic patterns."""
        data = {}
        attack_types = list(self.ATTACK_PATTERNS.keys())
        
        # Initialize with normal-like values
        for feature in self.CICIDS2017_FEATURES[:-1]:
            if 'Duration' in feature:
                data[feature] = np.random.exponential(10, n_samples)
            elif 'Packets' in feature or 'Flags' in feature or 'Count' in feature:
                data[feature] = np.random.poisson(5, n_samples).astype(float)
            elif 'Length' in feature or 'Bytes' in feature:
                data[feature] = np.random.gamma(2, 100, n_samples)
            elif 'IAT' in feature or 'Mean' in feature or 'Std' in feature:
                data[feature] = np.random.lognormal(2, 1, n_samples)
            elif 'Ratio' in feature or 'Rate' in feature:
                data[feature] = np.random.beta(2, 5, n_samples) * 10
            else:
                data[feature] = np.random.normal(10, 5, n_samples)
        
        # Apply attack-specific modifications
        for i in range(n_samples):
            attack_type = np.random.choice(attack_types)
            patterns = self.ATTACK_PATTERNS[attack_type]
            
            for feature, (min_val, max_val) in patterns.items():
                if feature in data:
                    data[feature][i] = np.random.uniform(min_val, max_val) * (1 + np.random.normal(0, self.config.feature_noise))
        
        # Ensure non-negative values
        for col in data:
            data[col] = np.maximum(data[col], 0)
        
        # Assign attack labels
        data['Label'] = np.random.choice(attack_types, n_samples)
        
        return pd.DataFrame(data)
    
    def _generate_unswnb15_normal(self, n_samples: int) -> pd.DataFrame:
        """Generate UNSW-NB15 normal traffic."""
        data = {}
        
        for feature in self.UNSWNB15_FEATURES[:-1]:
            if feature in ['srcip', 'dstip']:
                data[feature] = [f"{np.random.randint(1,256)}.{np.random.randint(0,256)}.{np.random.randint(0,256)}.{np.random.randint(0,256)}" for _ in range(n_samples)]
            elif feature in ['sport', 'dsport']:
                data[feature] = np.random.randint(1024, 65535, n_samples)
            elif feature == 'proto':
                data[feature] = np.random.choice([6, 17], n_samples)  # TCP or UDP
            elif feature == 'state':
                data[feature] = np.random.choice(['ACC', 'CLO', 'CON', 'ECO', 'FIN', 'INT', 'REQ', 'RST'], n_samples)
            elif feature == 'service':
                data[feature] = np.random.choice(['http', 'ftp', 'ssh', 'dns', 'smtp'], n_samples)
            elif feature in ['dur', 'sbytes', 'dbytes', 'sload', 'dload', 'spkts', 'dpkts']:
                data[feature] = np.random.exponential(100, n_samples)
            else:
                data[feature] = np.random.normal(10, 5, n_samples)
        
        data['Label'] = 'Normal'
        data['attack_cat'] = 'Normal'
        
        return pd.DataFrame(data)
    
    def _generate_unswnb15_attack(self, n_samples: int) -> pd.DataFrame:
        """Generate UNSW-NB15 attack traffic."""
        data = {}
        attack_cats = ['DoS', 'Backdoor', 'Analysis', 'Fuzzers', 'Shellcode', 'Reconnaissance', 'Worms']
        
        for feature in self.UNSWNB15_FEATURES[:-1]:
            if feature in ['srcip', 'dstip']:
                data[feature] = [f"{np.random.randint(1,256)}.{np.random.randint(0,256)}.{np.random.randint(0,256)}.{np.random.randint(0,256)}" for _ in range(n_samples)]
            elif feature in ['sport', 'dsport']:
                data[feature] = np.random.randint(1024, 65535, n_samples)
            elif feature == 'proto':
                data[feature] = np.random.choice([6, 17], n_samples)
            elif feature == 'state':
                data[feature] = np.random.choice(['ACC', 'CLO', 'CON', 'ECO', 'FIN', 'INT', 'REQ', 'RST'], n_samples)
            elif feature == 'service':
                data[feature] = np.random.choice(['http', 'ftp', 'ssh', 'dns', 'smtp'], n_samples)
            elif 'bytes' in feature or 'load' in feature or 'pkts' in feature:
                # Attack traffic has different patterns
                data[feature] = np.random.exponential(500, n_samples)
            else:
                data[feature] = np.random.normal(50, 20, n_samples)
        
        data['Label'] = 'Attack'
        data['attack_cat'] = np.random.choice(attack_cats, n_samples)
        
        return pd.DataFrame(data)
    
    def save_datasets(self, output_dir: str = './data'):
        """Generate and save both CICIDS2017 and UNSW-NB15-like datasets."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate CICIDS2017-like
        print("\n" + "="*60)
        print("CICIDS2017-like Dataset Generation")
        print("="*60)
        cicids_df = self.generate_cicids2017_like()
        cicids_path = output_path / 'cicids2017_synthetic.csv'
        cicids_df.to_csv(cicids_path, index=False)
        print(f"✅ Saved to {cicids_path}")
        
        # Generate UNSW-NB15-like
        print("\n" + "="*60)
        print("UNSW-NB15-like Dataset Generation")
        print("="*60)
        unsw_df = self.generate_unswnb15_like()
        unsw_path = output_path / 'unswnb15_synthetic.csv'
        unsw_df.to_csv(unsw_path, index=False)
        print(f"✅ Saved to {unsw_path}")
        
        # Print summary statistics
        print("\n" + "="*60)
        print("Dataset Summary")
        print("="*60)
        print(f"\nCICIDS2017-like Dataset:")
        print(f"  Shape: {cicids_df.shape}")
        print(f"  Features: {len(cicids_df.columns) - 1}")
        print(f"  Memory: {cicids_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print(f"\nUNSW-NB15-like Dataset:")
        print(f"  Shape: {unsw_df.shape}")
        print(f"  Features: {len(unsw_df.columns) - 1}")
        print(f"  Memory: {unsw_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        return cicids_df, unsw_df


def generate_all_datasets(
    n_normal: int = 50000,
    n_attack: int = 5000,
    output_dir: str = './data'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Quick function to generate both datasets.
    
    Args:
        n_normal: Number of normal samples
        n_attack: Number of attack samples
        output_dir: Where to save CSV files
    
    Returns:
        Tuple of (cicids_df, unsw_df)
    """
    config = SyntheticDatasetConfig(
        n_normal_samples=n_normal,
        n_attack_samples=n_attack
    )
    generator = SyntheticNetworkTrafficGenerator(config)
    return generator.save_datasets(output_dir)


if __name__ == '__main__':
    # Example usage
    generator = SyntheticNetworkTrafficGenerator(
        SyntheticDatasetConfig(
            n_normal_samples=50000,
            n_attack_samples=5000
        )
    )
    cicids_df, unsw_df = generator.save_datasets()
