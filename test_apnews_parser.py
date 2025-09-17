#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('scripts')
from web_parser import WebParser
import logging

logging.basicConfig(level=logging.INFO)

def test_apnews_parser():
    print("AP News parser test with JW Player support")
    print("=" * 60)
    
    # Initialize parser
    web_parser = WebParser('config/config.yaml')
    
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
    test_apnews_parser()
