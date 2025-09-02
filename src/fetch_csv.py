"""
CSV fetching and parsing functionality for timetable data.
"""

import csv
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from normalize import normalize_subject
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_today(timezone_str: str = "Asia/Tokyo", csv_path: str = "data/sample_timetable.csv") -> List[Dict[str, str]]:
    """
    Fetch today's timetable entries from CSV file.
    
    Args:
        timezone_str: Timezone string (default: "Asia/Tokyo")
        csv_path: Path to the CSV file
        
    Returns:
        List of dictionaries with subject and room information, sorted by period
        Returns empty list if no entries found for today
    """
    try:
        # Get today's date in the specified timezone
        tz = pytz.timezone(timezone_str)
        today = datetime.now(tz).strftime("%Y-%m-%d")
        logger.info(f"Fetching timetable for {today} in timezone {timezone_str}")
        
        # Check if CSV file exists
        csv_file = Path(csv_path)
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            return []
        
        # Read CSV and filter today's entries
        today_entries = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if row.get('date') == today:
                    today_entries.append({
                        'period': row.get('period', ''),
                        'subject': normalize_subject(row.get('subject', '')),
                        'room': row.get('room', '')
                    })
        
        # Sort by period (assuming period is numeric)
        try:
            today_entries.sort(key=lambda x: int(x.get('period', 0)) if x.get('period', '').isdigit() else 0)
        except (ValueError, TypeError):
            # If period sorting fails, keep original order
            logger.warning("Failed to sort by period, keeping original order")
        
        logger.info(f"Found {len(today_entries)} entries for today")
        return today_entries
        
    except Exception as e:
        logger.error(f"Error fetching today's timetable: {e}")
        return []


class TimetableFetcher:
    """Handles fetching and parsing of timetable CSV data."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def fetch_from_url(self, url: str, filename: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Fetch CSV data from a URL and save it locally.
        
        Args:
            url: URL to fetch CSV from
            filename: Optional filename to save as (defaults to URL basename)
            
        Returns:
            List of dictionaries with subject and room information
        """
        try:
            logger.info(f"Fetching timetable from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            if filename is None:
                filename = url.split('/')[-1] or "timetable.csv"
            
            filepath = self.data_dir / filename
            
            # Save the CSV data
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Saved timetable to: {filepath}")
            
            # Parse and return using fetch_today
            return fetch_today(csv_path=str(filepath))
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch timetable from {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching timetable: {e}")
            raise
    
    def load_local_csv(self, filename: str) -> List[Dict[str, str]]:
        """
        Load CSV data from local file.
        
        Args:
            filename: Name of the CSV file in the data directory
            
        Returns:
            List of dictionaries with subject and room information
        """
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        logger.info(f"Loading local timetable from: {filepath}")
        return fetch_today(csv_path=str(filepath))
    
    def get_sample_data(self) -> List[Dict[str, str]]:
        """
        Get sample timetable data for testing.
        
        Returns:
            List of dictionaries with sample timetable data
        """
        sample_data = [
            {'date': '2025-09-01', 'period': '1', 'subject': '국어', 'room': '201'},
            {'date': '2025-09-01', 'period': '2', 'subject': '수학', 'room': '201'},
            {'date': '2025-09-01', 'period': '3', 'subject': '영어', 'room': '201'},
            {'date': '2025-09-01', 'period': '4', 'subject': '체육', 'room': '운동장'},
            {'date': '2025-09-01', 'period': '5', 'subject': '과학', 'room': '실험실'}
        ]
        
        return sample_data


def main():
    """Example usage of fetch_today function."""
    try:
        # Test fetch_today function
        print("Testing fetch_today function...")
        today_entries = fetch_today()
        
        if today_entries:
            print(f"Found {len(today_entries)} entries for today:")
            for entry in today_entries:
                print(f"  • {entry['subject']} - {entry['room']}")
        else:
            print("No entries found for today")
        
        # Test with different timezone
        print(f"\nTesting with different timezone...")
        tokyo_entries = fetch_today("Asia/Tokyo")
        print(f"Tokyo timezone: {len(tokyo_entries)} entries")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
