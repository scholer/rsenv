


"""

Notes:
* You can export form data from a PDF in Acrobat X with "Tools (panel) -> Forms -> More options -> Export data".
    Available options are: FDF, XFDF, XML, and text.

Regarding FDF/XFDF format:
* https://docs.aspose.com/display/pdfnet/Whats+the+Difference+Between+XML%2C+FDF+and+XFDF
* FDF key-value format: /T(Company) /V(Aspose.com)
* XFDF field XML: <field name="Company"><value>Aspose.com</value></field>
* The only difference between XFDF and XML is that XFDF has a <f> tag that points to the corresponding PDF file,
    and an encapsulating <xfdf> tag with xml namespace definition.

Options for filling PDF forms:
* pypdftk
* pdfforms

Both options are basically just wrappers around pdftk command line binary.
* You need the "Server" version for command line usage: "PDFtk Server is our command-line tool [...]".
* There seems to be issues with the free pdftk binary not being maintained for OSX 10.11+.
* https://stackoverflow.com/questions/32505951/pdftk-server-on-os-x-10-11
* The above has link to official El Capitain build (10.11)::
    http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/pdftk_server-2.02-mac_osx-10.11-setup.pkg
* There is also a homebrew formula (which just uses the linked .pkg file)::
    brew install https://raw.githubusercontent.com/turforlag/homebrew-cervezas/master/pdftk.rb
* There is also a docker-based solution.
* Alternative python scripts for splitting and merging PDFs: https://github.com/flexpaper/OSX-PDF-Toolkit
* Installed pkg seems to work::
    $ pdftk --version
    $ man pdftk


PyPDFTk:
* https://github.com/revolunet/pypdftk
* "Python module to drive the awesome pdftk binary."
* Features: fill_form, concat, split, etc.
* fill_form: Create xfdf file from csv, then invoke ``$ pdftk input.pdf fill_form data.fdf output.pdf``.
* Does not provide a CLI entry point, you have to do it in python.


pdfforms:
* https://github.com/altaurog/pdfforms
* CLI entry point ``pdfforms`` with commands: inspect, fill::
    $ pdfforms inspect input.pdf
    $ pdfforms fill input.pdf
* Read input csv and field defs json, generate fdf file, invoke ``$ pdftk input.pdf fill_form - output.pdf``.
* The fields.json file defines the corresponding PDF file! (A little weird, but consistent with the FDF format)
* Basically a two-step process:
    1. Inspect input pdf, generate field defs json file with a unique numeric ID for every field.
    2. Input CSV has unique number, fdf_fields(fields, data) translates::
        field_name = fields[unique_number]["name"]
        field_value = data[unique_number]
        yield f"<< /T ({field_name}) /V ({field_value}) >>"
* Differences vs pypdftk:
    a. pypdftk writes fdf to a temp file, pdfforms inputs via stdin.
    b. pypdftk uses XFDF, pdfforms uses old FDF format.
* OBS:


fdfgen:
* https://github.com/ccnmtl/fdfgen
* Only focuses on generating (and modifying) FDF files from CSV files.
* Manually invoke pdftk on the generated FDF files (or just import using Adobe Acrobat).
* Python only, does not have any readily available CLI entry points.
* But I guess that is a-OK, since I want to update e.g. date.
* Also note: The two "date" fields are different, one for filing date (top), others for date(s) of expenditure,
    and a final one next to the signature.



pdfformfiller:
* https://github.com/diafygi/pdfformfiller
* "Insert text into existing pdfs. Usefull for filling out pdf forms."
* Not really for forms, more for templates.



"""
