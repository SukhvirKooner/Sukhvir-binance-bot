"""Grid trading order implementation."""

import time
from typing import Dict, Any, Optional, List, Tuple
from binance.exceptions import BinanceAPIException

from ...binance_client import BinanceClient
from ...models import OrderResponse, SymbolInfo
from ...validators import validate_order_request, ValidationError
from ...utils.logger import logger


class GridOrder:
    """Grid trading order implementation."""
    
    def __init__(self, client: BinanceClient):
        """
        Initialize grid order handler.
        
        Args:
            client: Binance client instance
        """
        self.client = client
    
    def create_grid(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        price_range: Tuple[float, float],
        num_levels: int,
        order_type: str = "LIMIT",
        time_in_force: str = "GTC",
        symbol_info: Optional[SymbolInfo] = None
    ) -> List[OrderResponse]:
        """
        Create a grid of orders within a price range.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY or SELL)
            total_quantity: Total quantity to distribute across grid
            price_range: Tuple of (min_price, max_price)
            num_levels: Number of grid levels
            order_type: Type of orders to place (LIMIT or MARKET)
            time_in_force: Time in force for LIMIT orders
            symbol_info: Symbol information for validation
            
        Returns:
            List[OrderResponse]: List of order responses
            
        Raises:
            ValidationError: If validation fails
            BinanceAPIException: If order placement fails
        """
        try:
            min_price, max_price = price_range
            
            logger.info(
                "grid_order",
                "creating_grid",
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                price_range=price_range,
                num_levels=num_levels,
                order_type=order_type
            )
            
            # Validate parameters
            if min_price >= max_price:
                raise ValidationError("Min price must be less than max price")
            
            if num_levels <= 0:
                raise ValidationError("Number of levels must be positive")
            
            if total_quantity <= 0:
                raise ValidationError("Total quantity must be positive")
            
            if order_type == "MARKET":
                raise ValidationError("Grid orders must use LIMIT orders")
            
            # Calculate grid parameters
            price_step = (max_price - min_price) / (num_levels - 1)
            quantity_per_level = total_quantity / num_levels
            
            logger.info(
                "grid_order",
                "grid_parameters_calculated",
                price_step=price_step,
                quantity_per_level=quantity_per_level
            )
            
            order_responses = []
            
            for i in range(num_levels):
                try:
                    # Calculate price for this level
                    if side.upper() == "BUY":
                        # For buy grid, start from min_price and go up
                        price = min_price + (i * price_step)
                    else:  # SELL
                        # For sell grid, start from max_price and go down
                        price = max_price - (i * price_step)
                    
                    client_order_id = f"GRID_{symbol}_{int(time.time())}_{i}"
                    
                    # Place limit order
                    from ...orders.limit_orders import LimitOrder
                    limit_order = LimitOrder(self.client)
                    response = limit_order.place_order(
                        symbol=symbol,
                        side=side,
                        quantity=quantity_per_level,
                        price=price,
                        time_in_force=time_in_force,
                        client_order_id=client_order_id,
                        symbol_info=symbol_info
                    )
                    
                    order_responses.append(response)
                    
                    logger.info(
                        "grid_order",
                        "grid_order_placed",
                        level=i + 1,
                        total_levels=num_levels,
                        price=price,
                        quantity=quantity_per_level,
                        order_id=response.order_id,
                        status=response.status
                    )
                    
                    # Small delay between orders to avoid rate limiting
                    time.sleep(0.1)
                
                except Exception as e:
                    logger.error(
                        "grid_order",
                        "grid_order_failed",
                        level=i + 1,
                        total_levels=num_levels,
                        price=price,
                        error=str(e)
                    )
                    # Continue with remaining orders
                    continue
            
            total_placed = len(order_responses)
            total_quantity_placed = sum(float(r.quantity) for r in order_responses)
            
            logger.info(
                "grid_order",
                "grid_creation_completed",
                total_levels_placed=total_placed,
                total_levels_requested=num_levels,
                total_quantity_placed=total_quantity_placed,
                total_quantity_requested=total_quantity,
                placement_ratio=total_placed / num_levels if num_levels > 0 else 0
            )
            
            return order_responses
            
        except ValidationError as e:
            logger.error(
                "grid_order",
                "grid_validation_failed",
                error=str(e),
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                price_range=price_range,
                num_levels=num_levels
            )
            raise
        except Exception as e:
            logger.error(
                "grid_order",
                "unexpected_grid_error",
                error=str(e),
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                price_range=price_range,
                num_levels=num_levels
            )
            raise
    
    def create_buy_grid(
        self,
        symbol: str,
        total_quantity: float,
        min_price: float,
        max_price: float,
        num_levels: int,
        time_in_force: str = "GTC",
        symbol_info: Optional[SymbolInfo] = None
    ) -> List[OrderResponse]:
        """
        Create a buy grid (buy low, sell high strategy).
        
        Args:
            symbol: Trading symbol
            total_quantity: Total quantity to distribute across grid
            min_price: Minimum price for grid
            max_price: Maximum price for grid
            num_levels: Number of grid levels
            time_in_force: Time in force for orders
            symbol_info: Symbol information for validation
            
        Returns:
            List[OrderResponse]: List of order responses
        """
        return self.create_grid(
            symbol=symbol,
            side="BUY",
            total_quantity=total_quantity,
            price_range=(min_price, max_price),
            num_levels=num_levels,
            time_in_force=time_in_force,
            symbol_info=symbol_info
        )
    
    def create_sell_grid(
        self,
        symbol: str,
        total_quantity: float,
        min_price: float,
        max_price: float,
        num_levels: int,
        time_in_force: str = "GTC",
        symbol_info: Optional[SymbolInfo] = None
    ) -> List[OrderResponse]:
        """
        Create a sell grid (sell high, buy low strategy).
        
        Args:
            symbol: Trading symbol
            total_quantity: Total quantity to distribute across grid
            min_price: Minimum price for grid
            max_price: Maximum price for grid
            num_levels: Number of grid levels
            time_in_force: Time in force for orders
            symbol_info: Symbol information for validation
            
        Returns:
            List[OrderResponse]: List of order responses
        """
        return self.create_grid(
            symbol=symbol,
            side="SELL",
            total_quantity=total_quantity,
            price_range=(min_price, max_price),
            num_levels=num_levels,
            time_in_force=time_in_force,
            symbol_info=symbol_info
        )
    
    def simulate_grid(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        price_range: Tuple[float, float],
        num_levels: int
    ) -> Dict[str, Any]:
        """
        Simulate a grid order without placing actual orders.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY or SELL)
            total_quantity: Total quantity to distribute across grid
            price_range: Tuple of (min_price, max_price)
            num_levels: Number of grid levels
            
        Returns:
            Dict: Simulation results
        """
        try:
            min_price, max_price = price_range
            
            logger.info(
                "grid_order",
                "simulating_grid",
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                price_range=price_range,
                num_levels=num_levels
            )
            
            # Calculate grid parameters
            price_step = (max_price - min_price) / (num_levels - 1)
            quantity_per_level = total_quantity / num_levels
            
            simulation = {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "price_range": price_range,
                "num_levels": num_levels,
                "price_step": price_step,
                "quantity_per_level": quantity_per_level,
                "levels": []
            }
            
            # Generate grid levels
            for i in range(num_levels):
                if side.upper() == "BUY":
                    price = min_price + (i * price_step)
                else:  # SELL
                    price = max_price - (i * price_step)
                
                level = {
                    "level": i + 1,
                    "price": price,
                    "quantity": quantity_per_level,
                    "client_order_id": f"GRID_{symbol}_{int(time.time())}_{i}"
                }
                simulation["levels"].append(level)
            
            logger.info(
                "grid_order",
                "grid_simulation_completed",
                num_levels=num_levels,
                total_quantity=total_quantity
            )
            
            return simulation
            
        except Exception as e:
            logger.error(
                "grid_order",
                "grid_simulation_failed",
                error=str(e),
                symbol=symbol
            )
            raise
