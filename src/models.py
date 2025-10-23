"""Pydantic models for order requests and responses."""

from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal


class OrderRequest(BaseModel):
    """Model for order placement requests."""
    
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    side: Literal["BUY", "SELL"] = Field(..., description="Order side")
    order_type: Literal["MARKET", "LIMIT", "STOP_LIMIT", "OCO", "TWAP", "GRID"] = Field(
        ..., alias="type", description="Order type"
    )
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Order price (required for LIMIT orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (for stop orders)")
    time_in_force: Optional[Literal["GTC", "IOC", "FOK"]] = Field(
        "GTC", description="Time in force"
    )
    client_order_id: Optional[str] = Field(None, description="Client-provided order ID")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        """Validate symbol format."""
        import re
        if not re.match(r'^[A-Z0-9]{6,12}$', v):
            raise ValueError('Symbol must be 6-12 uppercase alphanumeric characters')
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Validate price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @field_validator('stop_price')
    @classmethod
    def validate_stop_price(cls, v):
        """Validate stop price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Stop price must be positive')
        return v


class OrderResponse(BaseModel):
    """Model for order placement responses."""
    
    order_id: int = Field(..., alias="orderId", description="Binance order ID")
    symbol: str = Field(..., description="Trading pair symbol")
    status: str = Field(..., description="Order status")
    side: str = Field(..., description="Order side")
    order_type: str = Field(..., alias="type", description="Order type")
    quantity: str = Field(..., alias="origQty", description="Order quantity")
    price: Optional[str] = Field(None, description="Order price")
    stop_price: Optional[str] = Field(None, alias="stopPrice", description="Stop price")
    time_in_force: Optional[str] = Field(None, alias="timeInForce", description="Time in force")
    executed_qty: str = Field(..., alias="executedQty", description="Executed quantity")
    avg_price: Optional[str] = Field(None, alias="avgPrice", description="Average execution price")
    client_order_id: Optional[str] = Field(None, alias="clientOrderId", description="Client order ID")
    transact_time: int = Field(..., alias="updateTime", description="Transaction time")
    
    model_config = ConfigDict(populate_by_name=True)


class OrderStatus(BaseModel):
    """Model for order status queries."""
    
    order_id: int = Field(..., alias="orderId", description="Binance order ID")
    symbol: str = Field(..., description="Trading pair symbol")
    status: str = Field(..., description="Order status")
    side: str = Field(..., description="Order side")
    order_type: str = Field(..., alias="type", description="Order type")
    quantity: str = Field(..., description="Order quantity")
    price: Optional[str] = Field(None, description="Order price")
    stop_price: Optional[str] = Field(None, alias="stopPrice", description="Stop price")
    time_in_force: Optional[str] = Field(None, alias="timeInForce", description="Time in force")
    executed_qty: str = Field(..., alias="executedQty", description="Executed quantity")
    avg_price: Optional[str] = Field(None, alias="avgPrice", description="Average execution price")
    client_order_id: Optional[str] = Field(None, alias="clientOrderId", description="Client order ID")
    transact_time: int = Field(..., alias="transactTime", description="Transaction time")
    update_time: int = Field(..., alias="updateTime", description="Last update time")
    
    model_config = ConfigDict(populate_by_name=True)


class ExchangeInfo(BaseModel):
    """Model for exchange information."""
    
    timezone: str
    server_time: int = Field(..., alias="serverTime")
    symbols: list[Dict[str, Any]]
    
    model_config = ConfigDict(populate_by_name=True)


class SymbolInfo(BaseModel):
    """Model for individual symbol information."""
    
    symbol: str
    status: str
    base_asset: str = Field(..., alias="baseAsset")
    base_asset_precision: int = Field(..., alias="baseAssetPrecision")
    quote_asset: str = Field(..., alias="quoteAsset")
    quote_precision: int = Field(..., alias="quotePrecision")
    filters: list[Dict[str, Any]]
    
    model_config = ConfigDict(populate_by_name=True)


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    
    model_config = ConfigDict(populate_by_name=True)
