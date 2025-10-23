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
            
            # Binance Futures doesn't support OCO orders directly
            # We implement OCO functionality by placing separate limit and stop orders
            # The limit order (take profit) and stop order (stop loss) will be placed separately
            
            # First, place the limit order (take profit)
            limit_order_params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": "LIMIT",
                "quantity": quantity,
                "price": price,
                "timeInForce": "GTC"
            }
            
            if client_order_id:
                limit_order_params["newClientOrderId"] = f"{client_order_id}_limit"
            
            # Place limit order
            limit_response = self.client.client.futures_create_order(**limit_order_params)
            
            # Then, place the stop order (stop loss)
            stop_order_params = {
                "symbol": symbol,
                "side": "SELL" if side.upper() == "BUY" else "BUY",  # Opposite side for stop loss
                "type": "STOP_MARKET",
                "quantity": quantity,
                "stopPrice": stop_price
            }
            
            if client_order_id:
                stop_order_params["newClientOrderId"] = f"{client_order_id}_stop"
            
            # Place stop order
            stop_response = self.client.client.futures_create_order(**stop_order_params)
            
            # Combine responses for OCO-like behavior
            response = {
                "orderListId": f"oco_{limit_response.get('orderId', 0)}_{stop_response.get('orderId', 0)}",
                "listOrderStatus": "EXECUTING",
                "transactionTime": limit_response.get('updateTime', 0),
                "limitOrder": limit_response,
                "stopOrder": stop_response
            }
            
            logger.info(
                "oco_order",
                "oco_order_placed",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                limit_order_id=limit_response.get('orderId'),
                stop_order_id=stop_response.get('orderId'),
                response=response
            )
            
            # Convert response to OrderResponse format
            # OCO orders are implemented as separate orders, so we adapt the response
            order_response = OrderResponse(
                order_id=limit_response.get('orderId', 0),  # Use limit order ID as primary
                symbol=symbol,
                status=limit_response.get('status', 'UNKNOWN'),
                side=side.upper(),
                order_type="OCO",
                quantity=str(quantity),
                price=str(price),
                stop_price=str(stop_price),
                time_in_force="GTC",
                executed_qty=limit_response.get('executedQty', "0"),
                avg_price=limit_response.get('avgPrice'),
                client_order_id=client_order_id,
                transact_time=limit_response.get('updateTime', 0)
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
