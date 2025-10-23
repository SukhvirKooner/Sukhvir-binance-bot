"""OCO (One-Cancels-the-Other) order implementation."""

from typing import Dict, Any, Optional
from binance.exceptions import BinanceAPIException

from ...binance_client import BinanceClient
from ...models import OrderResponse, SymbolInfo
from ...validators import validate_order_request, ValidationError
from ...utils.logger import logger


class OCOOrder:
    """OCO (One-Cancels-the-Other) order implementation."""
    
    def __init__(self, client: BinanceClient):
        """
        Initialize OCO order handler.
        
        Args:
            client: Binance client instance
        """
        self.client = client
    
    def place_oco_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        stop_limit_price: Optional[float] = None,
        stop_limit_time_in_force: str = "GTC",
        client_order_id: Optional[str] = None,
        symbol_info: Optional[SymbolInfo] = None
    ) -> OrderResponse:
        """
        Place an OCO order.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY or SELL)
            quantity: Order quantity
            price: Limit price (take profit)
            stop_price: Stop price (stop loss trigger)
            stop_limit_price: Stop limit price (if None, uses stop_price)
            stop_limit_time_in_force: Time in force for stop limit order
            client_order_id: Optional client order ID
            symbol_info: Symbol information for validation
            
        Returns:
            OrderResponse: Order response
            
        Raises:
            ValidationError: If validation fails
            BinanceAPIException: If order placement fails
        """
        try:
            # Use stop_price as stop_limit_price if not provided
            if stop_limit_price is None:
                stop_limit_price = stop_price
            
            logger.info(
                "oco_order",
                "placing_oco_order",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                stop_limit_price=stop_limit_price,
                stop_limit_time_in_force=stop_limit_time_in_force
            )
            
            # Validate basic parameters
            if side.upper() not in ["BUY", "SELL"]:
                raise ValidationError(f"Invalid side for OCO order: {side}")
            
            # For OCO orders, we need to use the futures_create_oco_order method
            # This is a more complex order type that combines a limit order with a stop order
            
            order_params = {
                "symbol": symbol,
                "side": side.upper(),
                "quantity": quantity,
                "price": price,
                "stopPrice": stop_price,
                "stopLimitPrice": stop_limit_price,
                "stopLimitTimeInForce": stop_limit_time_in_force,
            }
            
            if client_order_id:
                order_params["newClientOrderId"] = client_order_id
            
            # Place OCO order
            response = self.client.client.futures_create_oco_order(**order_params)
            
            logger.info(
                "oco_order",
                "oco_order_placed",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                response=response
            )
            
            # Convert response to OrderResponse format
            # OCO orders return a different structure, so we adapt it
            order_response = OrderResponse(
                order_id=response.get('orderListId', 0),
                symbol=symbol,
                status=response.get('listOrderStatus', 'UNKNOWN'),
                side=side.upper(),
                order_type="OCO",
                quantity=str(quantity),
                price=str(price),
                stop_price=str(stop_price),
                time_in_force=stop_limit_time_in_force,
                executed_qty="0",
                avg_price=None,
                client_order_id=client_order_id,
                transact_time=response.get('transactionTime', 0)
            )
            
            return order_response
            
        except ValidationError as e:
            logger.error(
                "oco_order",
                "oco_order_validation_failed",
                error=str(e),
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price
            )
            raise
        except BinanceAPIException as e:
            logger.error(
                "oco_order",
                "oco_order_placement_failed",
                error_code=e.code,
                error_message=e.message,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price
            )
            raise
        except Exception as e:
            logger.error(
                "oco_order",
                "unexpected_oco_order_error",
                error=str(e),
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price
            )
            raise
    
    def place_buy_oco(
        self,
        symbol: str,
        quantity: float,
        take_profit_price: float,
        stop_loss_price: float,
        stop_limit_price: Optional[float] = None,
        stop_limit_time_in_force: str = "GTC",
        client_order_id: Optional[str] = None,
        symbol_info: Optional[SymbolInfo] = None
    ) -> OrderResponse:
        """
        Place a buy OCO order (take profit + stop loss).
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss trigger price
            stop_limit_price: Stop limit execution price
            stop_limit_time_in_force: Time in force for stop limit order
            client_order_id: Optional client order ID
            symbol_info: Symbol information for validation
            
        Returns:
            OrderResponse: Order response
        """
        return self.place_oco_order(
            symbol=symbol,
            side="BUY",
            quantity=quantity,
            price=take_profit_price,
            stop_price=stop_loss_price,
            stop_limit_price=stop_limit_price,
            stop_limit_time_in_force=stop_limit_time_in_force,
            client_order_id=client_order_id,
            symbol_info=symbol_info
        )
    
    def place_sell_oco(
        self,
        symbol: str,
        quantity: float,
        take_profit_price: float,
        stop_loss_price: float,
        stop_limit_price: Optional[float] = None,
        stop_limit_time_in_force: str = "GTC",
        client_order_id: Optional[str] = None,
        symbol_info: Optional[SymbolInfo] = None
    ) -> OrderResponse:
        """
        Place a sell OCO order (take profit + stop loss).
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            take_profit_price: Take profit limit price
            stop_loss_price: Stop loss trigger price
            stop_limit_price: Stop limit execution price
            stop_limit_time_in_force: Time in force for stop limit order
            client_order_id: Optional client order ID
            symbol_info: Symbol information for validation
            
        Returns:
            OrderResponse: Order response
        """
        return self.place_oco_order(
            symbol=symbol,
            side="SELL",
            quantity=quantity,
            price=take_profit_price,
            stop_price=stop_loss_price,
            stop_limit_price=stop_limit_price,
            stop_limit_time_in_force=stop_limit_time_in_force,
            client_order_id=client_order_id,
            symbol_info=symbol_info
        )
