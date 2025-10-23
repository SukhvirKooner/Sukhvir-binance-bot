"""Input validation functions for order parameters."""

import re
from typing import Optional, Dict, Any, List
from decimal import Decimal, ROUND_DOWN

from .config import config
from .models import SymbolInfo
from .utils.logger import logger


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading symbol to validate
        
    Returns:
        Validated symbol in uppercase
        
    Raises:
        ValidationError: If symbol format is invalid
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty")
    
    # Convert to uppercase and validate format
    symbol = symbol.upper().strip()
    
    if not re.match(config.SYMBOL_PATTERN, symbol):
        raise ValidationError(
            f"Invalid symbol format: {symbol}. "
            f"Symbol must be 6-12 uppercase alphanumeric characters (e.g., BTCUSDT)"
        )
    
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.
    
    Args:
        side: Order side to validate
        
    Returns:
        Validated side in uppercase
        
    Raises:
        ValidationError: If side is invalid
    """
    if not side:
        raise ValidationError("Order side cannot be empty")
    
    side = side.upper().strip()
    
    if side not in ["BUY", "SELL"]:
        raise ValidationError(f"Invalid order side: {side}. Must be BUY or SELL")
    
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.
    
    Args:
        order_type: Order type to validate
        
    Returns:
        Validated order type in uppercase
        
    Raises:
        ValidationError: If order type is invalid
    """
    if not order_type:
        raise ValidationError("Order type cannot be empty")
    
    order_type = order_type.upper().strip()
    
    valid_types = ["MARKET", "LIMIT", "STOP_LIMIT", "OCO", "TWAP", "GRID"]
    
    if order_type not in valid_types:
        raise ValidationError(
            f"Invalid order type: {order_type}. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    return order_type


def validate_quantity(quantity: float, symbol_info: Optional[SymbolInfo] = None) -> float:
    """
    Validate order quantity.
    
    Args:
        quantity: Quantity to validate
        symbol_info: Symbol information for precision validation
        
    Returns:
        Validated quantity
        
    Raises:
        ValidationError: If quantity is invalid
    """
    if quantity is None:
        raise ValidationError("Quantity cannot be empty")
    
    try:
        quantity = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid quantity: {quantity}. Must be a valid number")
    
    if quantity <= 0:
        raise ValidationError(f"Quantity must be positive: {quantity}")
    
    if quantity < config.MIN_QUANTITY:
        raise ValidationError(
            f"Quantity too small: {quantity}. Minimum: {config.MIN_QUANTITY}"
        )
    
    # Validate against symbol precision if available
    if symbol_info:
        # Get lot size filter
        lot_size_filter = None
        for filter_info in symbol_info.filters:
            if filter_info.get('filterType') == 'LOT_SIZE':
                lot_size_filter = filter_info
                break
        
        if lot_size_filter:
            min_qty = float(lot_size_filter.get('minQty', 0))
            max_qty = float(lot_size_filter.get('maxQty', float('inf')))
            step_size = float(lot_size_filter.get('stepSize', 0))
            
            if quantity < min_qty:
                raise ValidationError(
                    f"Quantity below minimum: {quantity}. Minimum: {min_qty}"
                )
            
            if quantity > max_qty:
                raise ValidationError(
                    f"Quantity above maximum: {quantity}. Maximum: {max_qty}"
                )
            
            # Validate step size
            if step_size > 0:
                # Use Decimal for precise calculations to avoid floating-point precision issues
                from decimal import Decimal, ROUND_DOWN
                quantity_decimal = Decimal(str(quantity))
                step_size_decimal = Decimal(str(step_size))
                
                # Calculate remainder using Decimal arithmetic
                remainder = quantity_decimal % step_size_decimal
                
                # Check if remainder is effectively zero (accounting for floating-point precision)
                if remainder != Decimal('0'):
                    # Round down to nearest valid step
                    valid_quantity = (quantity_decimal // step_size_decimal) * step_size_decimal
                    raise ValidationError(
                        f"Invalid quantity step: {quantity}. "
                        f"Must be multiple of {step_size}. "
                        f"Suggested: {float(valid_quantity)}"
                    )
    
    return quantity


def validate_price(price: Optional[float], symbol_info: Optional[SymbolInfo] = None) -> Optional[float]:
    """
    Validate order price.
    
    Args:
        price: Price to validate
        symbol_info: Symbol information for precision validation
        
    Returns:
        Validated price or None
        
    Raises:
        ValidationError: If price is invalid
    """
    if price is None:
        return None
    
    try:
        price = float(price)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid price: {price}. Must be a valid number")
    
    if price <= 0:
        raise ValidationError(f"Price must be positive: {price}")
    
    # Validate against symbol precision if available
    if symbol_info:
        # Get price filter
        price_filter = None
        for filter_info in symbol_info.filters:
            if filter_info.get('filterType') == 'PRICE_FILTER':
                price_filter = filter_info
                break
        
        if price_filter:
            min_price = float(price_filter.get('minPrice', 0))
            max_price = float(price_filter.get('maxPrice', float('inf')))
            tick_size = float(price_filter.get('tickSize', 0))
            
            if price < min_price:
                raise ValidationError(
                    f"Price below minimum: {price}. Minimum: {min_price}"
                )
            
            if price > max_price:
                raise ValidationError(
                    f"Price above maximum: {price}. Maximum: {max_price}"
                )
            
            # Validate tick size
            if tick_size > 0:
                # Use Decimal for precise calculations to avoid floating-point precision issues
                from decimal import Decimal, ROUND_DOWN
                price_decimal = Decimal(str(price))
                tick_size_decimal = Decimal(str(tick_size))
                
                # Calculate remainder using Decimal arithmetic
                remainder = price_decimal % tick_size_decimal
                
                # Check if remainder is effectively zero (accounting for floating-point precision)
                if remainder != Decimal('0'):
                    # Round down to nearest valid tick
                    valid_price = (price_decimal // tick_size_decimal) * tick_size_decimal
                    raise ValidationError(
                        f"Invalid price tick: {price}. "
                        f"Must be multiple of {tick_size}. "
                        f"Suggested: {float(valid_price)}"
                    )
    
    return price


def validate_time_in_force(time_in_force: Optional[str]) -> str:
    """
    Validate time in force.
    
    Args:
        time_in_force: Time in force to validate
        
    Returns:
        Validated time in force
        
    Raises:
        ValidationError: If time in force is invalid
    """
    if not time_in_force:
        return config.DEFAULT_TIME_IN_FORCE
    
    time_in_force = time_in_force.upper().strip()
    
    valid_tif = ["GTC", "IOC", "FOK"]
    
    if time_in_force not in valid_tif:
        raise ValidationError(
            f"Invalid time in force: {time_in_force}. "
            f"Must be one of: {', '.join(valid_tif)}"
        )
    
    return time_in_force


def validate_cross_field_constraints(
    order_type: str,
    price: Optional[float],
    stop_price: Optional[float],
    quantity: float
) -> None:
    """
    Validate cross-field constraints for order parameters.
    
    Args:
        order_type: Order type
        price: Order price
        stop_price: Stop price
        quantity: Order quantity
        
    Raises:
        ValidationError: If cross-field validation fails
    """
    order_type = order_type.upper()
    
    # LIMIT orders require price
    if order_type == "LIMIT" and price is None:
        raise ValidationError("LIMIT orders require a price")
    
    # STOP_LIMIT orders require both price and stop_price
    if order_type == "STOP_LIMIT":
        if price is None:
            raise ValidationError("STOP_LIMIT orders require a price")
        if stop_price is None:
            raise ValidationError("STOP_LIMIT orders require a stop_price")
    
    # OCO orders require price and stop_price
    if order_type == "OCO":
        if price is None:
            raise ValidationError("OCO orders require a price")
        if stop_price is None:
            raise ValidationError("OCO orders require a stop_price")
    
    # MARKET orders should not have price
    if order_type == "MARKET" and price is not None:
        raise ValidationError("MARKET orders should not have a price")


def validate_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
    time_in_force: Optional[str] = None,
    client_order_id: Optional[str] = None,
    symbol_info: Optional[SymbolInfo] = None
) -> Dict[str, Any]:
    """
    Validate complete order request.
    
    Args:
        symbol: Trading symbol
        side: Order side
        order_type: Order type
        quantity: Order quantity
        price: Order price
        stop_price: Stop price
        time_in_force: Time in force
        client_order_id: Client order ID
        symbol_info: Symbol information
        
    Returns:
        Validated order parameters as dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Validate individual fields
        validated_symbol = validate_symbol(symbol)
        validated_side = validate_side(side)
        validated_order_type = validate_order_type(order_type)
        validated_quantity = validate_quantity(quantity, symbol_info)
        validated_price = validate_price(price, symbol_info)
        validated_stop_price = validate_price(stop_price, symbol_info)
        validated_time_in_force = validate_time_in_force(time_in_force)
        
        # Validate cross-field constraints
        validate_cross_field_constraints(
            validated_order_type,
            validated_price,
            validated_stop_price,
            validated_quantity
        )
        
        # Map internal order types to Binance API order types
        binance_order_type = _map_to_binance_order_type(validated_order_type, validated_price, validated_stop_price)
        
        # Build validated order request
        order_request = {
            "symbol": validated_symbol,
            "side": validated_side,
            "type": binance_order_type,
            "quantity": validated_quantity,
        }
        
        # Only add timeInForce for non-MARKET orders
        if binance_order_type not in ["MARKET", "STOP_MARKET", "TAKE_PROFIT_MARKET", "TRAILING_STOP_MARKET"]:
            order_request["timeInForce"] = validated_time_in_force
        
        # Add optional fields
        if validated_price is not None:
            order_request["price"] = validated_price
        
        if validated_stop_price is not None:
            order_request["stopPrice"] = validated_stop_price
        
        if client_order_id:
            order_request["newClientOrderId"] = client_order_id
        
        logger.info(
            "validator",
            "order_request_validated",
            symbol=validated_symbol,
            side=validated_side,
            order_type=validated_order_type,
            binance_order_type=binance_order_type,
            quantity=validated_quantity
        )
        
        return order_request
        
    except ValidationError as e:
        logger.error(
            "validator",
            "validation_failed",
            error=str(e),
            symbol=symbol,
            side=side,
            order_type=order_type
        )
        raise
    except Exception as e:
        logger.error(
            "validator",
            "unexpected_validation_error",
            error=str(e),
            symbol=symbol
        )
        raise ValidationError(f"Unexpected validation error: {str(e)}")


def _map_to_binance_order_type(order_type: str, price: Optional[float], stop_price: Optional[float]) -> str:
    """
    Map internal order types to Binance API order types.
    
    Args:
        order_type: Internal order type
        price: Order price
        stop_price: Stop price
        
    Returns:
        Binance API order type
    """
    order_type = order_type.upper()
    
    if order_type == "MARKET":
        return "MARKET"
    elif order_type == "LIMIT":
        return "LIMIT"
    elif order_type == "STOP_LIMIT":
        # For stop-limit orders, use STOP type with price parameter
        return "STOP"
    elif order_type == "OCO":
        # OCO orders are not directly supported in Futures API
        # This would need to be implemented as separate orders
        raise ValidationError("OCO orders are not supported in Binance Futures API")
    elif order_type == "TWAP":
        # TWAP is a custom implementation, not a native Binance order type
        raise ValidationError("TWAP orders are custom implementations, not native Binance order types")
    elif order_type == "GRID":
        # Grid orders are custom implementations, not native Binance order types
        raise ValidationError("Grid orders are custom implementations, not native Binance order types")
    else:
        raise ValidationError(f"Unsupported order type: {order_type}")
