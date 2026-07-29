def format_currency(value):
    return f"${value:,.0f}"

def format_currency_millions(value):
    return f"${value / 1_000_000:,.1f}M"

def format_percentage(value):
    return f"{value:.1%}"

def format_integer(value):
    return f"{value:,.0f}"

def format_variance(value):
    return f"{'+' if value >= 0 else '-'}${abs(value) / 1_000_000:,.1f}M"

def format_year_range(start_year, projection_years):
    return f"{start_year}–{start_year + projection_years - 1}"
