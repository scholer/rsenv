# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""


Alternative ways of creating a PDF from a list of image files:

1. Windows Photos app -> Select photos -> Print to PDF.
2. Mac Preview -> Open photos -> Print to PDF.
3. On Android: Use Images to PDF converter app (Play Store).
4. Lots of other tools and web-apps - search google.





"""

import sys
import click
from fpdf import FPDF
from PIL import Image


@click.command()
@click.argument("inputfile", "inputfiles", multiple=True)
@click.option("--outputfn", "-o", default="output.pdf")
def pdf_from_image_files_cli(inputfiles, outputfn="output.pdf"):
    """ Make a PDF from a list of filenames.

    Adapted from https://stackoverflow.com/questions/27327513/create-pdf-from-a-list-of-images

    Args:
        inputfiles:
        outputfn:

    Returns:

    """

    if not inputfiles:
        print("No input files provides; cannot produce PDF output", file=sys.stderr)

    pdf = FPDF(unit="pt", format=Image.open(inputfiles[0]).size)

    for imgfn in inputfiles:
        # Append a new page and insert the image on the page top-left position.
        pdf.add_page()
        pdf.image(imgfn, 0, 0)

    if outputfn == "-":
        s = pdf.output(outputfn, "S")
        sys.stdout.write(s)

    pdf.output(outputfn, "F")
