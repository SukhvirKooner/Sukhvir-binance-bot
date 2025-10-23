"""Binance client wrapper with retry logic and error handling."""

from typing import Dict, Any, Optional, List
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import requests

from .config import config
from .models import OrderResponse, OrderStatus, ExchangeInfo, SymbolInfo
from .utils.logger import logger
from .utils.retry import retry_with_backoff


class BinanceClient:
    """Binance client wrapper with enhanced error handling and logging."""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize Binance client.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize Binance client
        self.client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        
        # Override base URL for testnet
        if testnet:
            self.client.API_URL = config.BINANCE_TESTNET_BASE_URL
        
        logger.info(
            "binance_client",
            "client_initialized",
            testnet=testnet,
            base_url=self.client.API_URL
        )
    
    @retry_with_backoff(max_retries=config.MAX_RETRIES, base_delay=config.RETRY_DELAY)
    def place_order(self, order_params: Dict[str, Any]) -> OrderResponse:
        """
        Place an order on Binance.
        
        Args:
            order_params: Order parameters
            
        Returns:
            OrderResponse: Order response from Binance
            
        Raises:
            BinanceAPIException: If API call fails
        """
        try:
            logger.info(
                "binance_client",
                "placing_order",
                request=order_params
            )
            
            # Place order using Binance client
            response = self.client.futures_create_order(**order_params)
            
            logger.info(
                "binance_client",
                "order_placed",
                response=response
            )
            
            return OrderResponse(**response)
            
        except BinanceAPIException as e:
            logger.error(
                "binance_client",
                "order_placement_failed",
                error_code=e.code,
                error_message=e.message,
                request=order_params
            )
            raise
        except Exception as e:
            logger.error(
                "binance_client",
                "unexpected_order_error",
                error=str(e),
                request=order_params
            )
            raise BinanceAPIException(f"Unexpected error: {str(e)}")
    
    @retry_with_backoff(max_retries=config.MAX_RETRIES, base_delay=config.RETRY_DELAY)
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            
        Returns:
            Dict: Cancellation response
            
        Raises:
            BinanceAPIException: If API call fails
        """
        try:
            logger.info(
                "binance_client",
                "cancelling_order",
                symbol=symbol,
                order_id=order_id
            )
            
            response = self.client.futures_cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            
            logger.info(
                "binance_client",
                "order_cancelled",
                response=response
            )
            
            return response
            
        except BinanceAPIException as e:
            logger.error(
                "binance_client",
                "order_cancellation_failed",
                error_code=e.code,
                error_message=e.message,
                symbol=symbol,
                order_id=order_id
            )
            raise
        except Exception as e:
            logger.error(
                "binance_client",
                "unexpected_cancellation_error",
                error=str(e),
                symbol=symbol,
                order_id=order_id
            )
            raise BinanceAPIException(f"Unexpected error: {str(e)}")
    
    @retry_with_backoff(max_retries=config.MAX_RETRIES, base_delay=config.RETRY_DELAY)
    def get_order(self, symbol: str, order_id: int) -> OrderStatus:
        """
        Get order status.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID
            
        Returns:
            OrderStatus: Order status information
            
        Raises:
            BinanceAPIException: If API call fails
        """
        try:
            logger.info(
                "binance_client",
                "querying_order",
                symbol=symbol,
                order_id=order_id
            )
            
            response = self.client.futures_get_order(
                symbol=symbol,
                orderId=order_id
            )
            
            logger.info(
                "binance_client",
                "order_queried",
                response=response
            )
            
            return OrderStatus(**response)
            
        except BinanceAPIException as e:
            logger.error(
                "binance_client",
                "order_query_failed",
                error_code=e.code,
                error_message=e.message,
                symbol=symbol,
                order_id=order_id
            )
            raise
        except Exception as e:
            logger.error(
                "binance_client",
                "unexpected_query_error",
                error=str(e),
                symbol=symbol,
                order_id=order_id
            )
            raise BinanceAPIException(f"Unexpected error: {str(e)}")
    
    @retry_with_backoff(max_retries=config.MAX_RETRIES, base_delay=config.RETRY_DELAY)
    def get_exchange_info(self) -> ExchangeInfo:
        """
        Get exchange information.
        
        Returns:
            ExchangeInfo: Exchange information
            
        Raises:
            BinanceAPIException: If API call fails
        """
        try:
            logger.info(
                "binance_client",
                "fetching_exchange_info"
            )
            
            response = self.client.futures_exchange_info()
            
            logger.info(
                "binance_client",
                "exchange_info_fetched",
                symbol_count=len(response.get('symbols', []))
            )
            
            return ExchangeInfo(**response)
            
        except BinanceAPIException as e:
            logger.error(
                "binance_client",
                "exchange_info_fetch_failed",
                error_code=e.code,
                error_message=e.message
            )
            raise
        except Exception as e:
            logger.error(
                "binance_client",
                "unexpected_exchange_info_error",
                error=str(e)
            )
            raise BinanceAPIException(f"Unexpected error: {str(e)}")
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get information for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            SymbolInfo: Symbol information or None if not found
            
        Raises:
            BinanceAPIException: If API call fails
        """
        try:
            exchange_info = self.get_exchange_info()
            
            for symbol_data in exchange_info.symbols:
                if symbol_data['symbol'] == symbol:
                    return SymbolInfo(**symbol_data)
            
            logger.warning(
                "binance_client",
                "symbol_not_found",
                symbol=symbol
            )
            return None
            
        except Exception as e:
            logger.error(
                "binance_client",
                "symbol_info_fetch_failed",
                error=str(e),
                symbol=symbol
            )
            raise
    
    @retry_with_backoff(max_retries=config.MAX_RETRIES, base_delay=config.RETRY_DELAY)
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Dict: Account information
            
        Raises:
            BinanceAPIException: If API call fails
        """
        try:
            logger.info(
                "binance_client",
                "fetching_account_info"
            )
            
            response = self.client.futures_account()
            
            logger.info(
                "binance_client",
                "account_info_fetched"
            )
            
            return response
            
        except BinanceAPIException as e:
            logger.error(
                "binance_client",
                "account_info_fetch_failed",
                error_code=e.code,
                error_message=e.message
            )
            raise
        except Exception as e:
            logger.error(
                "binance_client",
                "unexpected_account_info_error",
                error=str(e)
            )
            raise BinanceAPIException(f"Unexpected error: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Binance API.
        
        Returns:
            bool: True if connection is successful
            
        Raises:
            BinanceAPIException: If connection fails
        """
        try:
            logger.info(
                "binance_client",
                "testing_connection"
            )
            
            # Test with a simple API call
            self.client.futures_ping()
            
            logger.info(
                "binance_client",
                "connection_test_successful"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "binance_client",
                "connection_test_failed",
                error=str(e)
            )
            raise
