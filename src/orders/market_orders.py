"""Market order implementation."""

from typing import Dict, Any, Optional
from binance.exceptions import BinanceAPIException

from ..binance_client import BinanceClient
from ..models import OrderResponse, SymbolInfo
from ..validators import validate_order_request, ValidationError
from ..utils.logger import logger


class MarketOrder:
    """Market order implementation."""
    
    def __init__(self, client: BinanceClient):
        """
        Initialize market order handler.
        
        Args:
            client: Binance client instance
        """
        self.client = client
    
    def place_buy_order(
        self,
        symbol: str,
        quantity: float,
        client_order_id: Optional[str] = None,
        symbol_info: Optional[SymbolInfo] = None
    ) -> OrderResponse:
        """
        Place a market buy order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            client_order_id: Optional client order ID
            symbol_info: Symbol information for validation
            
        Returns:
            OrderResponse: Order response
            
        Raises:
            ValidationError: If validation fails
            BinanceAPIException: If order placement fails
        """
        try:
            logger.info(
                "market_order",
                "placing_buy_order",
                symbol=symbol,
                quantity=quantity
            )
            
            # Validate order request
            order_params = validate_order_request(
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=quantity,
                client_order_id=client_order_id,
                symbol_info=symbol_info
            )
            
            # Place order
            response = self.client.place_order(order_params)
            
            logger.info(
                "market_order",
                "buy_order_placed",
                order_id=response.order_id,
                symbol=symbol,
                quantity=quantity,
                executed_qty=response.executed_qty,
                avg_price=response.avg_price
            )
            
            return response
            
        except ValidationError as e:
            logger.error(
                "market_order",
                "buy_order_validation_failed",
                error=str(e),
                symbol=symbol,
                quantity=quantity
            )
            raise
        except BinanceAPIException as e:
            logger.error(
                "market_order",
                "buy_order_placement_failed",
                error_code=e.code,
                error_message=e.message,
                symbol=symbol,
                quantity=quantity
            )
            raise
        except Exception as e:
            logger.error(
                "market_order",
                "unexpected_buy_order_error",
                error=str(e),
                symbol=symbol,
                quantity=quantity
            )
            raise
    
    def place_sell_order(
        self,
        symbol: str,
        quantity: float,
        client_order_id: Optional[str] = None,
        symbol_info: Optional[SymbolInfo] = None
    ) -> OrderResponse:
        """
        Place a market sell order.
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            client_order_id: Optional client order ID
            symbol_info: Symbol information for validation
            
        Returns:
            OrderResponse: Order response
            
        Raises:
            ValidationError: If validation fails
            BinanceAPIException: If order placement fails
        """
        try:
            logger.info(
                "market_order",
                "placing_sell_order",
                symbol=symbol,
                quantity=quantity
            )
            
            # Validate order request
            order_params = validate_order_request(
                symbol=symbol,
                side="SELL",
                order_type="MARKET",
                quantity=quantity,
                client_order_id=client_order_id,
                symbol_info=symbol_info
            )
            
            # Place order
            response = self.client.place_order(order_params)
            
            logger.info(
                "market_order",
                "sell_order_placed",
                order_id=response.order_id,
                symbol=symbol,
                quantity=quantity,
                executed_qty=response.executed_qty,
                avg_price=response.avg_price
            )
            
            return response
            
        except ValidationError as e:
            logger.error(
                "market_order",
                "sell_order_validation_failed",
                error=str(e),
                symbol=symbol,
                quantity=quantity
            )
            raise
        except BinanceAPIException as e:
            logger.error(
                "market_order",
                "sell_order_placement_failed",
                error_code=e.code,
                error_message=e.message,
                symbol=symbol,
                quantity=quantity
            )
            raise
        except Exception as e:
            logger.error(
                "market_order",
                "unexpected_sell_order_error",
                error=str(e),
                symbol=symbol,
                quantity=quantity
            )
            raise
    
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        client_order_id: Optional[str] = None,
        symbol_info: Optional[SymbolInfo] = None
    ) -> OrderResponse:
        """
        Place a market order (buy or sell).
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY or SELL)
            quantity: Order quantity
            client_order_id: Optional client order ID
            symbol_info: Symbol information for validation
            
        Returns:
            OrderResponse: Order response
            
        Raises:
            ValidationError: If validation fails
            BinanceAPIException: If order placement fails
        """
        if side.upper() == "BUY":
            return self.place_buy_order(
                symbol=symbol,
                quantity=quantity,
                client_order_id=client_order_id,
                symbol_info=symbol_info
            )
        elif side.upper() == "SELL":
            return self.place_sell_order(
                symbol=symbol,
                quantity=quantity,
                client_order_id=client_order_id,
                symbol_info=symbol_info
            )
        else:
            raise ValidationError(f"Invalid side for market order: {side}")
