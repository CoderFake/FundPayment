from django import template
register = template.Library()

@register.filter(name='filter_fund')
def filter_fund(year_funds, month):
   try:
       if not year_funds:
           return None
       month = int(month)
       for fund in year_funds:
           if fund.month == month:
               return fund
       return None
   except (ValueError, TypeError):
       return None


@register.filter(name='format_price')
def format_price(value):
   try:
       if value is None:
           return '0'
       return '{:,.0f}'.format(float(value)).replace(',', '.')
   except (ValueError, TypeError):
       return '0'