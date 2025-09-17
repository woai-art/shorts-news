#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re

def test_apnews_debug():
    print("AP News debug - checking what we get")
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
        print(f"Content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check title
        title = soup.find('meta', property='og:title')
        if title:
            print(f"Title: {title.get('content')}")
        else:
            print("No title found")
        
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
        
        # Search for videos in text
        text = response.text
        print(f"\nSearching for videos in {len(text)} characters...")
        
        # JW Player pattern
        jwplayer_pattern = r'https://cdn\.jwplayer\.com/videos/[^"\s<>]+\.mp4'
        jwplayer_matches = re.findall(jwplayer_pattern, text, re.IGNORECASE)
        print(f"JW Player videos found: {len(jwplayer_matches)}")
        for match in jwplayer_matches:
            print(f"  {match}")
        
        # CDN pattern
        cdn_pattern = r'https://[^"\s<>]*\.(?:mp4|webm|mov)(?:\?[^"\s<>]*)?'
        cdn_matches = re.findall(cdn_pattern, text, re.IGNORECASE)
        print(f"CDN videos found: {len(cdn_matches)}")
        for match in cdn_matches[:5]:  # Show first 5
            print(f"  {match}")
        
        # Show first 1000 characters of HTML
        print(f"\nFirst 1000 characters of HTML:")
        print(response.text[:1000])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_apnews_debug()
