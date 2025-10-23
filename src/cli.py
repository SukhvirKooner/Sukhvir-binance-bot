"""CLI interface for the Binance Futures Order Bot."""

import sys
import click
from typing import Optional

from .config import config
from .binance_client import BinanceClient
from .orders.market_orders import MarketOrder
from .orders.limit_orders import LimitOrder
from .orders.advanced.stop_limit import StopLimitOrder
from .orders.advanced.oco import OCOOrder
from .orders.advanced.twap import TWAPOrder
from .orders.advanced.grid import GridOrder
from .validators import ValidationError
from .utils.logger import logger


class BotCLI:
    """CLI handler for the Binance bot."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """
        Initialize CLI handler.
        
        Args:
            dry_run: Whether to run in dry-run mode
            verbose: Whether to enable verbose logging
        """
        self.dry_run = dry_run
        self.verbose = verbose
        
        if verbose:
            config.LOG_LEVEL = "DEBUG"
        
        # Initialize client
        try:
            config.validate_config()
            self.client = BinanceClient(
                api_key=config.BINANCE_API_KEY,
                api_secret=config.BINANCE_API_SECRET,
                testnet=True
            )
            
            # Test connection
            if not self.dry_run:
                self.client.test_connection()
            
            logger.info(
                "cli",
                "cli_initialized",
                dry_run=dry_run,
                verbose=verbose
            )
            
        except Exception as e:
            logger.error(
                "cli",
                "cli_initialization_failed",
                error=str(e)
            )
            raise
    
    def get_symbol_info(self, symbol: str):
        """Get symbol information for validation."""
        try:
            return self.client.get_symbol_info(symbol)
        except Exception as e:
            logger.warning(
                "cli",
                "symbol_info_fetch_failed",
                symbol=symbol,
                error=str(e)
            )
            return None
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        client_order_id: Optional[str] = None
    ):
        """Place an order."""
        try:
            symbol_info = self.get_symbol_info(symbol)
            
            if self.dry_run:
                logger.info(
                    "cli",
                    "dry_run_order",
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    stop_price=stop_price,
                    time_in_force=time_in_force
                )
                click.echo(f"DRY RUN: Would place {order_type} {side} order for {quantity} {symbol}")
                if price:
                    click.echo(f"  Price: {price}")
                if stop_price:
                    click.echo(f"  Stop Price: {stop_price}")
                return
            
            # Place order based on type
            if order_type == "MARKET":
                market_order = MarketOrder(self.client)
                response = market_order.place_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    client_order_id=client_order_id,
                    symbol_info=symbol_info
                )
            elif order_type == "LIMIT":
                if price is None:
                    raise ValidationError("Price is required for LIMIT orders")
                limit_order = LimitOrder(self.client)
                response = limit_order.place_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    time_in_force=time_in_force,
                    client_order_id=client_order_id,
                    symbol_info=symbol_info
                )
            elif order_type == "STOP_LIMIT":
                if price is None or stop_price is None:
                    raise ValidationError("Price and stop_price are required for STOP_LIMIT orders")
                stop_limit_order = StopLimitOrder(self.client)
                response = stop_limit_order.place_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    stop_price=stop_price,
                    time_in_force=time_in_force,
                    client_order_id=client_order_id,
                    symbol_info=symbol_info
                )
            elif order_type == "OCO":
                if price is None or stop_price is None:
                    raise ValidationError("Price and stop_price are required for OCO orders")
                oco_order = OCOOrder(self.client)
                response = oco_order.place_oco_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    stop_price=stop_price,
                    client_order_id=client_order_id,
                    symbol_info=symbol_info
                )
            else:
                raise ValidationError(f"Unsupported order type: {order_type}")
            
            # Display results
            click.echo(f"Order placed successfully!")
            click.echo(f"  Order ID: {response.order_id}")
            click.echo(f"  Symbol: {response.symbol}")
            click.echo(f"  Side: {response.side}")
            click.echo(f"  Type: {response.order_type}")
            click.echo(f"  Quantity: {response.quantity}")
            click.echo(f"  Status: {response.status}")
            if response.price:
                click.echo(f"  Price: {response.price}")
            if response.avg_price:
                click.echo(f"  Average Price: {response.avg_price}")
            if response.executed_qty:
                click.echo(f"  Executed Quantity: {response.executed_qty}")
            
        except ValidationError as e:
            click.echo(f"Validation error: {e}", err=True)
            sys.exit(2)
        except Exception as e:
            click.echo(f"Error placing order: {e}", err=True)
            logger.error(
                "cli",
                "order_placement_failed",
                error=str(e),
                symbol=symbol,
                side=side,
                order_type=order_type
            )
            sys.exit(3)
    
    def get_order_status(self, symbol: str, order_id: int):
        """Get order status."""
        try:
            if self.dry_run:
                click.echo(f"DRY RUN: Would query order {order_id} for {symbol}")
                return
            
            response = self.client.get_order(symbol=symbol, order_id=order_id)
            
            click.echo(f"Order Status:")
            click.echo(f"  Order ID: {response.order_id}")
            click.echo(f"  Symbol: {response.symbol}")
            click.echo(f"  Side: {response.side}")
            click.echo(f"  Type: {response.order_type}")
            click.echo(f"  Status: {response.status}")
            click.echo(f"  Quantity: {response.quantity}")
            click.echo(f"  Executed Quantity: {response.executed_qty}")
            if response.price:
                click.echo(f"  Price: {response.price}")
            if response.avg_price:
                click.echo(f"  Average Price: {response.avg_price}")
            if response.stop_price:
                click.echo(f"  Stop Price: {response.stop_price}")
            
        except Exception as e:
            click.echo(f"Error getting order status: {e}", err=True)
            logger.error(
                "cli",
                "order_status_failed",
                error=str(e),
                symbol=symbol,
                order_id=order_id
            )
            sys.exit(3)
    
    def cancel_order(self, symbol: str, order_id: int):
        """Cancel an order."""
        try:
            if self.dry_run:
                click.echo(f"DRY RUN: Would cancel order {order_id} for {symbol}")
                return
            
            response = self.client.cancel_order(symbol=symbol, order_id=order_id)
            
            click.echo(f"Order cancelled successfully!")
            click.echo(f"  Order ID: {response.get('orderId', 'N/A')}")
            click.echo(f"  Symbol: {response.get('symbol', 'N/A')}")
            click.echo(f"  Status: {response.get('status', 'N/A')}")
            
        except Exception as e:
            click.echo(f"Error cancelling order: {e}", err=True)
            logger.error(
                "cli",
                "order_cancellation_failed",
                error=str(e),
                symbol=symbol,
                order_id=order_id
            )
            sys.exit(3)
    
    def simulate_twap(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        duration_minutes: int,
        order_type: str = "MARKET",
        price: Optional[float] = None
    ):
        """Simulate TWAP order."""
        try:
            twap_order = TWAPOrder(self.client)
            simulation = twap_order.simulate_twap(
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                duration_minutes=duration_minutes,
                order_type=order_type,
                price=price
            )
            
            click.echo(f"TWAP Simulation Results:")
            click.echo(f"  Symbol: {simulation['symbol']}")
            click.echo(f"  Side: {simulation['side']}")
            click.echo(f"  Total Quantity: {simulation['total_quantity']}")
            click.echo(f"  Duration: {simulation['duration_minutes']} minutes")
            click.echo(f"  Number of Orders: {simulation['num_orders']}")
            click.echo(f"  Interval: {simulation['interval_seconds']} seconds")
            click.echo(f"  Quantity per Order: {simulation['quantity_per_order']}")
            
            click.echo(f"\nOrder Schedule:")
            for order in simulation['orders']:
                click.echo(f"  Order {order['order_index']}: {order['quantity']} @ {order['time_offset_seconds']}s")
                if order['price']:
                    click.echo(f"    Price: {order['price']}")
            
        except Exception as e:
            click.echo(f"Error simulating TWAP: {e}", err=True)
            logger.error(
                "cli",
                "twap_simulation_failed",
                error=str(e),
                symbol=symbol
            )
            sys.exit(4)
    
    def simulate_grid(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        min_price: float,
        max_price: float,
        num_levels: int
    ):
        """Simulate grid order."""
        try:
            grid_order = GridOrder(self.client)
            simulation = grid_order.simulate_grid(
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                price_range=(min_price, max_price),
                num_levels=num_levels
            )
            
            click.echo(f"Grid Simulation Results:")
            click.echo(f"  Symbol: {simulation['symbol']}")
            click.echo(f"  Side: {simulation['side']}")
            click.echo(f"  Total Quantity: {simulation['total_quantity']}")
            click.echo(f"  Price Range: {simulation['price_range'][0]} - {simulation['price_range'][1]}")
            click.echo(f"  Number of Levels: {simulation['num_levels']}")
            click.echo(f"  Price Step: {simulation['price_step']}")
            click.echo(f"  Quantity per Level: {simulation['quantity_per_level']}")
            
            click.echo(f"\nGrid Levels:")
            for level in simulation['levels']:
                click.echo(f"  Level {level['level']}: {level['quantity']} @ {level['price']}")
            
        except Exception as e:
            click.echo(f"Error simulating grid: {e}", err=True)
            logger.error(
                "cli",
                "grid_simulation_failed",
                error=str(e),
                symbol=symbol
            )
            sys.exit(4)


# CLI Commands
@click.group()
@click.option('--profile', help='API key profile to use')
@click.option('--dry-run', is_flag=True, help='Validate and simulate orders without placing them')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, profile, dry_run, verbose):
    """Binance Futures Order Bot - CLI interface for trading operations."""
    ctx.ensure_object(dict)
    ctx.obj['bot'] = BotCLI(dry_run=dry_run, verbose=verbose)


@cli.command()
@click.option('--symbol', required=True, help='Trading symbol (e.g., BTCUSDT)')
@click.option('--side', required=True, type=click.Choice(['BUY', 'SELL']), help='Order side')
@click.option('--type', 'order_type', required=True, type=click.Choice(['MARKET', 'LIMIT', 'STOP_LIMIT', 'OCO']), help='Order type')
@click.option('--quantity', required=True, type=float, help='Order quantity')
@click.option('--price', type=float, help='Order price (required for LIMIT/STOP_LIMIT/OCO)')
@click.option('--stop-price', type=float, help='Stop price (required for STOP_LIMIT/OCO)')
@click.option('--time-in-force', default='GTC', type=click.Choice(['GTC', 'IOC', 'FOK']), help='Time in force')
@click.option('--client-order-id', help='Client-provided order ID')
@click.pass_context
def place(ctx, symbol, side, order_type, quantity, price, stop_price, time_in_force, client_order_id):
    """Place an order."""
    bot = ctx.obj['bot']
    bot.place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        time_in_force=time_in_force,
        client_order_id=client_order_id
    )


@cli.command()
@click.option('--symbol', required=True, help='Trading symbol')
@click.option('--order-id', required=True, type=int, help='Order ID to query')
@click.pass_context
def status(ctx, symbol, order_id):
    """Query order status."""
    bot = ctx.obj['bot']
    bot.get_order_status(symbol=symbol, order_id=order_id)


@cli.command()
@click.option('--symbol', required=True, help='Trading symbol')
@click.option('--order-id', required=True, type=int, help='Order ID to cancel')
@click.pass_context
def cancel(ctx, symbol, order_id):
    """Cancel an order."""
    bot = ctx.obj['bot']
    bot.cancel_order(symbol=symbol, order_id=order_id)


@cli.command()
@click.option('--symbol', required=True, help='Trading symbol')
@click.option('--side', required=True, type=click.Choice(['BUY', 'SELL']), help='Order side')
@click.option('--total-quantity', required=True, type=float, help='Total quantity to execute')
@click.option('--duration-minutes', required=True, type=int, help='Duration in minutes')
@click.option('--order-type', default='MARKET', type=click.Choice(['MARKET', 'LIMIT']), help='Type of orders to place')
@click.option('--price', type=float, help='Price for LIMIT orders')
@click.pass_context
def simulate_twap(ctx, symbol, side, total_quantity, duration_minutes, order_type, price):
    """Simulate TWAP order execution."""
    bot = ctx.obj['bot']
    bot.simulate_twap(
        symbol=symbol,
        side=side,
        total_quantity=total_quantity,
        duration_minutes=duration_minutes,
        order_type=order_type,
        price=price
    )


@cli.command()
@click.option('--symbol', required=True, help='Trading symbol')
@click.option('--side', required=True, type=click.Choice(['BUY', 'SELL']), help='Order side')
@click.option('--total-quantity', required=True, type=float, help='Total quantity to distribute')
@click.option('--min-price', required=True, type=float, help='Minimum price for grid')
@click.option('--max-price', required=True, type=float, help='Maximum price for grid')
@click.option('--num-levels', required=True, type=int, help='Number of grid levels')
@click.pass_context
def simulate_grid(ctx, symbol, side, total_quantity, min_price, max_price, num_levels):
    """Simulate grid order execution."""
    bot = ctx.obj['bot']
    bot.simulate_grid(
        symbol=symbol,
        side=side,
        total_quantity=total_quantity,
        min_price=min_price,
        max_price=max_price,
        num_levels=num_levels
    )


if __name__ == '__main__':
    cli()
