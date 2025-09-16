import dash
from dash import dcc, html

# Help page sections configuration
HELP_SECTIONS = [
    ("login", "Login", "Enter your Project ID and password, then click Login."),
    ("session", "Session Management", "Clone, delete, and view details of your sessions."),
    ("runfile", "Runfile Management", "Select runfiles from your project to submit jobs and check status."),
    ("table", "Table Management", "Clone, delete, and edit rows in your runfiles."),
    ("single-row", "Single Row Edit", "Click on any row to edit individual entries and save changes."),
    ("multi-row", "Multiple Row Edit", "Select multiple rows to make bulk changes efficiently."),
    ("submit", "Submit Job", "Configure parameters and submit jobs with email notifications."),
    ("status", "Job Status", "Monitor running jobs, check completion status, and view results.")
]

# Image mapping for each section
SECTION_IMAGES = {
    "login": "assets/img/app_login.png",
    "session": "assets/img/app_session_list.png", 
    #"runfile": "assets/img/app_runfile_edit.png",
    "table": "assets/img/app_edit_row.png",
    "single-row": "assets/img/app_single_row_parameter.png",
    "multi-row": "assets/img/app_multi_row_parameter.png",
    "submit": "assets/img/app_submit_job.png",
    #"status": "assets/img/app_job_status.png"
}

# Layout options: 'below' or 'side'
IMAGE_LAYOUT = 'below'  # Change this to 'side' to see the alternative

def create_table_of_contents():
    """Generate the table of contents navigation."""
    return html.Div([
        html.H3("Contents", className="help-toc-title"),
        html.Ul([
            html.Li(
                html.A(title, href=f"#{section_id}", className="help-toc-link")
            )
            for section_id, title, _ in HELP_SECTIONS
        ], className="help-toc-list")
    ], className="help-toc")

def create_help_section(section_id, title, description):
    """Create a help section with configurable image layout."""
    
    if IMAGE_LAYOUT == 'below':
        # Option 1: Image below text (full width, larger)
        content = [
            html.P(description, className="help-paragraph"),
        ]
        
        if section_id in SECTION_IMAGES:
            content.append(
                html.Img(
                    src=SECTION_IMAGES[section_id], 
                    alt=f"{title} Screenshot",
                    className="help-image-full-width"
                )
            )
        
        return html.Div([
            html.H3(title, id=section_id, className="help-section-title"),
            html.Div(content, className="help-section-content")
        ], className="help-section")
    
    else:  # 'side' layout
        # Option 2: Image to the right (wider than original)
        text_content = html.Div([
            html.P(description, className="help-paragraph")
        ], className="help-text-col-wide")
        
        content = [text_content]
        
        if section_id in SECTION_IMAGES:
            image_content = html.Div([
                html.Img(
                    src=SECTION_IMAGES[section_id], 
                    alt=f"{title} Screenshot",
                    className="help-image-side-wide"
                )
            ], className="help-image-col-wide")
            content.append(image_content)
        
        return html.Div([
            html.H3(title, id=section_id, className="help-section-title"),
            html.Div(content, className="help-section-row")
        ], className="help-section")

def create_layout():
    """Build the complete help page layout."""
    return html.Div([
        html.Div([
            # Page header
            html.H2("Help Documentation", className="help-title"),
            html.Hr(className="help-separator"),
            
            
            # Main content grid
            html.Div([
                # Left sidebar with table of contents
                html.Div([
                    create_table_of_contents()
                ], className="help-left-col"),
                
                # Right content area with help sections
                html.Div([
                    create_help_section(section_id, title, description)
                    for section_id, title, description in HELP_SECTIONS
                ], className="help-right-col")
                
            ], className="help-main-grid")
        ], className="help-container")
    ])

# Export the layout
layout = create_layout()