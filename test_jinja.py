from jinja2 import Environment
env = Environment()
t = env.from_string("{% if banner.image_url and 'default-banner.svg' not in banner.image_url %}YES{% else %}NO{% endif %}")
try:
    print(t.render(banner={'image_url': None}))
except Exception as e:
    import traceback
    traceback.print_exc()
