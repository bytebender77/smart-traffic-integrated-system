import os

folder = "/Users/kunalkumargupta/Desktop/final/integrated-system/presentation"
nav_script = """
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

for i in range(1, 15):
    filepath = os.path.join(folder, f"{i}.html")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Simple check: if already has 1.html reference, skip
        if "window.location.href = nextNum + '.html'" in content:
            continue
            
        if '</body>' in content:
            new_content = content.replace('</body>', nav_script + '</body>')
            with open(filepath, 'w') as f:
                f.write(new_content)
                print(f"Updated {filepath}")
