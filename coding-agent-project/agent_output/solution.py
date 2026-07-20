"""
Module for calculating order prices with tiered volume discounts.

This module provides functionality to apply tiered discount rules based on
quantity thresholds to calculate final order prices.
"""

from typing import List, Tuple


class DiscountTier:
    """Represents a single discount tier with minimum quantity and percentage."""

    def __init__(self, min_quantity: int, discount_percent: float) -> None:
        """
        Initialize a discount tier.

        Args:
            min_quantity: Minimum quantity required for this discount tier
            discount_percent: Discount percentage (0-100) to apply

        Raises:
            ValueError: If min_quantity is negative or discount_percent is invalid
        """
        if min_quantity < 0:
            raise ValueError("Minimum quantity must be non-negative")
        if not 0 <= discount_percent <= 100:
            raise ValueError("Discount percent must be between 0 and 100")

        self.min_quantity = min_quantity
        self.discount_percent = discount_percent

    def __repr__(self) -> str:
        """Return string representation of the discount tier."""
        return (f"DiscountTier(min_quantity={self.min_quantity}, "
                f"discount_percent={self.discount_percent})")


def calculate_final_price(
    unit_price: float,
    quantity: int,
    discount_tiers: List[Tuple[int, float]]
) -> float:
    """
    Calculate the final price after applying tiered volume discounts.

    The function finds the highest applicable discount tier based on quantity
    and applies that discount to the total order value.

    Args:
        unit_price: Price per unit (must be positive)
        quantity: Number of units ordered (must be non-negative)
        discount_tiers: List of tuples (min_quantity, discount_percent).
                       Each tier specifies minimum quantity and discount %.
                       Example: [(10, 5.0), (50, 10.0)] means 5% off for 10+
                       units and 10% off for 50+ units.

    Returns:
        Final price after applying the highest applicable discount

    Raises:
        ValueError: If unit_price is non-positive, quantity is negative,
                   or discount_tiers contain invalid values
        TypeError: If inputs are of incorrect type

    Examples:
        >>> calculate_final_price(10.0, 5, [(10, 5.0), (50, 10.0)])
        50.0
        >>> calculate_final_price(10.0, 15, [(10, 5.0), (50, 10.0)])
        142.5
        >>> calculate_final_price(10.0, 60, [(10, 5.0), (50, 10.0)])
        540.0
    """
    if not isinstance(unit_price, (int, float)):
        raise TypeError("unit_price must be a number")
    if not isinstance(quantity, int):
        raise TypeError("quantity must be an integer")
    if not isinstance(discount_tiers, list):
        raise TypeError("discount_tiers must be a list")

    if unit_price <= 0:
        raise ValueError("Unit price must be positive")
    if quantity < 0:
        raise ValueError("Quantity must be non-negative")

    # Validate and convert discount tiers
    validated_tiers: List[DiscountTier] = []
    for tier in discount_tiers:
        if not isinstance(tier, (tuple, list)) or len(tier) != 2:
            raise ValueError(
                "Each discount tier must be a tuple/list of "
                "(min_quantity, discount_percent)"
            )
        min_qty, discount_pct = tier
        validated_tiers.append(DiscountTier(min_qty, discount_pct))

    # Calculate base price
    base_price = unit_price * quantity

    # Find the highest applicable discount tier
    applicable_discount = 0.0
    for tier in validated_tiers:
        if quantity >= tier.min_quantity:
            applicable_discount = max(applicable_discount, tier.discount_percent)

    # Apply discount
    discount_amount = base_price * (applicable_discount / 100)
    final_price = base_price - discount_amount

    return round(final_price, 2)


def calculate_final_price_with_breakdown(
    unit_price: float,
    quantity: int,
    discount_tiers: List[Tuple[int, float]]
) -> dict:
    """
    Calculate final price with detailed breakdown of the calculation.

    Args:
        unit_price: Price per unit
        quantity: Number of units ordered
        discount_tiers: List of discount tier tuples

    Returns:
        Dictionary containing:
            - base_price: Total before discount
            - discount_percent: Percentage discount applied
            - discount_amount: Dollar amount of discount
            - final_price: Total after discount

    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs are of incorrect type
    """
    base_price = unit_price * quantity

    # Validate tiers
    validated_tiers: List[DiscountTier] = []
    for tier in discount_tiers:
        if not isinstance(tier, (tuple, list)) or len(tier) != 2:
            raise ValueError(
                "Each discount tier must be a tuple/list of "
                "(min_quantity, discount_percent)"
            )
        min_qty, discount_pct = tier
        validated_tiers.append(DiscountTier(min_qty, discount_pct))

    # Find applicable discount
    applicable_discount = 0.0
    for tier in validated_tiers:
        if quantity >= tier.min_quantity:
            applicable_discount = max(applicable_discount, tier.discount_percent)

    discount_amount = base_price * (applicable_discount / 100)
    final_price = calculate_final_price(unit_price, quantity, discount_tiers)

    return {
        "base_price": round(base_price, 2),
        "discount_percent": applicable_discount,
        "discount_amount": round(discount_amount, 2),
        "final_price": final_price
    }
