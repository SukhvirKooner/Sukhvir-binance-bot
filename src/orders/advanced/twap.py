"""TWAP (Time-Weighted Average Price) order implementation."""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from binance.exceptions import BinanceAPIException

from ...binance_client import BinanceClient
from ...models import OrderResponse, SymbolInfo
from ...validators import validate_order_request, ValidationError
from ...utils.logger import logger


class TWAPOrder:
    """TWAP (Time-Weighted Average Price) order implementation."""
    
    def __init__(self, client: BinanceClient):
        """
        Initialize TWAP order handler.
        
        Args:
            client: Binance client instance
        """
        self.client = client
    
    def execute_twap(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        duration_minutes: int,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        symbol_info: Optional[SymbolInfo] = None
    ) -> List[OrderResponse]:
        """
        Execute a TWAP order by splitting it into smaller chunks over time.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY or SELL)
            total_quantity: Total quantity to execute
            duration_minutes: Duration in minutes to spread the orders
            order_type: Type of orders to place (MARKET or LIMIT)
            price: Price for LIMIT orders (required if order_type is LIMIT)
            time_in_force: Time in force for LIMIT orders
            symbol_info: Symbol information for validation
            
        Returns:
            List[OrderResponse]: List of order responses
            
        Raises:
            ValidationError: If validation fails
            BinanceAPIException: If order placement fails
        """
        try:
            logger.info(
                "twap_order",
                "starting_twap_execution",
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                duration_minutes=duration_minutes,
                order_type=order_type
            )
            
            # Validate parameters
            if duration_minutes <= 0:
                raise ValidationError("Duration must be positive")
            
            if total_quantity <= 0:
                raise ValidationError("Total quantity must be positive")
            
            if order_type == "LIMIT" and price is None:
                raise ValidationError("Price is required for LIMIT orders")
            
            # Calculate number of orders and intervals
            # Use a reasonable number of orders (between 5 and 20)
            num_orders = min(max(5, duration_minutes // 2), 20)
            interval_seconds = (duration_minutes * 60) // num_orders
            quantity_per_order = total_quantity / num_orders
            
            logger.info(
                "twap_order",
                "twap_parameters_calculated",
                num_orders=num_orders,
                interval_seconds=interval_seconds,
                quantity_per_order=quantity_per_order
            )
            
            order_responses = []
            start_time = datetime.now()
            
            for i in range(num_orders):
                try:
                    # Calculate remaining time
                    elapsed_time = (datetime.now() - start_time).total_seconds()
                    remaining_time = (duration_minutes * 60) - elapsed_time
                    
                    if remaining_time <= 0:
                        logger.warning(
                            "twap_order",
                            "duration_exceeded",
                            order_index=i,
                            total_orders=num_orders
                        )
                        break
                    
                    # Place individual order
                    client_order_id = f"TWAP_{symbol}_{int(time.time())}_{i}"
                    
                    if order_type == "MARKET":
                        from ...orders.market_orders import MarketOrder
                        market_order = MarketOrder(self.client)
                        response = market_order.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=quantity_per_order,
                            client_order_id=client_order_id,
                            symbol_info=symbol_info
                        )
                    else:  # LIMIT
                        from ...orders.limit_orders import LimitOrder
                        limit_order = LimitOrder(self.client)
                        response = limit_order.place_order(
                            symbol=symbol,
                            side=side,
                            quantity=quantity_per_order,
                            price=price,
                            time_in_force=time_in_force,
                            client_order_id=client_order_id,
                            symbol_info=symbol_info
                        )
                    
                    order_responses.append(response)
                    
                    logger.info(
                        "twap_order",
                        "twap_order_placed",
                        order_index=i + 1,
                        total_orders=num_orders,
                        order_id=response.order_id,
                        quantity=quantity_per_order,
                        status=response.status
                    )
                    
                    # Wait for next interval (except for the last order)
                    if i < num_orders - 1:
                        time.sleep(interval_seconds)
                
                except Exception as e:
                    logger.error(
                        "twap_order",
                        "twap_order_failed",
                        order_index=i + 1,
                        total_orders=num_orders,
                        error=str(e)
                    )
                    # Continue with remaining orders
                    continue
            
            total_executed = sum(float(r.executed_qty) for r in order_responses)
            
            logger.info(
                "twap_order",
                "twap_execution_completed",
                total_orders_placed=len(order_responses),
                total_quantity_requested=total_quantity,
                total_quantity_executed=total_executed,
                execution_ratio=total_executed / total_quantity if total_quantity > 0 else 0
            )
            
            return order_responses
            
        except ValidationError as e:
            logger.error(
                "twap_order",
                "twap_validation_failed",
                error=str(e),
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                duration_minutes=duration_minutes
            )
            raise
        except Exception as e:
            logger.error(
                "twap_order",
                "unexpected_twap_error",
                error=str(e),
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                duration_minutes=duration_minutes
            )
            raise
    
    def simulate_twap(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        duration_minutes: int,
        order_type: str = "MARKET",
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Simulate a TWAP order without placing actual orders.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY or SELL)
            total_quantity: Total quantity to execute
            duration_minutes: Duration in minutes to spread the orders
            order_type: Type of orders to place (MARKET or LIMIT)
            price: Price for LIMIT orders
            
        Returns:
            Dict: Simulation results
        """
        try:
            logger.info(
                "twap_order",
                "simulating_twap",
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                duration_minutes=duration_minutes,
                order_type=order_type
            )
            
            # Calculate parameters
            num_orders = min(max(5, duration_minutes // 2), 20)
            interval_seconds = (duration_minutes * 60) // num_orders
            quantity_per_order = total_quantity / num_orders
            
            simulation = {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "duration_minutes": duration_minutes,
                "order_type": order_type,
                "num_orders": num_orders,
                "interval_seconds": interval_seconds,
                "quantity_per_order": quantity_per_order,
                "orders": []
            }
            
            # Generate order schedule
            for i in range(num_orders):
                order_time = i * interval_seconds
                order = {
                    "order_index": i + 1,
                    "time_offset_seconds": order_time,
                    "quantity": quantity_per_order,
                    "price": price if order_type == "LIMIT" else None,
                    "client_order_id": f"TWAP_{symbol}_{int(time.time())}_{i}"
                }
                simulation["orders"].append(order)
            
            logger.info(
                "twap_order",
                "twap_simulation_completed",
                num_orders=num_orders,
                total_quantity=total_quantity
            )
            
            return simulation
            
        except Exception as e:
            logger.error(
                "twap_order",
                "twap_simulation_failed",
                error=str(e),
                symbol=symbol
            )
            raise
