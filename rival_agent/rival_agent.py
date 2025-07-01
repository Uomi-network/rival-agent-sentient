import logging
import os
from dotenv import load_dotenv
from rival_agent.providers.model_provider import ModelProvider
from rival_agent.providers.search_provider import SearchProvider
from sentient_agent_framework import (
    AbstractAgent,
    DefaultServer,
    Session,
    Query,
    ResponseHandler)
from typing import AsyncIterator


load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RivalAgent(AbstractAgent):
    def __init__(
            self,
            name: str = "Rival"
    ):
        """Initialize the Rival Agent with blockchain and search capabilities."""
        super().__init__(name)

        # Blockchain configuration
        rpc_url = os.getenv("BLOCKCHAIN_RPC_URL")
        if not rpc_url:
            raise ValueError("BLOCKCHAIN_RPC_URL is not set")
        
        private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")  # Optional, will use mock if not provided
        contract_address = os.getenv("CONTRACT_ADDRESS", "0x609a8aeeef8b89be02c5b59a936a520547252824")
        nft_id = int(os.getenv("NFT_ID", "3"))
        
        self._model_provider = ModelProvider(
            rpc_url=rpc_url,
            private_key=private_key,
            contract_address=contract_address,
            nft_id=nft_id
        )
        logger.info(f"RivalAgent '{name}' initialized with blockchain NFT ID {nft_id}")

    async def assist(
            self,
            session: Session,
            query: Query,
            response_handler: ResponseHandler
    ):
        """Search the internet for information and process with blockchain AI."""
        try:
            # Search for information
            await response_handler.emit_text_block(
                "SEARCH", "🔍 Searching internet for results..."
            )
            search_results = await self._search_provider.search(query.prompt)
            
            if len(search_results["results"]) > 0:
                # Use response handler to emit JSON to the client
                await response_handler.emit_json(
                    "SOURCES", {"results": search_results["results"]}
                )
            if len(search_results["images"]) > 0:
                # Use response handler to emit JSON to the client
                await response_handler.emit_json(
                    "IMAGES", {"images": search_results["images"]}
                )

            # Process search results with blockchain AI
            await response_handler.emit_text_block(
                "PROCESSING", "🧠 Processing with blockchain AI agent..."
            )
            
            # Use response handler to create a text stream to stream the final response
            final_response_stream = response_handler.create_text_stream(
                "FINAL_RESPONSE"
            )
            async for chunk in self.__process_search_results(query.prompt, search_results["results"]):
                # Use the text stream to emit chunks of the final response to the client
                await final_response_stream.emit_chunk(chunk)
            
            # Mark the text stream as complete
            await final_response_stream.complete()
            # Mark the response as complete
            await response_handler.complete()
            
        except Exception as e:
            logger.error(f"Error in RivalAgent.assist: {e}")
            await response_handler.emit_text_block(
                "ERROR", f"❌ Error: {str(e)}"
            )
            await response_handler.complete()

    async def __process_search_results(
            self,
            prompt: str,
            search_results: dict
    ) -> AsyncIterator[str]:
        """Process the search results using the blockchain AI model."""
        try:
            process_query = f"""Based on the search results below, provide a comprehensive answer to the user's question.

User Question: {prompt}

Search Results: {search_results}

Please provide a well-structured, informative response that synthesizes the search results to answer the user's question. Include relevant details and cite sources when appropriate."""
            
            async for chunk in self._model_provider.query_stream(process_query):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error processing search results: {e}")
            yield f"Error processing search results: {str(e)}"

    def get_status(self) -> dict:
        """Get the current status of the Rival Agent."""
        return {
            "name": self.name,
            "blockchain_status": self._model_provider.get_connection_status(),
            "pending_requests": len(self._model_provider.get_pending_requests())
        }


def create_agent(name: str = "Rival") -> RivalAgent:
    """Factory function to create a RivalAgent instance."""
    return RivalAgent(name=name)


def main():
    """Main entry point for running the Rival Agent server."""
    try:
        # Create an instance of RivalAgent
        agent = RivalAgent(name="Rival")
        
        # Log startup information
        status = agent.get_status()
        logger.info(f"Starting {status['name']} agent")
        logger.info(f"Blockchain connected: {status['blockchain_status']['connected']}")
        logger.info(f"Contract: {status['blockchain_status']['contract_address']}")
        logger.info(f"NFT ID: {status['blockchain_status']['nft_id']}")
        
        # Create a server to handle requests to the agent
        server = DefaultServer(agent)
        
        # Run the server
        logger.info("Starting Rival Agent server...")
        server.run()
        
    except Exception as e:
        logger.error(f"Failed to start Rival Agent: {e}")
        raise


if __name__ == "__main__":
    main()
