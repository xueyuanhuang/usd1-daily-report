"""Parsing utilities for JSON data extraction."""

from typing import Any, Optional, List, Union


def safe_get(obj: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely traverse nested dict/list structure.
    
    Args:
        obj: The object to traverse
        *keys: Keys or indices to follow
        default: Default value if path not found
        
    Returns:
        The value at the path, or default if not found
    """
    current = obj
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list) and isinstance(key, int):
            if 0 <= key < len(current):
                current = current[key]
            else:
                return default
        else:
            return default
    return current


def find_market_by_symbol(
    obj: Any,
    symbol: str = "USD1",
    depth_limit: int = 6,
    _current_depth: int = 0,
) -> Optional[dict]:
    """
    Recursively search for a market entry matching the given symbol.
    
    Looks for dict entries with keys like 'symbol', 'ticker', 'underlyingSymbol',
    'tokenSymbol', 'asset' matching the target symbol (case-insensitive).
    
    Args:
        obj: Object to search
        symbol: Symbol to find (default "USD1")
        depth_limit: Maximum recursion depth
        _current_depth: Internal depth tracker
        
    Returns:
        The matching dict entry, or None if not found
    """
    if _current_depth >= depth_limit:
        return None
    
    symbol_upper = symbol.upper()
    symbol_keys = [
        "symbol", "ticker", "underlyingSymbol", "tokenSymbol", 
        "asset", "name", "token", "coinSymbol", "assetSymbol",
    ]
    
    if isinstance(obj, dict):
        # Check if this dict represents the target market
        for key in symbol_keys:
            value = obj.get(key)
            if isinstance(value, str) and value.upper() == symbol_upper:
                return obj
        
        # Recurse into dict values
        for value in obj.values():
            result = find_market_by_symbol(value, symbol, depth_limit, _current_depth + 1)
            if result is not None:
                return result
                
    elif isinstance(obj, list):
        # Recurse into list items
        for item in obj:
            result = find_market_by_symbol(item, symbol, depth_limit, _current_depth + 1)
            if result is not None:
                return result
    
    return None


def find_all_markets_by_symbol(
    obj: Any,
    symbol: str = "USD1",
    depth_limit: int = 6,
    _current_depth: int = 0,
) -> List[dict]:
    """
    Find all market entries matching the given symbol.
    
    Returns:
        List of matching dict entries
    """
    results = []
    
    if _current_depth >= depth_limit:
        return results
    
    symbol_upper = symbol.upper()
    symbol_keys = [
        "symbol", "ticker", "underlyingSymbol", "tokenSymbol", 
        "asset", "name", "token", "coinSymbol", "assetSymbol",
    ]
    
    if isinstance(obj, dict):
        # Check if this dict represents the target market
        for key in symbol_keys:
            value = obj.get(key)
            if isinstance(value, str) and value.upper() == symbol_upper:
                results.append(obj)
                break  # Found match, don't recurse into this dict's values
        else:
            # Recurse into dict values
            for value in obj.values():
                results.extend(find_all_markets_by_symbol(value, symbol, depth_limit, _current_depth + 1))
                
    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_all_markets_by_symbol(item, symbol, depth_limit, _current_depth + 1))
    
    return results


def normalize_rate(value: Any) -> Optional[float]:
    """
    Normalize a rate value to percentage.
    
    If value <= 1.5, assumes it's a fraction and multiplies by 100.
    Otherwise assumes it's already in percent.
    
    Args:
        value: Rate value (could be str, int, float)
        
    Returns:
        Rate as percentage float, or None if invalid
    """
    if value is None:
        return None
    
    try:
        rate = float(value)
        # If rate is very small (fraction), convert to percent
        if abs(rate) <= 1.5:
            rate = rate * 100
        return rate
    except (ValueError, TypeError):
        return None


def normalize_amount(
    value: Any,
    decimals: Optional[int] = None,
) -> Optional[float]:
    """
    Normalize a token amount value.
    
    Args:
        value: The amount value
        decimals: If provided, divide by 10^decimals
        
    Returns:
        Normalized float amount, or None if invalid
    """
    if value is None:
        return None
    
    try:
        amount = float(value)
        if decimals is not None and decimals > 0:
            amount = amount / (10 ** decimals)
        return amount
    except (ValueError, TypeError):
        return None


def format_rate(
    base: Optional[float],
    incentive: Optional[float] = None,
    is_borrow: bool = False,
) -> str:
    """
    Format rate with optional incentive breakdown.
    
    Args:
        base: Base rate in percent
        incentive: Incentive rate in percent (optional)
        is_borrow: If True, format as borrow (subtract incentive)
        
    Returns:
        Formatted rate string like "7.73%" or "7.73% (base 2.93% + inc 4.81%)"
    """
    if base is None:
        return "N/A"
    
    if incentive is None or incentive == 0:
        return f"{base:.2f}%"
    
    if is_borrow:
        # For borrow: net = borrow - incentive
        net = base - incentive
        return f"{net:.2f}% (borrow {base:.2f}% - inc {incentive:.2f}%)"
    else:
        # For supply: total = base + incentive
        total = base + incentive
        return f"{total:.2f}% (base {base:.2f}% + inc {incentive:.2f}%)"


def format_rate_simple(rate: Optional[float]) -> str:
    """Format a simple rate without breakdown."""
    if rate is None:
        return "N/A"
    return f"{rate:.2f}%"


def extract_numeric(
    obj: dict,
    candidate_keys: List[str],
    debug: bool = False,
) -> Optional[float]:
    """
    Try to extract a numeric value from dict using candidate keys.
    
    Args:
        obj: Dict to search
        candidate_keys: Keys to try in order
        debug: Print which key was used
        
    Returns:
        Found numeric value or None
    """
    for key in candidate_keys:
        value = obj.get(key)
        if value is not None:
            try:
                result = float(value)
                if debug:
                    print(f"    [Found '{key}' = {result}]")
                return result
            except (ValueError, TypeError):
                continue
    return None
