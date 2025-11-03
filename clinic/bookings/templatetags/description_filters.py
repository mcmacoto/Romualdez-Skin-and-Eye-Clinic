from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re

register = template.Library()


@register.filter(is_safe=True)
def format_service_description(value):
    """Format a plain-text service description into HTML.

    - Paragraphs are separated by one or more blank lines and become <p>...</p>.
    - Consecutive lines that start with bullet markers (•, -, *, etc.) become <ul><li>...</li></ul>.
    - All content is HTML-escaped to avoid XSS, then marked safe.

    This keeps output predictable for admin-entered plain text descriptions.
    """
    if not value:
        return ''

    # Normalize line endings
    text = value.replace('\r\n', '\n').replace('\r', '\n')

    lines = text.split('\n')

    # Group into blocks separated by blank lines
    blocks = []
    current = []
    for line in lines:
        if line.strip() == '':
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)

    out_parts = []

    # Regex to detect bullet/list lines (common bullet chars and hyphen/star)
    bullet_re = re.compile(r'^[\s\u2022\u2023\u25E6\-\*\u2024\u2043]+')

    for block in blocks:
        # Check if this block has a mix of header + bullets (like "This is for:\n• item1\n• item2")
        bullet_lines = [line for line in block if bullet_re.match(line)]
        non_bullet_lines = [line for line in block if not bullet_re.match(line)]
        
        # If we have both bullet and non-bullet lines in the same block
        if bullet_lines and non_bullet_lines:
            # Render non-bullet lines as a paragraph first
            if non_bullet_lines:
                paragraph = ' '.join([ln.strip() for ln in non_bullet_lines])
                out_parts.append(f'<p>{escape(paragraph)}</p>')
            # Then render bullet lines as a list
            if bullet_lines:
                out_parts.append('<ul>')
                for line in bullet_lines:
                    item_text = bullet_re.sub('', line).strip()
                    out_parts.append(f'<li>{escape(item_text)}</li>')
                out_parts.append('</ul>')
        # If all lines in the block look like a list item, render a ul
        elif all(bullet_re.match(line) for line in block):
            out_parts.append('<ul>')
            for line in block:
                item_text = bullet_re.sub('', line).strip()
                out_parts.append(f'<li>{escape(item_text)}</li>')
            out_parts.append('</ul>')
        else:
            # Normal paragraph: join lines into one paragraph
            paragraph = ' '.join([ln.strip() for ln in block])
            out_parts.append(f'<p>{escape(paragraph)}</p>')

    return mark_safe('\n'.join(out_parts))
