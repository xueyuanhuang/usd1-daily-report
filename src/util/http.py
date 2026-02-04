"""HTTP utilities with retry and backoff."""

import time
from typing import Any, Optional

import requests

# Default User-Agent
USER_AGENT = "USD1-Snapshot/1.0 (Python/requests)"

# Retry configuration
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds


def fetch_json(
    url: str,
    timeout: float = 20.0,
    debug: bool = False,
    headers: Optional[dict] = None,
) -> Any:
    """
    Fetch JSON from URL with retry and exponential backoff.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        debug: If True, print response shape info
        headers: Optional additional headers
        
    Returns:
        Parsed JSON response
        
    Raises:
        requests.RequestException: If all retries fail
    """
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    
    last_exception: Optional[Exception] = None
    
    for attempt in range(MAX_RETRIES):
        try:
            if debug and attempt > 0:
                print(f"  [Retry {attempt + 1}/{MAX_RETRIES}]")
            
            response = requests.get(
                url,
                headers=request_headers,
                timeout=timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            
            if debug:
                _print_shape(data, url)
            
            return data
            
        except requests.RequestException as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                sleep_time = BACKOFF_BASE * (2 ** attempt)
                if debug:
                    print(f"  [Request failed: {e}, retrying in {sleep_time}s...]")
                time.sleep(sleep_time)
    
    raise last_exception  # type: ignore


def _print_shape(data: Any, url: str, max_items: int = 3) -> None:
    """Print a preview of the JSON structure for debugging."""
    print(f"\n  [DEBUG] Response shape for: {url[:80]}...")
    _print_shape_recursive(data, indent=2, max_depth=3, max_items=max_items)
    print()


def _print_shape_recursive(
    obj: Any,
    indent: int = 0,
    max_depth: int = 3,
    max_items: int = 3,
    current_depth: int = 0,
) -> None:
    """Recursively print object shape."""
    prefix = "  " * indent
    
    if current_depth >= max_depth:
        print(f"{prefix}...")
        return
    
    if isinstance(obj, dict):
        keys = list(obj.keys())[:max_items]
        print(f"{prefix}dict with {len(obj)} keys: {keys}{'...' if len(obj) > max_items else ''}")
        for key in keys[:2]:  # Show first 2 keys' structure
            print(f"{prefix}  '{key}':")
            _print_shape_recursive(obj[key], indent + 2, max_depth, max_items, current_depth + 1)
    elif isinstance(obj, list):
        print(f"{prefix}list with {len(obj)} items")
        if obj and current_depth < max_depth - 1:
            print(f"{prefix}  [0]:")
            _print_shape_recursive(obj[0], indent + 2, max_depth, max_items, current_depth + 1)
    elif isinstance(obj, str):
        preview = obj[:50] + "..." if len(obj) > 50 else obj
        print(f"{prefix}str: \"{preview}\"")
    elif isinstance(obj, (int, float)):
        print(f"{prefix}{type(obj).__name__}: {obj}")
    elif obj is None:
        print(f"{prefix}null")
    else:
        print(f"{prefix}{type(obj).__name__}")
