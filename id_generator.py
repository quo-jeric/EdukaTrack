import random
import string
from typing import Dict, Set, List
import os

class IDGenerator:
    def __init__(self):
        self.generated_ids: Set[str] = set()
        self.prefix_counters: Dict[str, int] = {'S': 1, 'T': 1, 'A': 1}
        self.recent_ids: List[str] = []
        self.file_path = 'generated_ids.txt'
        self.load_ids()
        
    def load_ids(self):
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    id_str = line.strip()
                    if id_str:
                        self.generated_ids.add(id_str)
                        if '-' in id_str:
                            prefix, num_str = id_str.split('-')
                            try:
                                num = int(num_str)
                                if prefix in self.prefix_counters and num >= self.prefix_counters[prefix]:
                                    self.prefix_counters[prefix] = num + 1
                            except ValueError:
                                pass
        except IOError as e:
            print(f"Warning: Could not load IDs: {e}")
        
    def save_ids(self):
        try:
            with open(self.file_path, 'w') as f:
                for id_str in sorted(self.generated_ids):
                    f.write(f"{id_str}\n")
        except IOError as e:
            print(f"Warning: Could not save generated IDs: {e}")

    def generate_unique_id(self, prefix: str) -> str:
        if prefix not in ['S', 'T', 'A']:
            raise ValueError("Prefix must be 'S' (Student), 'T' (Teacher), or 'A' (Admin)")
        
        for _ in range(1000):
            counter = self.prefix_counters[prefix]
            new_id = f"{prefix}-{counter:05d}"

            if new_id not in self.generated_ids:
                self.generated_ids.add(new_id)
                self.prefix_counters[prefix] += 1
                self.recent_ids.append(new_id)
                self.save_ids()
                return new_id
            
            self.prefix_counters[prefix] += 1
        
        for _ in range(1000):
            random_num = random.randint(1, 99999)
            new_id = f"{prefix}-{random_num:05d}"
            
            if new_id not in self.generated_ids:
                self.generated_ids.add(new_id)
                self.recent_ids.append(new_id)
                self.save_ids()
                return new_id
            
        raise Exception(f"Cannot generate ID for prefix {prefix}")

    def generate_strong_password(self) -> str:
        numbers = random.choices(string.digits, k=2)
        letters = random.choices(string.ascii_letters, k=6)
        password_chars = numbers + letters
        random.shuffle(password_chars)
        return ''.join(password_chars)
    
    def reserve_id(self, id_to_reserve: str) -> bool:
        if id_to_reserve in self.generated_ids:
            return False
        
        prefix = id_to_reserve.split('-')[0]
        if prefix in ['S', 'T', 'A']:
            self.generated_ids.add(id_to_reserve)
            self.recent_ids.append(id_to_reserve)
            self.save_ids()
            return True
        return False
    
    def release_id(self, id_to_release: str) -> bool:
        if id_to_release in self.generated_ids:
            self.generated_ids.remove(id_to_release)
            self.save_ids()
            return True
        return False
    
    def get_all_ids(self) -> list:
        return sorted(list(self.generated_ids))
    
    def get_stats(self) -> Dict:
        stats = {
            'total_ids': len(self.generated_ids),
            'prefix_counts': {},
            'recent_ids': self.recent_ids[-10:]
        }
        
        for id_str in self.generated_ids:
            prefix = id_str.split('-')[0]
            stats['prefix_counts'][prefix] = stats['prefix_counts'].get(prefix, 0) + 1
        
        return stats

id_generator = IDGenerator()
