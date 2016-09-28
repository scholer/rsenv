


Typical procedure for CoA files:
--------------------------------

First, download "certificate" CSV files using ```idt_download_especs```.
     
Then use ```reformat_coa_seq``` to reformat DNA sequence fields.

Now you can use grep or whatever to search for sequences.


Producedure for order sheets:
-----------------------------

Download Excel files using wiki_file_downloader module, if needed.

Then use ```convert_idt_xlsx_order_to_csv``` to convert Excel files to csv.
(This module will remove the "order" header and only include the actual sequences in the csv output.



