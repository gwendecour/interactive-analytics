import os
import glob
import re

files_to_patch = glob.glob('src/**/*.py', recursive=True)

# The correct expressions we want
correct_template = 'template="plotly_dark" if st.session_state.get("theme", "dark") == "dark" else "plotly_white"'
correct_color = 'color="white" if st.session_state.get("theme", "dark") == "dark" else "black"'

for path in files_to_patch:
    if not os.path.isfile(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Clean up any mangled template strings from previous bad regex
    # Match any template assignment that looks like it got duplicated or messed up
    # We'll just replace everything after 'template=' up to the comma or newline
    # This regex is a bit dangerous, so let's be more specific:
    # Find all instances of template="..." or template='...' or template=... if ... else ...
    content = re.sub(r'template\s*=\s*["\']plotly_dark["\'](?:\s*if.*?else.*?["\']plotly_white["\'])*(?:\s*if.*?else.*?["\']plotly_white["\'])*', correct_template, content)
    content = re.sub(r'template\s*=\s*["\']plotly_white["\'](?:\s*if.*?else.*?["\']plotly_white["\'])*(?:\s*if.*?else.*?["\']plotly_white["\'])*', correct_template, content)
    
    # Step 2: Clean up any mangled color strings
    content = re.sub(r'color\s*=\s*["\']white["\'](?:\s*if.*?else.*?["\']black["\'])*(?:\s*if.*?else.*?["\']black["\'])*', correct_color, content)
    content = re.sub(r'color\s*=\s*["\']black["\'](?:\s*if.*?else.*?["\']black["\'])*(?:\s*if.*?else.*?["\']black["\'])*', correct_color, content)
    
    # Step 3: Write back
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patching complete 2!")
