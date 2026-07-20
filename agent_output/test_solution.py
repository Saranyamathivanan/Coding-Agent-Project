"""
Test suite for order price calculation with tiered volume discounts.
"""

import pytest
from solution import (
    calculate_final_price,
    calculate_final_price_with_breakdown,
    DiscountTier
)


class TestDiscountTier:
    """Tests for the DiscountTier class."""

    def test_valid_tier_creation(self) -> None:
        """Test creating a valid discount tier."""
        tier = DiscountTier(10, 5.0)
        assert tier.min_quantity == 10
        assert tier.discount_percent == 5.0

    def test_invalid_min_quantity(self) -> None:
        """Test that negative min_quantity raises ValueError."""
        with pytest.raises(ValueError, match="Minimum quantity must be non-negative"):
            DiscountTier(-1, 5.0)

    def test_invalid_discount_percent_negative(self) -> None:
        """Test that negative discount percent raises ValueError."""
        with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
            DiscountTier(10, -5.0)

    def test_invalid_discount_percent_over_100(self) -> None:
        """Test that discount percent over 100 raises ValueError."""
        with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
            DiscountTier(10, 150.0)


class TestCalculateFinalPrice:
    """Tests for the calculate_final_price function."""

    def test_normal_case_no_discount(self) -> None:
        """Test normal case where quantity doesn't meet any tier threshold."""
        discount_tiers = [(10, 5.0), (50, 10.0)]
        result = calculate_final_price(10.0, 5, discount_tiers)
        assert result == 50.0

    def test_normal_case_first_tier(self) -> None:
        """Test normal case with first tier discount applied."""
        discount_tiers = [(10, 5.0), (50, 10.0)]
        result = calculate_final_price(10.0, 15, discount_tiers)
        # 15 * 10 = 150, 5% off = 142.50
        assert result == 142.5

    def test_normal_case_second_tier(self) -> None:
        """Test normal case with second tier discount applied."""
        discount_tiers = [(10, 5.0), (50, 10.0)]
        result = calculate_final_price(10.0, 60, discount_tiers)
        # 60 * 10 = 600, 10% off = 540.00
        assert result == 540.0

    def test_edge_case_zero_quantity(self) -> None:
        """Test edge case with zero quantity."""
        discount_tiers = [(10, 5.0), (50, 10.0)]
        result = calculate_final_price(10.0, 0, discount_tiers)
        assert result == 0.0

    def test_edge_case_exact_tier_threshold(self) -> None:
        """Test edge case where quantity exactly meets tier threshold."""
        discount_tiers = [(10, 5.0), (50, 10.0)]
        result = calculate_final_price(10.0, 10, discount_tiers)
        # 10 * 10 = 100, 5% off = 95.00
        assert result == 95.0

    def test_edge_case_empty_discount_tiers(self) -> None:
        """Test edge case with no discount tiers."""
        result = calculate_final_price(10.0, 20, [])
        assert result == 200.0

    def test_edge_case_single_tier(self) -> None:
        """Test edge case with single discount tier."""
        discount_tiers = [(10, 15.0)]
        result = calculate_final_price(20.0, 15, discount_tiers)
        # 15 * 20 = 300, 15% off = 255.00
        assert result == 255.0

    def test_edge_case_multiple_applicable_tiers(self) -> None:
        """Test that highest discount is applied when multiple tiers qualify."""
        discount_tiers = [(10, 5.0), (20, 8.0), (50, 10.0)]
        result = calculate_final_price(10.0, 25, discount_tiers)
        # 25 * 10 = 250, 8% off (highest applicable) = 230.00
        assert result == 230.0

    def test_edge_case_unsorted_tiers(self) -> None:
        """Test that function works with unsorted discount tiers."""
        discount_tiers = [(50, 10.0), (10, 5.0)]
        result = calculate_final_price(10.0, 60, discount_tiers)
        # Should still apply 10% discount
        assert result == 540.0

    def test_edge_case_decimal_unit_price(self) -> None:
        """Test with decimal unit price."""
        discount_tiers = [(10, 5.0)]
        result = calculate_final_price(9.99, 10, discount_tiers)
        # 10 * 9.99 = 99.90, 5% off = 94.91 (rounded)
        assert result == 94.91

    def test_invalid_negative_unit_price(self) -> None:
        """Test that negative unit price raises ValueError."""
        discount_tiers = [(10, 5.0)]
        with pytest.raises(ValueError, match="Unit price must be positive"):
            calculate_final_price(-10.0, 5, discount_tiers)

    def test_invalid_zero_unit_price(self) -> None:
        """Test that zero unit price raises ValueError."""
        discount_tiers = [(10, 5.0)]
        with pytest.raises(ValueError, match="Unit price must be positive"):
            calculate_final_price(0.0, 5, discount_tiers)

    def test_invalid_negative_quantity(self) -> None:
        """Test that negative quantity raises ValueError."""
        discount_tiers = [(10, 5.0)]
        with pytest.raises(ValueError, match="Quantity must be non-negative"):
            calculate_final_price(10.0, -5, discount_tiers)

    def test_invalid_type_unit_price(self) -> None:
        """Test that invalid type for unit_price raises TypeError."""
        discount_tiers = [(10, 5.0)]
        with pytest.raises(TypeError, match="unit_price must be a number"):
            calculate_final_price("10.0", 5, discount_tiers)

    def test_invalid_type_quantity(self) -> None:
        """Test that invalid type for quantity raises TypeError."""
        discount_tiers = [(10, 5.0)]
        with pytest.raises(TypeError, match="quantity must be an integer"):
            calculate_final_price(10.0, 5.5, discount_tiers)

    def test_invalid_type_discount_tiers(self) -> None:
        """Test that invalid type for discount_tiers raises TypeError."""
        with pytest.raises(TypeError, match="discount_tiers must be a list"):
            calculate_final_price(10.0, 5, "invalid")

    def test_invalid_tier_format(self) -> None:
        """Test that invalid tier format raises ValueError."""
        discount_tiers = [(10, 5.0), (20,)]  # Missing discount percent
        with pytest.raises(ValueError, match="Each discount tier must be a tuple/list"):
            calculate_final_price(10.0, 15, discount_tiers)

    def test_invalid_tier_min_quantity(self) -> None:
        """Test that invalid min_quantity in tier raises ValueError."""
        discount_tiers = [(-10, 5.0)]
        with pytest.raises(ValueError, match="Minimum quantity must be non-negative"):
            calculate_final_price(10.0, 5, discount_tiers)

    def test_invalid_tier_discount_percent(self) -> None:
        """Test that invalid discount_percent in tier raises ValueError."""
        discount_tiers = [(10, 150.0)]
        with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
            calculate_final_price(10.0, 15, discount_tiers)


class TestCalculateFinalPriceWithBreakdown:
    """Tests for the calculate_final_price_with_breakdown function."""

    def test_breakdown_with_discount(self) -> None:
        """Test breakdown calculation with discount applied."""
        discount_tiers = [(10, 5.0), (50, 10.0)]
        result = calculate_final_price_with_breakdown(10.0, 15, discount_tiers)

        assert result["base_price"] == 150.0
        assert result["discount_percent"] == 5.0
        assert result["discount_amount"] == 7.5
        assert result["final_price"] == 142.5

    def test_breakdown_without_discount(self) -> None:
        """Test breakdown when no discount applies."""
        discount_tiers = [(10, 5.0)]
        result = calculate_final_price_with_breakdown(10.0, 5, discount_tiers)

        assert result["base_price"] == 50.0
        assert result["discount_percent"] == 0.0
        assert result["discount_amount"] == 0.0
        assert result["final_price"] == 50.0

    def test_breakdown_highest_tier(self) -> None:
        """Test breakdown with highest tier discount."""
        discount_tiers = [(10, 5.0), (50, 10.0), (100, 15.0)]
        result = calculate_final_price_with_breakdown(10.0, 120, discount_tiers)

        assert result["base_price"] == 1200.0
        assert result["discount_percent"] == 15.0
        assert result["discount_amount"] == 180.0
        assert result["final_price"] == 1020.0
