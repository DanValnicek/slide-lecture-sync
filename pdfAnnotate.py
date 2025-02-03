import fitz  # PyMuPDF

def add_hybrid_link_to_pdf(input_pdf, output_pdf, classic_url, custom_uri, link_text):
    """
    Adds a JavaScript OpenAction (custom URI) and a classic link (fallback URL).
    The JavaScript runs when the PDF is opened (Adobe Acrobat), and the classic link works in all viewers.
    """
    # Open the input PDF
    doc = fitz.open(input_pdf)

    # --- Add JavaScript OpenAction (triggers when PDF is opened) ---
    # Create JavaScript action object
    xref = doc.get_new_xref()  # Get new xref for the action object
    js = f"app.launchURL('{custom_uri}', true);"  # Custom URI scheme
    objsource = f"<<\n/Type/Action\n/S/JavaScript\n/JS({js})\n>>"  # PDF object syntax
    doc.update_object(xref, objsource)  # Insert the JavaScript action object

    # Update the PDF catalog to point to this action
    cat = doc.pdf_catalog()  # Get xref of the catalog
    doc.xref_set_key(cat, "OpenAction", f"{xref} 0 R")  # Set OpenAction

    # --- Add classic link (fallback for non-Adobe viewers) ---
    for page in doc:
        # Define link position (bottom-left corner)
        rect = fitz.Rect(20, page.rect.height - 30, 200, page.rect.height - 10)

        # Add link text
        page.insert_text(
            (25, page.rect.height - 15),  # Text position
            link_text,
            fontsize=12,
            fontname="helv",
            color=(0, 0, 1),  # Blue
        )

        # Add classic URL link
        page.insert_link({
            "kind": fitz.LINK_URI,
            "from": rect,
            "uri": classic_url,  # Fallback URL
        })

    # Save the modified PDF
    doc.save(output_pdf)
    print(f"PDF saved to {output_pdf}. Open in Adobe Acrobat for custom URI, or use classic link.")
input_pdf = "C:\\Users\\danva\\PycharmProjects\\GeoFormer\\data\\pdfs\\grafy1.pdf"
output_pdf = "output.pdf"
link_url = "myscheme://C:\\Users\\danva\\PycharmProjects\\GeoFormer\\data\\videos\\IDM_2023-11-07_1080p.mp4/"  # Custom URI scheme
# link_url = "https://www.google.com"  # Custom URI scheme
link_text = "Click here for more information"

add_hybrid_link_to_pdf(input_pdf, output_pdf, link_url, link_url, link_text)
