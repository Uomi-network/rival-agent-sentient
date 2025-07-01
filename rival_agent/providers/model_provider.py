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
from substrateinterface import SubstrateInterface

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
        self.logger.setLevel(logging.INFO)
        
        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        
        # Setup Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add middleware for POA chains if needed
        if not self.w3.is_connected():
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Setup Substrate interface for event handling
        try:
            # Convert HTTP URLs to WebSocket if needed
            substrate_url = self.rpc_url
            if substrate_url.startswith('http'):
                substrate_url = substrate_url.replace('http', 'ws')
                # if not substrate_url.endswith(':9944'):
                #     substrate_url = substrate_url.rstrip('/') + ':9944'
            
            self.substrate = SubstrateInterface(url=substrate_url)
            self.logger.info(f"Connected to Substrate chain: {self.substrate.chain}")
        except Exception as e:
            self.logger.warning(f"Could not connect to Substrate interface: {e}")
            self.substrate = None
        
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
            
            # Get dynamic gas price
            gas_price = await self._get_dynamic_gas_price()
            # Estimate gas limit
            try:
                gas_estimate = self.contract.functions.callAgent(
                    self.nft_id,
                    input_cid_file,
                    input_data
                ).estimate_gas({
                    'from': self.wallet_address,
                    'value': agent_price
                })
                # Add 20% buffer to gas estimate
                gas_limit = int(gas_estimate * 1.2)
                self.logger.info(f"Gas estimate: {gas_estimate}, using limit: {gas_limit}")
            except Exception as e:
                self.logger.warning(f"Could not estimate gas: {e}, using default")
                gas_limit = 500000  # Default fallback
            
            # Build transaction
            transaction = self.contract.functions.callAgent(
                self.nft_id,
                input_cid_file,
                input_data
            ).build_transaction({
                'from': self.wallet_address,
                'value': agent_price,  # Send the required payment
                'gas': gas_limit,  # Dynamic gas limit
                'gasPrice': gas_price,  # Dynamic gas price
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and submit transaction with retry logic for gas price issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Sign transaction
                    signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
                    
                    # Submit transaction
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    tx_hash_hex = tx_hash.hex()
                    
                    self.logger.info(f"Transaction submitted successfully: {tx_hash_hex}")
                    
                    # Store pending request with transaction hash
                    self.pending_requests[tx_hash_hex] = {
                        "query": query,
                        "status": "pending",
                        "submitted_at": time.time(),
                        "tx_hash": tx_hash_hex,
                        "nft_id": self.nft_id
                    }
                    
                    return tx_hash_hex
                    
                except Exception as retry_error:
                    error_str = str(retry_error)
                    if "gas price less than block base fee" in error_str or "underpriced" in error_str:
                        if attempt < max_retries - 1:
                            self.logger.warning(f"Gas price too low on attempt {attempt + 1}, retrying with higher price...")
                            # Increase gas price significantly for retry
                            gas_price = int(gas_price * 1.5)  # Increase by 50%
                            transaction['gasPrice'] = gas_price
                            await asyncio.sleep(1)  # Wait a bit before retry
                            continue
                        else:
                            self.logger.error(f"Failed after {max_retries} attempts with gas price issues")
                            raise Exception(f"Transaction failed after {max_retries} retries due to gas price: {retry_error}")
                    else:
                        # For non-gas-price errors, don't retry
                        raise retry_error
            
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
        request_id = int(tx_hash[-8:], 16)
        
        # Wait a bit then emit RequestAccepted event
        await asyncio.sleep(1.0)
        await self._emit_mock_event("RequestAccepted", tx_hash, {
            "requestId": request_id,
            "address": self.wallet_address,
            "nftId": self.nft_id
        })
        
        # Wait longer then emit NodeOutputReceived event
        await asyncio.sleep(3.0)
        mock_response = f"Based on your query '{self.pending_requests[tx_hash]['query']}', here's my analysis and response from the Rival blockchain AI agent."
        await self._emit_mock_event("NodeOutputReceived", tx_hash, {
            "requestId": request_id,
            "accountId": "FpXEL",
            "outputData": mock_response.encode('utf-8')
        })

    async def _emit_mock_event(self, event_type: str, tx_hash: str, data: Dict[str, Any]):
        """Emit a mock blockchain event"""
        self.logger.info(f"Mock event emitted: {event_type} for tx {tx_hash[:10]}...")
        
        if event_type == "NodeOutputReceived" and tx_hash in self.pending_requests:
            # Update request status with response
            self.pending_requests[tx_hash]["status"] = "completed"
            self.pending_requests[tx_hash]["response"] = data["output_data"].decode('utf-8') if isinstance(data["output_data"], bytes) else str(data["output_data"])

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
        """Listen for NodeOutputReceived event and return the output"""
        if not self.account:
            # Mock mode - wait for mock events
            return await self._wait_for_mock_result(tx_hash)
        
        event_type = 'NodeOutputReceived'
        
        try:
            start_time = time.time()
            latest_block = self.w3.eth.block_number
            
            while time.time() - start_time < self.max_wait_time:
                # Get new blocks
                current_block = self.w3.eth.block_number
                
                if current_block > latest_block:
                    # Check for AgentResult events in new blocks (real blockchain events)
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

                            self.logger.error(f"Checking event: {event.event} in block {event.blockNumber}")


                            
                            # Check if this event matches our request
                            if request_id is None or event_request_id == request_id and event.event == event_type:
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
            
            # Wait for RequestAccepted and get request ID
            request_id = await self._wait_for_request_accepted(tx_hash)
            if not request_id:
                yield "Error: Request not accepted"
                return
            
            # Listen for NodeOutputReceived
            if self.account:
                response = await self._listen_for_node_output(request_id)
            else:
                # Mock mode
                response = await self._wait_for_mock_result(tx_hash)
            
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
            
            # Wait for RequestAccepted and get request ID
            request_id = await self._wait_for_request_accepted(tx_hash)
            if not request_id:
                return "Error: Request not accepted"
            
            # Listen for NodeOutputReceived and return complete response
            if self.account:
                response = await self._listen_for_node_output(request_id)
            else:
                # Mock mode
                response = await self._wait_for_mock_result(tx_hash)
                
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

    async def _get_dynamic_gas_price(self) -> int:
        """Calculate dynamic gas price based on current network conditions"""
        try:
            # Try to get the current base fee (for EIP-1559 networks)
            try:
                latest_block = self.w3.eth.get_block('latest')
                if hasattr(latest_block, 'baseFeePerGas') and latest_block.baseFeePerGas:
                    # For EIP-1559 networks, use base fee + priority fee
                    base_fee = latest_block.baseFeePerGas
                    priority_fee = self.w3.to_wei('2', 'gwei')  # 2 Gwei priority fee
                    gas_price = base_fee + priority_fee
                    self.logger.info(f"Using EIP-1559 gas pricing: base_fee={base_fee}, priority_fee={priority_fee}, total={gas_price}")
                    return gas_price
            except Exception as e:
                self.logger.debug(f"EIP-1559 pricing not available: {e}")
            
            # Fallback to legacy gas price method
            try:
                current_gas_price = self.w3.eth.gas_price
                # Add 20% buffer to ensure transaction goes through
                buffered_gas_price = int(current_gas_price * 1.2)
                self.logger.info(f"Using legacy gas pricing: current={current_gas_price}, buffered={buffered_gas_price}")
                return buffered_gas_price
            except Exception as e:
                self.logger.warning(f"Could not fetch current gas price: {e}")
            
            # Final fallback to a higher fixed price
            fallback_price = self.w3.to_wei('50', 'gwei')  # 50 Gwei fallback
            self.logger.warning(f"Using fallback gas price: {fallback_price}")
            return fallback_price
            
        except Exception as e:
            self.logger.error(f"Error calculating gas price: {e}")
            # Use a safe fallback price
            return self.w3.to_wei('100', 'gwei')  # 100 Gwei emergency fallback

    async def _wait_for_request_accepted(self, tx_hash: str) -> Optional[int]:
        """Wait for RequestAccepted event and return request ID"""
        if not self.account:
            # Mock mode
            return int(tx_hash[-8:], 16)
        
        self.logger.error(f"Waiting for RequestAccepted event for transaction {tx_hash}...")
        try:
            start_time = time.time()
            latest_block = self.w3.eth.block_number - 5

            self.logger.error(f"Latest block: {latest_block}")
            
            while time.time() - start_time < 30.0:  # 30 second timeout for acceptance
                current_block = self.w3.eth.block_number
                
                if current_block >= latest_block:
                    # Look for RequestSent events (which was working fine)
                    from_block = latest_block + 1
                    to_block = current_block
                    
                    try:
                        event_filter = self.contract.events.RequestSent.create_filter(
                            fromBlock=from_block,
                            toBlock=to_block
                        )
                        
                        events = event_filter.get_all_entries()
                        
                        for event in events:
                            self.logger.error(f"Checking event: {event.event} in block {event.blockNumber}")
                            self.logger.error(f"Event.transactionHash: {event.transactionHash.hex()}")
                            self.logger.error(f"TX Hash: {tx_hash}")
                            # Check if this event is from our transaction
                            if event.transactionHash.hex() == tx_hash:
                                request_id = event.args.requestId
                                self.logger.error(f"Request accepted with ID: {request_id}")
                                return request_id
                                
                    except Exception as e:
                        self.logger.warning(f"Error checking for RequestSent events: {e}")
                    
                    latest_block = current_block
                
                await asyncio.sleep(1.0)
            
            self.logger.warning("No RequestAccepted event found within timeout")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for request acceptance: {e}")
            return None

    async def _listen_for_node_output(self, request_id: int) -> str:
        """Listen for NodeOutputReceived event using substrate-interface"""
        if not self.account:
            # This is handled by mock events
            return ""
    
        self.logger.error(f"Listening for NodeOutputReceived event with request_id {request_id}")
        
        if not self.substrate:
            self.logger.error("Substrate interface not available")
            raise Exception("Substrate interface not connected")
        
        try:
            start_time = time.time()
            # Get current block number using the correct method
            start_block_hash = self.substrate.get_chain_head()
            start_block = self.substrate.get_block_number(start_block_hash)
            
            while time.time() - start_time < self.max_wait_time:
                try:
                    # Get current block number
                    current_block_hash = self.substrate.get_chain_head()
                    current_block = self.substrate.get_block_number(current_block_hash)
                    
                    # Check new blocks for events
                    if current_block > start_block:
                        for block_num in range(start_block + 1, current_block + 1):
                            try:
                                # Get block hash
                                block_hash = self.substrate.get_block_hash(block_num)
                                
                                # Get all events in this block
                                events = self.substrate.get_events(block_hash)
                                
                                if events:
                                    self.logger.error(f"Found {len(events)} events in block {block_num}")
                                
                                for event in events:


                                    # Handle different possible event structures
                                    event_id = None
                                    event_data = None
                                    
                                    if hasattr(event, 'value'):
                                        if 'event_id' in event.value:
                                            event_id = event.value['event_id']
                                        elif 'name' in event.value:
                                            event_id = event.value['name']

                                        if 'attributes' in event.value:
                                            event_data = event.value['attributes']
                                        elif 'value' in event.value:
                                            event_data = event.value['value']
                                

                                    # Check if this is our target event
                                    if event_id == 'NodeOutputReceived':
                                        self.logger.error(f"Found NodeOutputReceived event in block {block_num}. Attributes: {event_data}")
                                        
                                        # Extract event attributes
                                        event_request_id = None
                                        output_data = None
                                        account_id = None
                                        
                                    
                                        # Handle direct dictionary access
                                        event_request_id = event_data.get('request_id')
                                        output_data = event_data.get('output_data')
                                        account_id = event_data.get('account_id')

                                        self.logger.error(f"Event attributes: requestId={event_request_id}, accountId={account_id}, outputData={output_data}")
                                        
                                        # If this matches our request, return the output
                                        if event_request_id == request_id and output_data is not None:
                                            self.logger.info(f"NodeOutputReceived event found for request {request_id}")
                                            
                                            # Decode the output data
                                            if isinstance(output_data, bytes):
                                                try:
                                                    decoded_output = output_data.decode('utf-8')
                                                    return decoded_output
                                                except UnicodeDecodeError:
                                                    # If it's not UTF-8, return as hex string
                                                    return output_data.hex()
                                            elif isinstance(output_data, str):
                                                return output_data
                                            else:
                                                return str(output_data)
                                
                            except Exception as block_error:
                                self.logger.warning(f"Error processing block {block_num}: {block_error}")
                                continue
                        
                        start_block = current_block
                
                except Exception as substrate_error:
                    self.logger.warning(f"Substrate error while checking for events: {substrate_error}")
                
                # Wait before checking again
                await asyncio.sleep(self.polling_interval)
            
            raise TimeoutError(f"No NodeOutputReceived event found for request {request_id} within {self.max_wait_time} seconds")
            
        except Exception as e:
            self.logger.error(f"Error listening for node output: {e}")
            raise
