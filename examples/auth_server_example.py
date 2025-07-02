#!/usr/bin/env python3
"""
Example of using the AuthenticatedServer with a RivalAgent.

This example shows how to use the AuthenticatedServer which extends
the DefaultServer and adds API key authentication via middleware.
"""

import os
import logging
from dotenv import load_dotenv
from rival_agent import RivalAgent
from rival_agent.auth_server import AuthenticatedServer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to start the authenticated server."""
    try:
        # Create a RivalAgent instance
        agent = RivalAgent(name="AuthenticatedRival")
        
        # Log startup information
        status = agent.get_status()
        logger.info(f"Starting {status['name']} agent with authentication")
        logger.info(f"Blockchain connected: {status['blockchain_status']['connected']}")
        logger.info(f"Contract: {status['blockchain_status']['contract_address']}")
        logger.info(f"NFT ID: {status['blockchain_status']['nft_id']}")
        
        # Create an authenticated server
        # API key can be provided explicitly or via RIVAL_API_KEY environment variable
        server = AuthenticatedServer(
            agent=agent,
            api_key=os.getenv("RIVAL_API_KEY"),  # Optional: will use env var if not provided
        )
        
        logger.info("Starting authenticated Rival Agent server...")
        logger.info("All endpoints except '/' and '/health' require authentication")
        logger.info("Use: curl -H 'Authorization: Bearer YOUR_API_KEY' http://localhost:8000/assist")
        
        # Run the server
        server.run(
            host="0.0.0.0",
            port=8000
        )
        
    except Exception as e:
        logger.error(f"Failed to start authenticated Rival Agent: {e}")
        raise


if __name__ == "__main__":
    main()
