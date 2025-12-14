from django import template

register = template.Library()


@register.filter
def humanize_number(value):
    """
    Convert numbers to human readable format with K, M, B suffixes
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return value
    
    if abs(num) >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif abs(num) >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif abs(num) >= 1_000:
        return f"{num / 1_000:.2f}K"
    else:
        return f"{num:.2f}"
