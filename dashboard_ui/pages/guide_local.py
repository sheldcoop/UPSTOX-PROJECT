"""
Local Development Guide Page
Displays the LOCAL_DEVELOPMENT.md content within the NiceGUI dashboard
"""

from nicegui import ui
from pathlib import Path
import markdown


def create_page():
    """Create the Local Development Guide page"""
    
    # Read the LOCAL_DEVELOPMENT.md file
    local_dev_path = Path(__file__).parent.parent.parent / "docs" / "LOCAL_DEVELOPMENT.md"
    
    try:
        with open(local_dev_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['fenced_code', 'tables', 'codehilite']
        )
        
    except FileNotFoundError:
        html_content = """
        <div style="color: red; padding: 20px; border: 2px solid red; border-radius: 5px;">
            <h2>⚠️ Error: Documentation Not Found</h2>
            <p>The file <code>docs/LOCAL_DEVELOPMENT.md</code> could not be found.</p>
            <p>Please ensure the documentation is present in the repository.</p>
        </div>
        """
    except Exception as e:
        html_content = f"""
        <div style="color: red; padding: 20px; border: 2px solid red; border-radius: 5px;">
            <h2>⚠️ Error Loading Documentation</h2>
            <p>An error occurred while loading the documentation:</p>
            <pre>{str(e)}</pre>
        </div>
        """
    
    # Page layout
    with ui.column().classes('w-full gap-4 p-4'):
        # Header
        with ui.card().classes('w-full'):
            ui.html("""
                <div style="text-align: center; padding: 10px;">
                    <h1 style="color: #2563eb; margin: 0;">
                        🛠️ Local Development Guide
                    </h1>
                    <p style="color: #6b7280; margin-top: 5px;">
                        Complete setup and development workflow documentation
                    </p>
                </div>
            """)
        
        # Quick Actions Card
        with ui.card().classes('w-full'):
            with ui.row().classes('gap-2 items-center'):
                ui.label('Quick Actions:').classes('text-lg font-semibold')
                
                ui.button(
                    'Open in Editor',
                    icon='edit',
                    on_click=lambda: ui.notify(
                        f'Open {local_dev_path} in your editor',
                        type='info'
                    )
                ).props('flat color=primary')
                
                ui.button(
                    'View on GitHub',
                    icon='open_in_new',
                    on_click=lambda: ui.open(
                        'https://github.com/sheldcoop/UPSTOX-PROJECT/blob/main/docs/LOCAL_DEVELOPMENT.md',
                        new_tab=True
                    )
                ).props('flat color=primary')
                
                ui.button(
                    'Refresh',
                    icon='refresh',
                    on_click=lambda: ui.open('/guide-local')
                ).props('flat color=primary')
        
        # Documentation Content
        with ui.card().classes('w-full'):
            # Custom CSS for better markdown rendering
            ui.html("""
                <style>
                    .markdown-content {
                        line-height: 1.6;
                        color: #333;
                    }
                    .markdown-content h1 {
                        color: #2563eb;
                        border-bottom: 2px solid #2563eb;
                        padding-bottom: 10px;
                        margin-top: 20px;
                    }
                    .markdown-content h2 {
                        color: #1e40af;
                        border-bottom: 1px solid #e5e7eb;
                        padding-bottom: 8px;
                        margin-top: 30px;
                    }
                    .markdown-content h3 {
                        color: #1e3a8a;
                        margin-top: 20px;
                    }
                    .markdown-content code {
                        background: #f3f4f6;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9em;
                    }
                    .markdown-content pre {
                        background: #1e293b;
                        color: #e2e8f0;
                        padding: 15px;
                        border-radius: 5px;
                        overflow-x: auto;
                        margin: 15px 0;
                    }
                    .markdown-content pre code {
                        background: none;
                        padding: 0;
                        color: #e2e8f0;
                    }
                    .markdown-content table {
                        border-collapse: collapse;
                        width: 100%;
                        margin: 15px 0;
                    }
                    .markdown-content table th {
                        background: #f3f4f6;
                        padding: 10px;
                        text-align: left;
                        border: 1px solid #e5e7eb;
                    }
                    .markdown-content table td {
                        padding: 8px;
                        border: 1px solid #e5e7eb;
                    }
                    .markdown-content ul, .markdown-content ol {
                        margin: 10px 0;
                        padding-left: 30px;
                    }
                    .markdown-content li {
                        margin: 5px 0;
                    }
                    .markdown-content a {
                        color: #2563eb;
                        text-decoration: none;
                    }
                    .markdown-content a:hover {
                        text-decoration: underline;
                    }
                    .markdown-content blockquote {
                        border-left: 4px solid #2563eb;
                        margin: 15px 0;
                        padding: 10px 20px;
                        background: #f9fafb;
                    }
                    .markdown-content hr {
                        border: none;
                        border-top: 2px solid #e5e7eb;
                        margin: 30px 0;
                    }
                </style>
            """)
            
            # Render the markdown content
            with ui.scroll_area().classes('w-full h-[70vh]'):
                ui.html(f'<div class="markdown-content">{html_content}</div>')
        
        # Footer with helpful links
        with ui.card().classes('w-full'):
            with ui.row().classes('gap-4 items-center justify-center'):
                ui.label('Related Documentation:').classes('font-semibold')
                
                ui.link('Testing Guide', '/guide').classes('text-blue-600')
                ui.label('|')
                ui.link('Deployment', 'https://github.com/sheldcoop/UPSTOX-PROJECT/blob/main/docs/DEPLOYMENT.md').classes('text-blue-600')
                ui.label('|')
                ui.link('API Endpoints', 'https://github.com/sheldcoop/UPSTOX-PROJECT/blob/main/docs/ENDPOINTS.md').classes('text-blue-600')
                ui.label('|')
                ui.link('Project Status', 'https://github.com/sheldcoop/UPSTOX-PROJECT/blob/main/PROJECT_STATUS.md').classes('text-blue-600')


if __name__ == '__main__':
    # Test the page standalone
    create_page()
    ui.run(title='Local Development Guide', port=8888)
