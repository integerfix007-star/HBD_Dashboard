import os
import markdown
from playwright.sync_api import sync_playwright

def convert_md_to_pdf(md_file_path, pdf_file_path):
    # Read the markdown file
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert markdown to html
    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'toc'])

    # Add some basic styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 4px;
                font-family: 'Courier New', Courier, monospace;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 8px;
                overflow-x: auto;
                border: 1px solid #ddd;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #f8f9fa;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 20px;
                color: #555;
                font-style: italic;
                margin: 20px 0;
            }}
            .toc {{
                background: #f9f9f9;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Use Playwright to generate PDF
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(full_html)
        # Wait for any potential rendering
        page.wait_for_timeout(1000)
        page.pdf(path=pdf_file_path, format="A4", margin={
            "top": "20mm",
            "bottom": "20mm",
            "left": "20mm",
            "right": "20mm"
        })
        browser.close()

if __name__ == "__main__":
    import os
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Files in CWD: {os.listdir('.')}")
    
    # Try current directory and parent directory
    possible_paths = [
        "FULL_SYSTEM_DOCUMENTATION.md",
        "../FULL_SYSTEM_DOCUMENTATION.md",
        "backend/FULL_SYSTEM_DOCUMENTATION.md"
    ]
    
    md_path = None
    for p in possible_paths:
        print(f"Checking {p}...")
        if os.path.exists(p):
            md_path = p
            print(f"Found at {p}!")
            break
            
    if not md_path:
        print(f"❌ Error: Source file not found in any of {possible_paths}")
    else:
        pdf_path = md_path.replace(".md", ".pdf")
        print(f"Converting {os.path.abspath(md_path)} to {os.path.abspath(pdf_path)}...")
        try:
            convert_md_to_pdf(md_path, pdf_path)
            print("✅ Conversion successful!")
        except Exception as e:
            print(f"❌ Error during conversion: {e}")



