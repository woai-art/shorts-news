#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re

def test_apnews_simple():
    print("AP News video test")
    
    url = "https://apnews.com/video/images-of-trump-and-epstein-projected-on-windsor-castle-as-us-president-visits-uk-6b004c3ab53247078795780c5c4bf7b1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find video tags
        videos = soup.find_all('video')
        print(f"Found {len(videos)} video tags")
        
        for i, video in enumerate(videos):
            print(f"Video {i+1}:")
            print(f"  src: {video.get('src')}")
            print(f"  data-src: {video.get('data-src')}")
            
            sources = video.find_all('source')
            for j, source in enumerate(sources):
                print(f"  Source {j+1}: {source.get('src')}")
        
        # Find iframes
        iframes = soup.find_all('iframe')
        print(f"Found {len(iframes)} iframe tags")
        
        for i, iframe in enumerate(iframes):
            src = iframe.get('src')
            if src and 'video' in src.lower():
                print(f"  iframe {i+1}: {src}")
        
        # Search in text
        text = response.text
        mp4_matches = re.findall(r'https://[^\s"\'<>]+\.mp4', text)
        print(f"Found {len(mp4_matches)} MP4 URLs in text")
        for match in mp4_matches[:3]:
            print(f"  {match}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_apnews_simple()
