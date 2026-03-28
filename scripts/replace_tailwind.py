import os
import re

public_dir = r"c:\imf\habitacion\public"
cdn_pattern = re.compile(r'<script\s+src="https://cdn\.tailwindcss\.com[^"]*"></script>', re.IGNORECASE)
replacement = '<link rel="stylesheet" href="/css/tailwind.css">'

for root, dirs, files in os.walk(public_dir):
    for file in files:
        if file.endswith(".html"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if cdn_pattern.search(content):
                new_content = cdn_pattern.sub(replacement, content)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated: {file_path}")
