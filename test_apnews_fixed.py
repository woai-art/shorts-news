#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re

def test_apnews_fixed():
    print("AP News fixed debug")
    print("=" * 60)
    
    url = "https://apnews.com/video/images-of-trump-and-epstein-projected-on-windsor-castle-as-us-president-visits-uk-6b004c3ab53247078795780c5c4bf7b1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Content-Encoding: {response.headers.get('content-encoding', 'None')}")
        print(f"Content-Type: {response.headers.get('content-type', 'None')}")
        
        # Try different decoding methods
        content = response.text
        print(f"Text length: {len(content)}")
        
        if len(content) < 1000:
            print("Content seems compressed, trying different decoding...")
            content = response.content.decode('utf-8', errors='ignore')
            print(f"Decoded length: {len(content)}")
        
        # Check if content looks like HTML
        if '<html' in content.lower() or '<!doctype' in content.lower():
            print("✅ Content looks like HTML")
        else:
            print("❌ Content doesn't look like HTML")
            print(f"First 200 chars: {content[:200]}")
            return
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check title
        title = soup.find('meta', property='og:title')
        if title:
            print(f"Title: {title.get('content')}")
        else:
            print("No og:title found")
            title_tag = soup.find('title')
            if title_tag:
                print(f"Title tag: {title_tag.get_text()}")
        
        # Check description
        description = soup.find('meta', property='og:description')
        if description:
            print(f"Description: {description.get('content')}")
        else:
            print("No description found")
        
        # Check images
        og_image = soup.find('meta', property='og:image')
        if og_image:
            print(f"Image: {og_image.get('content')}")
        else:
            print("No image found")
        
        # Search for videos
        print(f"\nSearching for videos in {len(content)} characters...")
        
        # JW Player pattern
        jwplayer_pattern = r'https://cdn\.jwplayer\.com/videos/[^"\s<>]+\.mp4'
        jwplayer_matches = re.findall(jwplayer_pattern, content, re.IGNORECASE)
        print(f"JW Player videos found: {len(jwplayer_matches)}")
        for match in jwplayer_matches:
            print(f"  {match}")
        
        # CDN pattern
        cdn_pattern = r'https://[^"\s<>]*\.(?:mp4|webm|mov)(?:\?[^"\s<>]*)?'
        cdn_matches = re.findall(cdn_pattern, content, re.IGNORECASE)
        print(f"CDN videos found: {len(cdn_matches)}")
        for match in cdn_matches[:5]:
            print(f"  {match}")
        
        # Show first 1000 characters
        print(f"\nFirst 1000 characters:")
        print(content[:1000])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_apnews_fixed()
