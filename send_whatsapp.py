#!/usr/bin/env python3
"""CLI helper to send a WhatsApp message via the unified automation agent."""

import os
from unified_automation_agent import AutomationAgent


def main() -> None:
    agent = AutomationAgent(
        chrome_profile_path=os.environ.get("CHROME_PROFILE_PATH"),
        chrome_profile_directory=os.environ.get("CHROME_PROFILE_DIRECTORY"),
    )
    try:
        success = agent.send_whatsapp_message("256706272481", "Good morning")
        print("Message sent" if success else "Message failed")
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()
