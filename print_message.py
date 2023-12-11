from datetime import datetime

def print_message(message):
    timestamp = datetime.now().strftime("[%Y/%m/%d %H:%M:%S]")
    print(f"{timestamp}{message}")