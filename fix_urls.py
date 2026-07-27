import os
import glob

def fix_hardcoded_urls(directory):
    for filepath in glob.glob(os.path.join(directory, '**', '*.tsx'), recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'http://localhost:8000' in content:
            print(f"Fixing {filepath}")
            # Replace string literals
            content = content.replace('"http://localhost:8000', '`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}` + "')
            # Replace template literals
            content = content.replace('`http://localhost:8000/', '`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

fix_hardcoded_urls('C:/Users/vedaa/OneDrive/Desktop/resume-project/github/frontend/src')
