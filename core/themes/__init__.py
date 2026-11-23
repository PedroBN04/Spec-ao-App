from core.models import Theme
from core.themes import hotel, noshow, telco

REGISTRY: dict[str, Theme] = {
    "telco": telco.THEME,
    "hotel": hotel.THEME,
    "noshow": noshow.THEME,
}
