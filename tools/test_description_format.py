import os
import sys

# Make sure project root is on sys.path so Django settings package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure project's settings module is available
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')
try:
    import django
    django.setup()
except Exception as e:
    print('Failed to setup Django:', e)
    sys.exit(1)

from bookings.templatetags.description_filters import format_service_description

sample = '''Unlock your brightest, healthiest-looking skin with our Glutathione Injection.

Often called the body's "master antioxidant," glutathione is a powerful nutrient that combats oxidative stress, detoxifies the body, and promotes a brighter, more even skin tone from within.

While our bodies produce glutathione naturally, levels can be depleted by stress, aging, and environmental toxins. Our Glutathione Injection delivers this vital antioxidant directly for high absorption, bypassing the digestive system for maximum effectiveness.

This treatment is ideal for:
• Achieving a luminous, "lit-from-within" glow
• Reducing the appearance of hyperpigmentation and dark spots
• Supporting your body's natural detoxification processes
• Boosting your immune system and energy levels
• Protecting against free radical damage that causes signs of aging

What to Expect: The service is a quick and simple intramuscular (IM) injection, administered in just a few minutes by one of our certified medical professionals. For best results, a series of treatments is typically recommended.
'''

html = format_service_description(sample)
print(html)
