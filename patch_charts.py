import os
import glob
import re

files_to_patch = glob.glob('src/**/*.py', recursive=True)

for path in files_to_patch:
    if not os.path.isfile(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Ensure streamlit is imported if we are using st.session_state
    if 'st.session_state' not in content and ('template="plotly_' in content or "template='plotly_" in content or "color='black'" in content or "color='white'" in content):
        if 'import streamlit as st' not in content:
            content = 'import streamlit as st\n' + content

    # Step 2: Replace hardcoded templates
    content = re.sub(
        r"template\s*=\s*['\"]plotly_white['\"]", 
        "template=\"plotly_dark\" if st.session_state.get(\"theme\", \"dark\") == \"dark\" else \"plotly_white\"", 
        content
    )
    content = re.sub(
        r"template\s*=\s*['\"]plotly_dark['\"]", 
        "template=\"plotly_dark\" if st.session_state.get(\"theme\", \"dark\") == \"dark\" else \"plotly_white\"", 
        content
    )
    
    # Step 3: Replace hardcoded colors (black -> white in dark mode)
    # We only want to target specific traces, so let's target color='black' or color='white' inside dicts
    content = re.sub(
        r"color\s*=\s*['\"]black['\"]", 
        "color=\"white\" if st.session_state.get(\"theme\", \"dark\") == \"dark\" else \"black\"", 
        content
    )
    content = re.sub(
        r"color\s*=\s*['\"]white['\"]", 
        "color=\"white\" if st.session_state.get(\"theme\", \"dark\") == \"dark\" else \"black\"", 
        content
    )
    
    # Step 4: Write back
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patching complete!")
