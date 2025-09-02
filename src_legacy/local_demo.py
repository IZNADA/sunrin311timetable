"""
Local demonstration of the complete timetable workflow.
"""

import csv
from pathlib import Path
import logging
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

# Import our modules
from fetch_csv import fetch_today
from render_image import render_timetable_image
from detect_change import calc_hash, record_post
from utils import format_date_kr

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_today_date_str() -> str:
    """
    Get today's date string in Asia/Tokyo timezone.
    
    Returns:
        Date string in format "YYYY-MM-DD (Day)"
    """
    tz = pytz.timezone("Asia/Tokyo")
    today = datetime.now(tz)
    return format_date_kr(today)


def create_dummy_timetable():
    """
    Create dummy timetable data for today if none exists.
    
    Returns:
        List of timetable entries
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    dummy_data = [
        {'date': today, 'period': '1', 'subject': '국어', 'room': '201'},
        {'date': today, 'period': '2', 'subject': '수학', 'room': '201'},
        {'date': today, 'period': '3', 'subject': '영어', 'room': '201'},
        {'date': today, 'period': '4', 'subject': '체육', 'room': '운동장'},
        {'date': today, 'period': '5', 'subject': '과학', 'room': '실험실'}
    ]
    
    # Save to CSV
    csv_path = "data/sample_timetable.csv"
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'period', 'subject', 'room'])
        writer.writeheader()
        writer.writerows(dummy_data)
    
    logger.info(f"Created dummy timetable for {today}")
    return dummy_data


def main():
    """Main function to run the local demo."""
    try:
        print("🚀 Starting Insta-Timetable Local Demo")
        print("=" * 50)
        
        # Get today's date string
        date_str = get_today_date_str()
        print(f"📅 Today: {date_str}")
        
        # Extract date part for file naming
        date_only = date_str.split(' ')[0]  # "2025-09-01"
        
        # Step 1: Try to fetch today's timetable
        print("\n📊 Step 1: Fetching today's timetable...")
        timetable = fetch_today()
        
        if not timetable:
            print("⚠️  No timetable found for today, creating dummy data...")
            create_dummy_timetable()
            timetable = fetch_today()
        
        if timetable:
            print(f"✅ Found {len(timetable)} timetable entries")
            for entry in timetable:
                print(f"   • {entry['subject']} - {entry['room']}")
        else:
            print("❌ Failed to load timetable data")
            return
        
        # Step 2: Render timetable image
        print("\n🎨 Step 2: Rendering timetable image...")
        output_path = f"out/{date_only}.jpg"
        
        # Get brand color from environment variable
        brand_color = os.getenv("BRAND_COLOR_HEX", "#2A6CF0")
        
        # Include school and class info if provided via env
        school_name = os.getenv("SCHOOL_NAME")
        try:
            grade = int(os.getenv("GRADE")) if os.getenv("GRADE") else None
        except Exception:
            grade = os.getenv("GRADE")
        class_nm = os.getenv("CLASS_NM")

        image_path = render_timetable_image(
            date_str=date_str,
            timetable=timetable,
            out_path=output_path,
            brand_color=brand_color,
            school_name=school_name,
            grade=grade,
            class_nm=class_nm,
        )
        
        print(f"✅ Timetable image generated: {image_path}")
        
        # Step 3: Calculate hash and record post
        print("\n🔍 Step 3: Recording post...")
        hash_value = calc_hash(timetable)
        record_post(date_only, "local", hash_value)
        print(f"✅ Post recorded with hash: {hash_value[:8]}...")
        
        # Final result
        print(f"\n🎉 Demo completed successfully!")
        print(f"📁 Result: {output_path}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    main()
