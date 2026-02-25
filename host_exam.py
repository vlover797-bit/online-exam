import os
import sys
import time
import subprocess
from pyngrok import ngrok, conf

# Optional: Configuration if needed
# conf.get_default().auth_token = "<TOKEN>"

def host_exam():
    # Start Django server in background
    # Using 0.0.0.0 to ensure it binds to all interfaces, though localhost is fine for ngrok
    print("Starting Django server...")
    django_process = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to start
    time.sleep(3)

    try:
        # Open a HTTP tunnel on port 8000
        print("Initializing ngrok tunnel...")
        public_url = ngrok.connect(8000).public_url
        print(f"\n========================================")
        print(f"EXAM HOSTED SUCCESSFULLY")
        print(f"Public Link: {public_url}")
        print(f"========================================\n")
        
        # Keep the script running to keep the tunnel open
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f"Error starting ngrok: {e}")
        print("You may need to sign up for ngrok (https://dashboard.ngrok.com/signup) and install your auth token.")
        print("Run: ngrok config add-authtoken <token>")
    finally:
        print("Shutting down...")
        ngrok.kill()
        django_process.terminate()

if __name__ == "__main__":
    host_exam()
