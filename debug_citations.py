#!/usr/bin/env python3
"""
Simple script to test visual citations in the browser and capture console logs
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def debug_citations():
    print("🔍 Testing visual citations with browser debugging...")
    
    # Configure Chrome to capture console logs
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Don't use headless mode so we can see what's happening
    # chrome_options.add_argument("--headless")
    
    # Enable logging
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("📱 Loading frontend at http://localhost:3000...")
        driver.get("http://localhost:3000")
        
        # Wait for page to load
        WebDriverWait(driver, 15).wait(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".chat-input, input[type='text']"))
        )
        
        print("💬 Sending test message...")
        
        # Find input field (try multiple selectors)
        input_field = None
        input_selectors = [
            ".chat-input",
            "input[type='text']",
            "textarea",
            ".message-input",
            "input[placeholder*='message']",
            "input[placeholder*='type']"
        ]
        
        for selector in input_selectors:
            try:
                input_field = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Found input field with selector: {selector}")
                break
            except:
                continue
        
        if not input_field:
            print("❌ Could not find input field")
            # Take screenshot for debugging
            driver.save_screenshot("/Users/johninniger/Workspace/line_lead_qsr_mvp/debug_no_input.png")
            return False
        
        # Clear and type message
        input_field.clear()
        input_field.send_keys("Show me an image of Pizza Canotto")
        
        # Try to find and click send button
        send_button = None
        send_selectors = [
            ".send-button",
            "button[type='submit']",
            "button:contains('Send')",
            ".submit-btn",
            "[aria-label*='send']"
        ]
        
        for selector in send_selectors:
            try:
                send_button = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Found send button with selector: {selector}")
                break
            except:
                continue
        
        if send_button:
            send_button.click()
        else:
            # Try pressing Enter
            print("⌨️ No send button found, trying Enter key...")
            input_field.send_keys(Keys.RETURN)
        
        print("⏳ Waiting for response...")
        time.sleep(5)  # Give time for the request to complete
        
        # Check for any messages that appeared
        messages = driver.find_elements(By.CSS_SELECTOR, ".message, .chat-message, .assistant-message")
        print(f"📝 Found {len(messages)} messages on page")
        
        # Look for citation elements
        citation_containers = driver.find_elements(By.CSS_SELECTOR, ".multimodal-citation-container")
        visual_citations = driver.find_elements(By.CSS_SELECTOR, ".visual-citations")
        citation_cards = driver.find_elements(By.CSS_SELECTOR, ".citation-card")
        
        print(f"📊 Citation elements found:")
        print(f"   - Citation containers: {len(citation_containers)}")
        print(f"   - Visual citation sections: {len(visual_citations)}")
        print(f"   - Citation cards: {len(citation_cards)}")
        
        # Capture console logs
        print("\n📋 Browser console logs:")
        logs = driver.get_log('browser')
        
        citation_logs = []
        for log in logs[-50:]:  # Get last 50 logs
            message = log['message']
            level = log['level']
            
            # Filter for our debug messages
            if any(keyword in message for keyword in ['🎯', '🔍', '📊', '📋', '✨', '🔄', '⚠️']):
                citation_logs.append(f"[{level}] {message}")
                print(f"   {message}")
        
        if not citation_logs:
            print("   No citation-related debug logs found")
            
            # Show all recent logs for debugging
            print("\n📝 Recent console logs:")
            for log in logs[-10:]:
                print(f"   [{log['level']}] {log['message']}")
        
        # Take screenshot for debugging
        driver.save_screenshot("/Users/johninniger/Workspace/line_lead_qsr_mvp/debug_citations_test.png")
        print("📸 Screenshot saved: debug_citations_test.png")
        
        # Wait a moment to see the result
        print("\n⏸️ Pausing for 10 seconds to observe the UI...")
        time.sleep(10)
        
        driver.quit()
        
        # Return whether we found citations
        return len(citation_cards) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    debug_citations()