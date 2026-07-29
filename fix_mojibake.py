import os

replacements = {
    'ðŸ” ': '🔍',
    'â€º': '›',
    'ðŸ“‚': '📂',
    'â ¤': '❤',
    'â™¡': '♡',
    'ðŸ“º': '📺',
    'ðŸŽ¬': '🎬'
}

def fix_mojibake(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    original = text
                    for bad, good in replacements.items():
                        text = text.replace(bad, good)
                    
                    if text != original:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(text)
                        print('Fixed string replacements in:', path)
                except Exception as e:
                    pass

fix_mojibake('app/templates')
