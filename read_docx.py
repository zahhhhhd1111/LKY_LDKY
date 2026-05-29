import zipfile
import re
import sys

path = r'C:\4code\3lot\软著代码.docx'
try:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        sys.stdout.write("Files: " + str(names) + "\n")
        if 'word/document.xml' in names:
            with z.open('word/document.xml') as f:
                content = f.read().decode('utf-8')
            text = re.sub(r'<[^>]+>', '', content)
            text = re.sub(r'\s+', ' ', text).strip()
            sys.stdout.write("Length: " + str(len(text)) + "\n")
            sys.stdout.write(text[:5000] + "\n")
        else:
            sys.stdout.write("No document.xml found\n")
except Exception as e:
    sys.stdout.write("Error: " + str(e) + "\n")

sys.stdout.flush()
