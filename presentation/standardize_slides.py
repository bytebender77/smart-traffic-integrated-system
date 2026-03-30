import os
import re

folder = "/Users/kunalkumargupta/Desktop/final/integrated-system/presentation"

standard_head_top = """    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>Smart Mobility Presentation</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&amp;family=Space+Grotesk:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>"""

nav_script_template = """
    <script>
        document.addEventListener('keydown', function(event) {
            const currentPath = window.location.pathname;
            const currentFile = currentPath.substring(currentPath.lastIndexOf('/') + 1) || '1.html';
            const currentNum = parseInt(currentFile.split('.')[0]) || 1;
            let nextNum;
            if (event.code === 'ArrowRight' || event.code === 'Space') {
                nextNum = currentNum + 1;
                if (nextNum <= 14) window.location.href = nextNum + '.html';
            } else if (event.code === 'ArrowLeft') {
                nextNum = currentNum - 1;
                if (nextNum >= 1) window.location.href = nextNum + '.html';
            }
        });
    </script>
"""

# Common CSS fixes
def fix_css(content):
    content = content.replace("'Orbitron'", "'Space Grotesk'")
    content = content.replace('"Orbitron"', "'Space Grotesk'")
    content = content.replace("'Rajdhani'", "'Inter'")
    content = content.replace('"Rajdhani"', "'Inter'")
    
    # Standardize body CSS with explicit white color
    content = re.sub(r'body\s*{[^}]*}', 'body { margin: 0; padding: 0; overflow: hidden; font-family: "Inter", sans-serif; background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%); width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; color: white; }', content, flags=re.DOTALL)
    
    # Standardize .slide-container CSS
    content = re.sub(r'\.slide-container\s*{[^}]*}', '.slide-container { position: relative; width: 100%; height: 100%; max-width: 1280px; max-height: 720px; overflow: hidden; background: radial-gradient(ellipse at center, #0f172a 0%, #020617 100%); box-shadow: 0 0 100px rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.05); }', content, flags=re.DOTALL)
    
    # Ensure p tags or other text elements don't default to black
    if 'p {' not in content and 'p{' not in content:
        content += "\n        p { margin: 0; color: white; }"
    else:
        content = re.sub(r'p\s*{[^}]*}', 'p { margin: 0; color: inherit; }', content)

    return content

for i in range(1, 15):
    filepath = os.path.join(folder, f"{i}.html")
    if not os.path.exists(filepath): continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract existing <style> content
    styles = re.findall(r'<style>(.*?)</style>', content, flags=re.DOTALL | re.IGNORECASE)
    cleaned_styles = [fix_css(s) for s in styles]
    
    # Build new head
    new_head = f"<head>\n{standard_head_top}\n"
    for s in cleaned_styles:
        new_head += f"    <style>{s}</style>\n"
    new_head += "</head>"
    
    content = re.sub(r'<head>.*?</head>', new_head, content, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract core body content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, flags=re.DOTALL | re.IGNORECASE)
    if body_match:
        inner = body_match.group(1)
        # Remove our previously added wraps and scripts
        inner = re.sub(r'<div class="slide-container"[^>]*>', '', inner)
        inner = re.sub(r'<div style="position: relative; width: 100%; height: 100%; max-width: 1280px; max-height: 720px;">', '', inner)
        inner = re.sub(r'<div style="position: relative; width: 100%; height: 100%;">', '', inner)
        
        # Cleanup nested closing divs from previous script runs
        # We'll just count </div> and hope for the best, or better: use a simpler approach
        inner = inner.replace('</div>\n    </div>', '') 
        inner = inner.replace('</div>\n        </div>\n    </div>', '')
        
        # Actually, simpler: find the first <div> and take everything till the last </div> before the script
        inner = re.sub(r'<script>.*?document\.addEventListener\(.*?keydown.*?</script>', '', inner, flags=re.DOTALL)
        
        # Final standardized body structure
        final_body = f"""
<body>
    <div class="slide-container">
        <div style="position: relative; width: 100%; height: 100%;">
            {inner.strip()}
        </div>
    </div>
    {nav_script_template}
</body>
"""
        content = re.sub(r'<body[^>]*>.*?</body>', final_body, content, flags=re.DOTALL | re.IGNORECASE)

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Standardized {filepath}")
