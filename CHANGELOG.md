

0.6.3:

* Added `cadnano-neatprinted-json` CLI entry point to setup.py,
  and added `rsenv.origami.cadnano.cadnano_prettyprint` module. 
* Added `cadnano-diff-jsondata` CLI entry point to setup.py,
  and added `rsenv.origami.cadnano.cadnano_diff` module.


0.6.2:

* Added `cadnano-json-vstrands-hashes` CLI - create a hash of the "vstrands" 
  part of a cadnano JSON file, with and without staple strand colors.
* Added `cadnano-get-json-name`, `cadnano-set-json-name` and `cadnano-reset-json-name` CLIs, 
  for setting the "name" attribute of a cadnano file (now that I've created a 
  cadnano fork that doesn't update this on every save).


0.6.1: 

* Added `oil-diff` (order_independent_line_diff_cli) CLI tool incl. entry point.
* Added `pdf.pdf_from_jpgs` module with `pdf_from_image_files_cli()` click CLI.


0.6.0:

* Large refactoring of modules from `rsenv.seq` to new package `rsenv.origami`.
* Added `oligoset-file-hasher-cli` CLI tool.



0.5.0:

* Added `rsenv.labelprint` package with modules for printing zpl labels on Zebra label printer.
* Added `print-zpl-labels` CLI entry point in `setup.py`.


0.2.7:

* Added module `rsenv.seq.oligomanagement.IDT_coa_to_platelibrary_file`
  and setup.py CLI `convert_IDT_espec_to_platelibrary_file_cli`.
* Renamed `click_cli_cmd_utils` module to `cli_cmd_utils` and 
  `create_click_command` function to `create_click_cli_command`.


0.2.6:

* Added `generic_text_extraction` module and `generic_text_extractor_cli`, 
    which is basically just "grep", but with support for a yaml-based parameter input file that can be stored locally. 
    I use this for extracting order numbers from HTML copy/pasted from IDT orderstatus page.
* Added `generic_batch_download` module and `generic_batch_downloader_cli`. 
    I used to download a bunch of coa.csv files from IDT.

Note that I already had idt_download_especs_v2 module, but I prefer the simplicity and generality 
that comes from splitting the "text extraction" from "file download", especially since IDT is now 
using a very javascript-heavy website, which made it difficult to produce a unified solution anyways.


0.2.5:

* Added `rsenv.utils.hash_utils` module and `sha256sum` and `sha256setsum` CLI entry-points.
