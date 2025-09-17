#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('scripts')
from web_parser import WebParser
from media_manager import MediaManager
import logging

logging.basicConfig(level=logging.INFO)

def test_apnews_full():
    print("AP News full test - parsing and downloading video")
    print("=" * 60)
    
    # Initialize components
    web_parser = WebParser('config/config.yaml')
    media_manager = MediaManager({'media_dir': 'media', 'max_video_duration': 300, 'max_video_size': 100*1024*1024})
    
    # Test URL
    test_url = "https://apnews.com/video/images-of-trump-and-epstein-projected-on-windsor-castle-as-us-president-visits-uk-6b004c3ab53247078795780c5c4bf7b1"
    
    try:
        print(f"Testing URL: {test_url}")
        print("=" * 60)
        
        # Parse URL
        result = web_parser.parse_url(test_url)
        
        if result and result.get('success'):
            print("✅ URL parsed successfully")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"Source: {result.get('source', 'N/A')}")
            print(f"Images: {len(result.get('images', []))}")
            print(f"Videos: {len(result.get('videos', []))}")
            
            if result.get('videos'):
                print("Video URLs found:")
                for i, video_url in enumerate(result['videos'], 1):
                    print(f"  {i}. {video_url}")
                
                # Try to download the first video
                first_video = result['videos'][0]
                print(f"\n🔄 Trying to download video: {first_video}")
                
                downloaded_path = media_manager._download_jwplayer_video_direct(first_video, "AP News Test")
                if downloaded_path:
                    print(f"✅ Video downloaded successfully: {downloaded_path}")
                else:
                    print("❌ Failed to download video")
            else:
                print("❌ No videos found")
                
            if result.get('images'):
                print("Image URLs found:")
                for i, image_url in enumerate(result['images'], 1):
                    print(f"  {i}. {image_url}")
        else:
            print("❌ Failed to parse URL")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        web_parser.close()

if __name__ == "__main__":
    test_apnews_full()
