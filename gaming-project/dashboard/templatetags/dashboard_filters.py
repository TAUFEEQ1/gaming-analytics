from django import template

register = template.Library()


@register.filter
def humanize_number(value):
    """
    Convert numbers to human readable format with K, M, B, T suffixes
    Handles negative values and trillions
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return value
    
    # Store sign for negative numbers
    sign = '-' if num < 0 else ''
    abs_num = abs(num)
    
    if abs_num >= 1_000_000_000_000:
        return f"{sign}{abs_num / 1_000_000_000_000:.2f}T"
    elif abs_num >= 1_000_000_000:
        return f"{sign}{abs_num / 1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{sign}{abs_num / 1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"{sign}{abs_num / 1_000:.2f}K"
    else:
        return f"{sign}{abs_num:.2f}"


@register.filter
def abs_value(value):
    """
    Return absolute value of a number
    """
    try:
        import math
        return abs(float(value))
    except (ValueError, TypeError):
        return value


@register.filter(name='abs')
def absolute_value(value):
    """
    Return absolute value of a number (template filter named 'abs')
    """
    try:
        import math
        return abs(float(value))
    except (ValueError, TypeError):
        return value
