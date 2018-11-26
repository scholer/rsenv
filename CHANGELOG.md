
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
