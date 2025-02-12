# monitor.py
import psutil
import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_service():
    """Monitor the service and restart if necessary."""
    while True:
        try:
            # Check if gunicorn is running
            found = False
            for proc in psutil.process_iter(['name', 'cmdline']):
                if 'gunicorn' in proc.info['name']:
                    found = True
                    # Check CPU and memory usage
                    cpu_percent = proc.cpu_percent(interval=1)
                    memory_percent = proc.memory_percent()
                    
                    if cpu_percent > 90 or memory_percent > 90:
                        logger.warning(f"High resource usage detected: CPU={cpu_percent}%, Memory={memory_percent}%")
                        # Restart service
                        subprocess.run(['systemctl', 'restart', 'fin-advisor-api'])
                        
            if not found:
                logger.error("Service not found, restarting...")
                subprocess.run(['systemctl', 'restart', 'fin-advisor-api'])
                
        except Exception as e:
            logger.error(f"Error in monitoring: {str(e)}")
            
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    check_service()