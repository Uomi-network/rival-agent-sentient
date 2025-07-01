from datetime import datetime
import asyncio
import json
import time
import os
from typing import AsyncIterator, Optional, Dict, Any
from dataclasses import dataclass
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

@dataclass
class BlockchainEvent:
    """Data class for blockchain events"""
    event_type: str
    request_id: int
    data: Dict[str, Any]

class ModelProvider:
    def __init__(
        self,
        rpc_url: str,
        private_key: Optional[str] = None,
        contract_address: str = "0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id: int = 3
    ):
        """Initializes blockchain connection and smart contract interface."""

        # Blockchain configuration
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.nft_id = nft_id
        
        # Request tracking
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        
        # Event polling configuration
        self.polling_interval = 2.0  # seconds
        self.max_wait_time = 300.0  # 5 minutes timeout
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        
        # Setup Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add middleware for POA chains if needed
        if not self.w3.is_connected():
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Setup account for transaction signing
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            self.wallet_address = self.account.address
        else:
            # For testing without real private key
            self.account = None
            self.wallet_address = "0x0000000000000000000000000000000000000000"
            self.logger.warning("No private key provided - running in mock mode")
        
        # Setup contract instance
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        # Verify connection
        if self.w3.is_connected():
            self.logger.info(f"Connected to blockchain at {self.rpc_url}")
            self.logger.info(f"Contract address: {self.contract_address}")
            self.logger.info(f"Wallet address: {self.wallet_address}")
        else:
            self.logger.error("Failed to connect to blockchain")

    def _load_contract_abi(self) -> list:
        """Load the contract ABI from the JSON file"""
        try:
            # Try multiple possible paths for the ABI file
            possible_paths = [
                # From rival_agent/providers directory
                os.path.join(os.path.dirname(__file__), "..", "..", "abi.json"),
                # From rival_agent directory  
                os.path.join(os.path.dirname(__file__), "..", "abi.json"),
                # From current directory
                os.path.join(os.path.dirname(__file__), "abi.json"),
                # Absolute path fallback
                os.path.join(os.getcwd(), "abi.json")
            ]
            
            for abi_path in possible_paths:
                try:
                    with open(abi_path, 'r') as f:
                        abi = json.load(f)
                    self.logger.info(f"Contract ABI loaded from {abi_path}")
                    return abi
                except FileNotFoundError:
                    continue
            
            raise FileNotFoundError("ABI file not found in any expected location")
            
        except Exception as e:
            self.logger.error(f"Failed to load contract ABI: {e}")
            # Return minimal ABI for callAgent function if file not found
            return [
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "nftId", "type": "uint256"},
                        {"internalType": "string", "name": "inputCidFile", "type": "string"},
                        {"internalType": "string", "name": "inputData", "type": "string"}
                    ],
                    "name": "callAgent",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function"
                },
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
                        {"indexed": True, "internalType": "uint256", "name": "requestId", "type": "uint256"},
                        {"indexed": True, "internalType": "bytes", "name": "inputUri", "type": "bytes"},
                        {"indexed": False, "internalType": "uint256", "name": "nftId", "type": "uint256"}
                    ],
                    "name": "RequestSent",
                    "type": "event"
                },
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "internalType": "uint256", "name": "requestId", "type": "uint256"},
                        {"indexed": True, "internalType": "bytes", "name": "output", "type": "bytes"},
                        {"indexed": True, "internalType": "uint256", "name": "nftId", "type": "uint256"},
                        {"indexed": False, "internalType": "uint256", "name": "validationCount", "type": "uint256"},
                        {"indexed": False, "internalType": "uint256", "name": "totalValidator", "type": "uint256"}
                    ],
                    "name": "AgentResult",
                    "type": "event"
                }
            ]

    async def _submit_transaction(self, query: str) -> str:
        """Submit a callAgent transaction to the blockchain and return transaction hash"""
        
        if not self.account:
            # Mock mode for testing
            self.logger.warning("Running in mock mode - no real transaction submitted")
            return await self._submit_mock_transaction(query)
        
        try:
            # Prepare transaction parameters
            input_cid_file = ""  # Can be empty or IPFS hash if needed
            input_data = query  # The actual query data
            
            # Get agent price for payment calculation
            try:
                agent_info = self.contract.functions.agents(self.nft_id).call()
                agent_price = agent_info[4]  # price is at index 4
                self.logger.info(f"Agent price: {agent_price} wei")
            except Exception as e:
                self.logger.warning(f"Could not fetch agent price: {e}, using default")
                agent_price = 0  # Default to 0 if we can't fetch price
            
            # Build transaction
            transaction = self.contract.functions.callAgent(
                self.nft_id,
                input_cid_file,
                input_data
            ).build_transaction({
                'from': self.wallet_address,
                'value': agent_price,  # Send the required payment
                'gas': 500000,  # Estimate gas limit
                'gasPrice': self.w3.to_wei('20', 'gwei'),  # Gas price
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            # Submit transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            self.logger.info(f"Transaction submitted: {tx_hash_hex}")
            
            # Store pending request with transaction hash
            self.pending_requests[tx_hash_hex] = {
                "query": query,
                "status": "pending",
                "submitted_at": time.time(),
                "tx_hash": tx_hash_hex,
                "nft_id": self.nft_id
            }
            
            return tx_hash_hex
            
        except Exception as e:
            self.logger.error(f"Failed to submit transaction: {e}")
            raise Exception(f"Transaction submission failed: {e}")

    async def _submit_mock_transaction(self, query: str) -> str:
        """Submit a mock transaction for testing purposes"""
        mock_tx_hash = f"0x{''.join(['0'] * 40)}{int(time.time())}"
        
        self.pending_requests[mock_tx_hash] = {
            "query": query,
            "status": "pending",
            "submitted_at": time.time(),
            "tx_hash": mock_tx_hash,
            "nft_id": self.nft_id
        }
        
        # Schedule mock events
        asyncio.create_task(self._schedule_mock_events(mock_tx_hash))
        
        return mock_tx_hash

    async def _schedule_mock_events(self, tx_hash: str):
        """Schedule mock blockchain events for testing"""
        # Wait a bit then emit RequestSent event
        await asyncio.sleep(1.0)
        await self._emit_mock_event("RequestSent", tx_hash, {
            "sender": self.wallet_address,
            "requestId": int(tx_hash[-8:], 16),  # Use last 8 chars as request ID
            "inputUri": f"data:{self.pending_requests[tx_hash]['query']}",
            "nftId": self.nft_id
        })
        
        # Wait longer then emit AgentResult event
        await asyncio.sleep(3.0)
        mock_response = f"Based on your query '{self.pending_requests[tx_hash]['query']}', here's my analysis and response from the Rival blockchain AI agent."
        await self._emit_mock_event("AgentResult", tx_hash, {
            "requestId": int(tx_hash[-8:], 16),
            "output": mock_response.encode('utf-8'),
            "nftId": self.nft_id,
            "validationCount": 1,
            "totalValidator": 1
        })

    async def _emit_mock_event(self, event_type: str, tx_hash: str, data: Dict[str, Any]):
        """Emit a mock blockchain event"""
        self.logger.info(f"Mock event emitted: {event_type} for tx {tx_hash[:10]}...")
        
        if event_type == "AgentResult" and tx_hash in self.pending_requests:
            # Update request status with response
            self.pending_requests[tx_hash]["status"] = "completed"
            self.pending_requests[tx_hash]["response"] = data["output"].decode('utf-8') if isinstance(data["output"], bytes) else str(data["output"])

    async def _wait_for_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """Wait for transaction receipt and extract request ID"""
        if not self.account:
            # In mock mode, return immediately
            return {"status": 1, "logs": []}
        
        try:
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                self.logger.info(f"Transaction {tx_hash} confirmed")
                return receipt
            else:
                self.logger.error(f"Transaction {tx_hash} failed")
                return None
                
        except Exception as e:
            self.logger.error(f"Error waiting for transaction receipt: {e}")
            return None

    async def _listen_for_agent_result(self, tx_hash: str, request_id: Optional[int] = None) -> str:
        """Listen for AgentResult event and return the output"""
        if not self.account:
            # Mock mode - wait for mock events
            return await self._wait_for_mock_result(tx_hash)
        
        try:
            start_time = time.time()
            latest_block = self.w3.eth.block_number
            
            while time.time() - start_time < self.max_wait_time:
                # Get new blocks
                current_block = self.w3.eth.block_number
                
                if current_block > latest_block:
                    # Check for AgentResult events in new blocks
                    from_block = latest_block + 1
                    to_block = current_block
                    
                    try:
                        event_filter = self.contract.events.AgentResult.create_filter(
                            fromBlock=from_block,
                            toBlock=to_block
                        )
                        
                        events = event_filter.get_all_entries()
                        
                        for event in events:
                            event_request_id = event.args.requestId
                            event_nft_id = event.args.nftId
                            
                            # Check if this event matches our request
                            if event_nft_id == self.nft_id and (request_id is None or event_request_id == request_id):
                                output_bytes = event.args.output
                                output_str = output_bytes.decode('utf-8') if isinstance(output_bytes, bytes) else str(output_bytes)
                                
                                self.logger.info(f"Agent result received for request {event_request_id}")
                                return output_str
                                
                    except Exception as e:
                        self.logger.warning(f"Error checking for events: {e}")
                    
                    latest_block = current_block
                
                await asyncio.sleep(self.polling_interval)
            
            raise TimeoutError(f"No agent result received within {self.max_wait_time} seconds")
            
        except Exception as e:
            self.logger.error(f"Error listening for agent result: {e}")
            raise

    async def _wait_for_mock_result(self, tx_hash: str) -> str:
        """Wait for mock result in testing mode"""
        start_time = time.time()
        
        while time.time() - start_time < self.max_wait_time:
            if tx_hash in self.pending_requests:
                request_info = self.pending_requests[tx_hash]
                
                if request_info["status"] == "completed":
                    response = request_info.get("response", "")
                    del self.pending_requests[tx_hash]
                    return response
                elif request_info["status"] == "failed":
                    error_msg = request_info.get("error", "Unknown error")
                    del self.pending_requests[tx_hash]
                    raise Exception(f"Request failed: {error_msg}")
            
            await asyncio.sleep(self.polling_interval)
        
        # Timeout
        if tx_hash in self.pending_requests:
            del self.pending_requests[tx_hash]
        raise TimeoutError(f"Request timed out after {self.max_wait_time} seconds")

    async def query_stream(
        self,
        query: str
    ) -> AsyncIterator[str]:
        """Submit query to blockchain via callAgent and yield the response in chunks."""
        
        try:
            # Submit transaction
            tx_hash = await self._submit_transaction(query)
            self.logger.info(f"Transaction submitted: {tx_hash}")
            
            # Wait for transaction confirmation
            receipt = await self._wait_for_transaction_receipt(tx_hash)
            if not receipt:
                yield "Error: Transaction failed"
                return
            
            # Listen for agent result
            response = await self._listen_for_agent_result(tx_hash)
            
            # Simulate streaming by yielding chunks
            chunk_size = 20
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.1)  # Simulate streaming delay
                
        except Exception as e:
            self.logger.error(f"Error in query_stream: {e}")
            yield f"Error: {str(e)}"

    async def query(
        self,
        query: str
    ) -> str:
        """Submit query to blockchain via callAgent and return the complete response."""
        
        try:
            # Submit transaction
            tx_hash = await self._submit_transaction(query)
            self.logger.info(f"Transaction submitted: {tx_hash}")
            
            # Wait for transaction confirmation
            receipt = await self._wait_for_transaction_receipt(tx_hash)
            if not receipt:
                return "Error: Transaction failed"
            
            # Listen for agent result and return complete response
            response = await self._listen_for_agent_result(tx_hash)
            return response
            
        except Exception as e:
            self.logger.error(f"Error in query: {e}")
            return f"Error: {str(e)}"

    def get_pending_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending requests (keyed by transaction hash)"""
        return self.pending_requests.copy()

    async def cancel_request(self, tx_hash: str) -> bool:
        """Cancel a pending request"""
        if tx_hash in self.pending_requests:
            self.pending_requests[tx_hash]["status"] = "cancelled"
            del self.pending_requests[tx_hash]
            self.logger.info(f"Request {tx_hash} cancelled")
            return True
        return False

    def get_connection_status(self) -> Dict[str, Any]:
        """Get blockchain connection status"""
        return {
            "connected": self.w3.is_connected() if hasattr(self, 'w3') else False,
            "rpc_url": self.rpc_url,
            "contract_address": self.contract_address,
            "wallet_address": self.wallet_address,
            "nft_id": self.nft_id,
            "chain_id": self.w3.eth.chain_id if hasattr(self, 'w3') and self.w3.is_connected() else None
        }
