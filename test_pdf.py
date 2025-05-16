from flask import render_template
import pdfkit

rendered = render_template("laporan.html", data=123)
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
pdf = pdfkit.from_string(rendered, False, configuration=config)