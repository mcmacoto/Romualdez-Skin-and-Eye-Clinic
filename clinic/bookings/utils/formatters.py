from django.utils.html import format_html

def format_currency(amount):
    return f"{amount:,.2f}"

def format_status_badge(status):
    colors = {'Pending': 'warning', 'Confirmed': 'info', 'Completed': 'success', 'Cancelled': 'danger'}
    color = colors.get(status, 'secondary')
    return format_html('<span class="badge badge-{}">{}</span>', color, status)

def format_colored_text(text, color='black'):
    return format_html('<span style="color: {}">{}</span>', color, text)

def format_image_preview(image_url, width=100):
    if image_url:
        return format_html('<img src="{}" width="{}" />', image_url, width)
    return 'No image'

def get_status_color(status):
    colors = {'Pending': 'orange', 'Confirmed': 'blue', 'Completed': 'green', 'Cancelled': 'red'}
    return colors.get(status, 'gray')
