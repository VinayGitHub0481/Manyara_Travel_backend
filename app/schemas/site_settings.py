

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SiteSettingsUpdate(BaseModel):
    # ============================================================
    # Website / marketing settings
    # ============================================================

    offer_banner_text: Optional[str] = None
    homepage_headline: Optional[str] = None
    trust_line: Optional[str] = None

    # ============================================================
    # Top Info Bar
    # ============================================================

    # Show / hide the Top Info Bar on the public website
    top_bar_enabled: Optional[bool] = None

    # Locations displayed in the Top Info Bar
    # Example: Hyderabad / Bengaluru
    top_bar_location_1: Optional[str] = None
    top_bar_location_2: Optional[str] = None

    # Example: 5000+ successful travelers
    top_bar_traveller_text: Optional[str] = None

    # Social media link 1
    # Example: Instagram + Instagram profile URL
    top_bar_social_1_name: Optional[str] = None
    top_bar_social_1_url: Optional[str] = None

    # Social media link 2
    # Example: YouTube + YouTube channel URL
    top_bar_social_2_name: Optional[str] = None
    top_bar_social_2_url: Optional[str] = None

    top_bar_social_3_name: Optional[str] = None
    top_bar_social_3_url:  Optional[str] = None

    top_bar_social_4_name: Optional[str] = None
    top_bar_social_4_url:  Optional[str] = None

    # ============================================================
    # Contact information
    # ============================================================

    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    company_address: Optional[str] = None
    address_url: Optional[str] = None

    # ============================================================
    # Homepage featured collections
    # ============================================================

    featured_international: Optional[list[str]] = None
    featured_national: Optional[list[str]] = None


class SiteSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # ============================================================
    # Website / marketing settings
    # ============================================================

    offer_banner_text: Optional[str]
    homepage_headline: Optional[str]
    trust_line: Optional[str]

    # ============================================================
    # Top Info Bar
    # ============================================================

    top_bar_enabled: Optional[bool]

    top_bar_location_1: Optional[str]
    top_bar_location_2: Optional[str]

    top_bar_traveller_text: Optional[str]

    top_bar_social_1_name: Optional[str]
    top_bar_social_1_url: Optional[str]

    top_bar_social_2_name: Optional[str]
    top_bar_social_2_url: Optional[str]

    top_bar_social_3_name: Optional[str] = None
    top_bar_social_3_url:  Optional[str] = None
    
    top_bar_social_4_name: Optional[str] = None
    top_bar_social_4_url:  Optional[str] = None

    # ============================================================
    # Contact information
    # ============================================================

    phone_number: Optional[str]
    whatsapp_number: Optional[str]
    company_address: Optional[str]
    address_url: Optional[str]

    # ============================================================
    # Homepage featured collections
    # ============================================================

    featured_international: Optional[list[str]]
    featured_national: Optional[list[str]]

    # ============================================================
    # Metadata
    # ============================================================

    updated_at: Optional[datetime]
