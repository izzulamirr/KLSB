from app import create_app
import re

app = create_app()
client = app.test_client()
resp = client.get('/services')

print(f'Status: {resp.status_code}')

html = resp.data.decode()

# Find the hero background URL
bg_match = re.search(r'background-image:\s*url\([\'"]([^\'"]+)[\'"]', html)
if bg_match:
    print(f'Hero BG URL found: {bg_match.group(1)}')
else:
    print('Hero BG URL: NOT FOUND in HTML')

# Find the section with hero
section_start = html.find('<section class="relative min-h-')
if section_start != -1:
    section_end = html.find('</section>', section_start) + 10
    section_html = html[section_start:section_end]
    print('\nHero section HTML (first 600 chars):')
    print(section_html[:600])
else:
    print('Hero section not found')
