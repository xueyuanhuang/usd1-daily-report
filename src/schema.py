"""Data schema for USD1 lending market metrics."""

from dataclasses import dataclass
from typing import Optional


def compact_amount(x: Optional[float]) -> str:
    """
    Format a numeric amount in compact notation.

    Returns:
        - "N/A" if x is None
        - "{x/1e12:.2f}T" if >= 1 trillion
        - "{x/1e9:.2f}B" if >= 1 billion
        - "{x/1e6:.2f}M" if >= 1 million
        - "{x/1e3:.2f}K" if >= 1 thousand
        - "{x:.2f}" otherwise
    """
    if x is None:
        return "N/A"

    if x >= 1e12:
        return f"{x / 1e12:.2f}T"
    elif x >= 1e9:
        return f"{x / 1e9:.2f}B"
    elif x >= 1e6:
        return f"{x / 1e6:.2f}M"
    elif x >= 1e3:
        return f"{x / 1e3:.2f}K"
    else:
        return f"{x:.2f}"


@dataclass
class Row:
    """A single row representing one protocol's USD1 market metrics."""

    protocol: str
    total_supplied: Optional[float]
    supply_rate: str
    total_borrowed: Optional[float]
    borrow_rate: str

    def to_csv_dict(self) -> dict:
        """Convert to dictionary for CSV writing with compact amount formatting."""
        return {
            "protocol": self.protocol,
            "total_supplied": compact_amount(self.total_supplied),
            "supply_rate": self.supply_rate,
            "total_borrowed": compact_amount(self.total_borrowed),
            "borrow_rate": self.borrow_rate,
        }

    def to_table_row(self) -> list:
        """Convert to list for tabulate display with compact amount formatting."""
        return [
            self.protocol,
            compact_amount(self.total_supplied),
            self.supply_rate,
            compact_amount(self.total_borrowed),
            self.borrow_rate,
        ]


# CSV header columns
CSV_COLUMNS = ["protocol", "total_supplied", "supply_rate", "total_borrowed", "borrow_rate"]
