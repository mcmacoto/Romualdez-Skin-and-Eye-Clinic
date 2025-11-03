import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')
django.setup()

from bookings.templatetags.description_filters import format_service_description

# Test the filter with sample text
test_text = """Unlock your brightest, healthiest-looking skin with our Glutathione Injection.

Often called the body's "master antioxidant," glutathione is a powerful nutrient that combats oxidative stress, detoxifies the body, and promotes a brighter, more even skin tone from within.

While our bodies produce glutathione naturally, levels can be depleted by stress, aging, and environmental toxins. Our Glutathione Injection delivers this vital antioxidant directly for high absorption, bypassing the digestive system for maximum effectiveness.

This treatment is ideal for:
• Achieving a luminous, "lit-from-within" glow
• Reducing the appearance of hyperpigmentation and dark spots
• Supporting your body's natural detoxification processes
• Boosting your immune system and energy levels
• Protecting against free radical damage that causes signs of aging

What to Expect: The service is a quick and simple intramuscular (IM) injection, administered in just a few minutes by one of our certified medical professionals. For best results, a series of treatments is typically recommended."""

print("=== FORMATTED OUTPUT ===")
print(format_service_description(test_text))
print("\n=== TEST COMPLETE ===")
