import sys
import os
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.ai.service import AIService

# Configure logging to see the output
logging.basicConfig(level=logging.INFO)


def test_chat():
    print("--- Testing AI Chat ---")
    try:
        service = AIService()

        msg = "Hey"
        print(f"User: {msg}")
        response = service.send_message(msg)
        print(f"AI: {response}")

    except Exception as e:
        print(f"Test Failed Main: {e}")


if __name__ == "__main__":
    test_chat()
