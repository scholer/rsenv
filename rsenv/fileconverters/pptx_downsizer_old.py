# Copyright 2017, Rasmus S. Sorensen <rasmusscholer@gmail.com>

"""



    OBS! OLD MODULE - USE DEDICATED `pptx-downsizer` package instead!





Module for downsizing Microsoft PowerPoint presentations (pptx) files.

https://github.com/scholer/pptx_downsizer

Currently only supports downsizing of images (not e.g. videos).


Use cases:
----------

Why might someone want to downsize a Power Point presentation?

If you are like me, when you create a PowerPoint presentation,
you just throw in a lot of images on the slides without paying
too much attention to how large the images are.

You may even use the "screenshot" feature (Cmd+shift+4 on Mac)
to quickly capture images of whatever you have on your screen,
and paste it into the PowerPoint presentation (using "Paste special").
In which case you are actually creating large TIFF images in your presentation (at least for PowerPoint 2016).

Even though the images in the presentation are compressed/zipped when saving the presentation file,
the presentation will still be significantly larger than it actually needs to be.

However, once you realize that your presentation is 100+ MBs,
you don't have the time to re-save a lower-quality version of each image
and then substitute that image in the presentation.

Q: What to do?

A: First, use the built-in "Compress Pictures" feature:
Go "File -> Compress pictures", or select any image, go to the "Picture Tools" toolbar,
and select the "Compress Pictures" icon (four arrows pointing to the corners of an image).
This tool allows you to down-scale pictures and removed cropped-out areas,
and can be applied to all pictures in the presentation at once,
**but does not (currently) change the image format of pictures in the presentation.**

Make sure to save your presentation under a new name, in case you want to revert some of the compressed pictures!

A: Then, *use `pptx_downsizer`*!

`pptx_downsizer` will go over all images in your presentation (pptx),
and down-size all images above a certain size.

* By default, all images are converted to PNG format (except for JPEGs which remains in JPEG format).
* You can also choose to use JPEG format (recommended only after doing an initial downsizing using PNG).
* If images are more than a certain limit (default 2048 pixels) in either dimension (width, height),
they are down-scaled to a more reasonable size (you most likely do not need very high-resolution
images in your presentation, since most projectors still have a relatively low resolution anyways.)


Q: How much can I expect `pptx_downsizer` to reduce my powerpoint presentations (pptx files)?

A: If you have copy/pasted a lot of screenshots (TIFF files), it is not uncommon to for the presentation to
   be reduced to less than half (and in some case one fourth) of the original file size.
   If you further convert remaining large PNG images to JPEG (as a separate downsizing), you
   should be able to get another 30-50 percent reduction.
   Of course, this all depends on how large your original images are and how much you are willing to



Examples:
---------

Make sure to save your presentation (and, preferably exit PowerPoint,
and make a backup of your presentation just in case).

Let's say you have your original, large presentation saved as `Presentation.pptx`

After installing `pptx_downloader`, you can run the following from your terminal (command line):

    ```pptx_downsizer "Presentation.pptx"```

If you want to change the file size limit used to determine what images are down-sized to 1 MB (= 1'000'000 bytes):

    ```pptx_downsizer "Presentation.pptx" --fsize-filter 1e6```

If you want to disable down-scaling of large high-resolution images, set `img-max-size` to 0:

    ```pptx_downsizer "Presentation.pptx" --img-max-size 0```

If you want to convert large images to JPEG format:

    ```pptx_downsizer "Presentation.pptx" --convert-to jpeg```




Installation:
-------------

First, make sure you have Python 3+ installed. I recommend using the Anaconda Python distribution,
which makes everything a lot easier.


With python installed, install `pptx_downsizer` using `pip`:

    ```pip install pptx_downsizer```


You can make sure `pptx_downsizer` is installed by invoking it anywhere from the terminal (command line):

    ````pptx_downsizer```


Note: You may want to install `pptx_downsizer` in a separate/non-default python environment.
(If you know what that means, you already know how to do that.
If you do not know what that means, then don't worry–you probably don't need it after all).



Troubleshooting and bugs:
-------------------------

*NOTE: `pptx_downsizer` is very early/beta software. I strongly recommend to
(a) back up your presentation to a separate folder before running `pptx_downsizer`, and
(b) work for as long as possible in the original presentation.
That way, if `pptx_downsizer` doesn't work, you can always go back to your original presentation,
and you will not have lost any work.**


Q: HELP! I ran the downsizer and now the presentation won't open / PowerPoint gives errors when opening the pptx file!

A: Sorry that it didn't work for you.
    If you want, feel free to send me a copy of both the presentation
    and the downsized pptx file produced by this script, and I'll try to figure out what the problem is.
    There are, unfortunately, a lot of things that could be wrong,
    and without the original presentation, I probably cannot diagnose the issue.

**OBS: If PowerPoint gives you errors when opening the downsized file,
please don't bother trying to fix the downsized file yourself.
You may run into unexpected errors later.
Instead, just continue working with your original presentation.**


Q: Why doesn't `pptx_downsizer` work?

A: It works for me and all the `.pptx` files I've thrown at it.
   However, there are obviously going to be a lot of scenarios that I haven't run into yet.


Q: Does `pptx_downloader` overwrite the original presentation file?

A: No, by default `pptx_downloader` will create a new file with ".downsized" postfix.
    If the intended output already exists, `pptx_downloader` will let you know,
    giving you a change to (manually) move/rename the existing file if you want to keep it.
    You can disable this prompt using the `--overwrite` argument.





"""

# from __future__ import print_function
import sys
import os
import zipfile
import tempfile
from fnmatch import fnmatch
from glob import glob
from functools import partial
from PIL import Image
import argparse
import inspect
import yaml


def downsize_pptx_images(
    filename,
    outputfn_fmt="{fnroot}.downsized.pptx",  # "{filename}.downsized.pptx",
    convert_to="png",
    fn_filter=None,  # Only filter files matching this filter (str or callable or None) - or maybe OR filter?
    fsize_filter=int(0.5*2**20),  # Only downsample files above this filesize (number or None)
    img_max_size=2048,
    quality=90,
    optimize=True,
    overwrite=None,
    open_pptx=False,
    verbose=1,
    compress_type=zipfile.ZIP_DEFLATED,
    # **writer_kwargs
):
    # TODO: If output is .jpg, you may need to add the following line:
    # TODO      <Default Extension="jpeg" ContentType="image/jpeg"/>
    # TODO      <Default Extension="jpg" ContentType="application/octet-stream"/>

    # OBS: File endings should be \r\n, even on Mac - because MS software.
    assert os.path.isfile(filename)
    old_fsize = os.path.getsize(filename)
    pptx_fnroot, pptx_ext = os.path.splitext(filename)
    convert_to = convert_to.lower().strip(".")
    print("\nDownsizing PowerPoint presentation %r (%0.01f MB)...\n" % (filename, old_fsize/2**20))
    if convert_to == "jpg":
        print("WARNING: Selected format 'jpg' should be 'jpeg' instead, switching...")
        convert_to = "jpeg"
    filter_desc = []
    if fsize_filter:
        filter_desc.append("above %0.01f kB" % (fsize_filter/2**10,))
    if img_max_size:
        filter_desc.append("larger than %s pixels" % img_max_size)
    if fn_filter:
        filter_desc.append("with filename matching %r" % fn_filter)

    print(" - Converting image files", " or ".join(filter_desc))
    if isinstance(fn_filter, str):
        fn_filter = partial(fnmatch, pat=fn_filter)

    def ffilter(fname):
        """Return True if file should be included."""
        return (
            (fsize_filter and os.path.getsize(fname) > fsize_filter)
            and (fn_filter is None or fn_filter(fname))
        )

    output_ext = "." + convert_to.strip(".")
    changed_fns = []
    with tempfile.TemporaryDirectory() as tmpdirname:
        pptdir = os.path.join(tmpdirname, "ppt")
        mediadir = os.path.join(pptdir, "media")
        print("\nExtracting %r to temporary directory %r..." % (filename, tmpdirname))
        with zipfile.ZipFile(filename, 'r') as zipfd:
            zipfd.extractall(tmpdirname)
        print("pptdir:", pptdir)
        print("mediadir:", mediadir)
        image_files = glob(os.path.join(mediadir, "image*"))
        image_files = [fn for fn in image_files if ffilter(fn)]
        print("\nConverting image files...")
        for imgfn in image_files:
            old_img_fsize = os.path.getsize(imgfn)
            print("Converting %r (%s kb)..." % (imgfn,  old_img_fsize//1024))
            fnbase, fnext = os.path.splitext(imgfn)
            if fnext == '.jpg' or fnext == '.jpeg':
                print(" - Preserving JPEG image format for file %r." % (imgfn,))
                outputfn = imgfn
            else:
                outputfn = fnbase + output_ext
            img = Image.open(imgfn)
            if img_max_size and (img.height > img_max_size or img.width > img_max_size):
                downscalefactor = (max(img.size) // img_max_size) + 1
                newsize = tuple(v // downscalefactor for v in img.size)
                print(" - Resizing %sx, from %s to %s" % (downscalefactor, img.size, newsize))
                img.resize(newsize)
            img.save(outputfn, optimize=optimize, quality=quality)  # extra keywords are ignored (e.g. quality for png)
            print(" - Saved:  %r (%s kb)" % (outputfn, os.path.getsize(outputfn) // 1024))
            new_img_fsize = os.path.getsize(outputfn)
            if fsize_filter and new_img_fsize > fsize_filter:
                print(" - Notice: Filesize %s kb is still above the filesize limit (%s kb)"
                      % (new_img_fsize//1024, fsize_filter//1024))
            if fnext != output_ext:
                # We only need to change the basename, all images are in the same directory...
                changed_fns.append((os.path.basename(imgfn), os.path.basename(outputfn)))
                os.remove(imgfn)
                print(" - Deleted: %r" % (imgfn,))
        print("\nChanged image filenames:")
        print("\n".join("  %s -> %s" % tup for tup in changed_fns))

        print("\nFinding changed .xml.rels files...")
        xml_files = glob(os.path.join(pptdir, "**", "*.xml.rels"), recursive=True)
        changed_xml_fns = []
        for xmlfn in xml_files:
            with open(xmlfn) as fd:
                xml = fd.read()
                if any(oldimgfn in xml for oldimgfn, newimgfn in changed_fns):
                    # Make sure to use \r\n as file endings:
                    changed_xml_fns.append((xmlfn, xml.replace("\n", "\r\n")))

        print("\nMaking changes to %s of %s xml relationship files..." % (len(changed_xml_fns), len(xml_files)))
        for xmlfn, xml in changed_xml_fns:
            count = 0
            for oldimgfn, newimgfn in changed_fns:
                xml = xml.replace(oldimgfn, newimgfn)
                count += 1
            print(" - Performed %s substitutions in file %r" % (count, xmlfn))
            with open(xmlfn, 'w') as fd:
                fd.write(xml)

        new_zip_fn = outputfn_fmt.format(filename=filename, fnroot=pptx_fnroot)
        if os.path.exists(new_zip_fn) and not overwrite:
            print(("WARNING, output file already exists! If you want to keep \n%r,\n"
                   "please move/rename it before continuing. "))
            input("Press enter to continue... ")
        print("\nCreating new pptx zip archive: %r" % (new_zip_fn,))
        zip_directory(tmpdirname, new_zip_fn, relative=True, compress_type=compress_type)
        new_fsize = os.path.getsize(new_zip_fn)
        print("\nDone! New file size: %0.01f MB (%0.01f %% of original)" % (new_fsize/2**20, 100*new_fsize/old_fsize))

        if convert_to == "png":
            print("""
Notice: This downsizing was done using PNG image format (default setting). 
PNG format preserves the appearance and quality of images very well, 
but may result in large file sizes for complex images. 
If you notice any files that are still excessively large in the output above, 
try running this downsizing again using `jpeg` as `convert_to` option. """)

    return new_zip_fn


def zip_directory(directory, targetfn=None, relative=True, compress_type=zipfile.ZIP_DEFLATED):
    assert os.path.isdir(directory)
    if targetfn is None:
        targetfn = directory + ".zip"
    filecount = 0
    print("Creating archive %r from directory %r:" % (targetfn, directory))
    with zipfile.ZipFile(targetfn, mode="w") as zipfd:
        for dirpath, dirnames, filenames in os.walk(directory):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                arcname = os.path.relpath(fpath, start=directory) if relative else fpath
                print(" - adding %r" % (arcname,))
                zipfd.write(fpath, arcname=arcname, compress_type=compress_type)
                filecount += 1
    print("\n%s files written to archive %r" % (filecount, targetfn))
    return targetfn


def convert_str_to_int(s, do_float=True, do_eval=True):
    try:
        return int(s)
    except ValueError as e:
        if do_float:
            try:
                return convert_str_to_int(float(s), do_float=False, do_eval=False)
            except ValueError as e:
                if do_eval:
                    return convert_str_to_int(eval(s), do_float=do_float, do_eval=False)
                else:
                    raise e
        else:
            raise e


def open_pptx(fpath):
    import subprocess
    import shlex
    if 'darwin' in sys.platform:
        exec = 'open -a "Microsoft PowerPoint"'
    else:
        raise NotImplementedError("Opening pptx files not yet supported on Windows.")
        # TODO: The right way to do this is probably to search the registry using _winreg package.
    p = subprocess.Popen(shlex.split(exec) + [fpath])


# TODO: Consider using `click` package instead of argparse? (Is more natural when functions map directly to arguments)

def get_argparser(defaults=None):
    if defaults is None:
        spec = inspect.getfullargspec(downsize_pptx_images)
        # import pdb; pdb.set_trace()
        # Note: Reverse, so that args without defaults comes last naturally:
        defaults = dict(zip((spec.args+spec.kwonlyargs)[::-1], (spec.defaults+(spec.kwonlydefaults or ()))[::-1]))
    ap = argparse.ArgumentParser(prog="PowerPoint pptx downsizer.")
    ap.add_argument("filename", help="Path to PowerPoint pptx file.")
    ap.add_argument("--convert-to", default=defaults['convert_to'])
    ap.add_argument("--outputfn_fmt", default=defaults['outputfn_fmt'])
    ap.add_argument("--fn-filter", default=defaults['fn_filter'])
    ap.add_argument("--fsize-filter", default=defaults['fsize_filter'])
    ap.add_argument("--img-max-size", default=defaults['img_max_size'], type=int)
    ap.add_argument("--quality", default=defaults['quality'], type=int)
    ap.add_argument("--open-pptx", default=defaults['open_pptx'], action="store_true")
    ap.add_argument("--optimize", default=defaults['optimize'], action="store_true", dest="optimize")
    ap.add_argument("--no-optimize", default=defaults['optimize'], action="store_false", dest="optimize")
    ap.add_argument("--verbose", default=defaults['verbose'], type=int)
    ap.add_argument("--overwrite", default=defaults['overwrite'], action="store_true")
    # compress_type=zipfile.ZIP_DEFLATED
    ap.add_argument("--compress-type", default='ZIP_DEFLATED')
    return ap


def parse_args(argv=None, defaults=None):
    ap = get_argparser(defaults=defaults)
    argns = ap.parse_args(argv)
    if argns.fsize_filter:
        try:
            argns.fsize_filter = convert_str_to_int(argns.fsize_filter)
        except ValueError:
            ap.print_usage()
            print("Error: fsize_filter must be numeric, is %r" % argns.fsize_filter)
    if argns.compress_type and isinstance(argns.compress_type, str):
        argns.compress_type = getattr(zipfile, argns.compress_type)
    return argns


def cli(argv=None):
    argns = parse_args(argv)
    params = vars(argns)
    if argns.verbose:
        print("parameters:")
        print(yaml.dump(params, default_flow_style=False))
    downsize_pptx_images(**params)


if __name__ == '__main__':
    cli()
