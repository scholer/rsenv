

The `videoutils` package contains a bunch of different modules for 
reading and writing videos and video-like image sequences.


For more info, see:

* `qpaint_analysis` - which has old notes from 2017 about converting TIFF image stacks to video.
* `imagestack-pyper` - updated project, based on the old code from `qpaint_analysis` project.



This `videoutils` package explores a bunch of third-party libraries for creating videos:

* MoviePy - http://zulko.github.io/moviepy/
* ImageIO - https://imageio.github.io/
* PyAV - https://docs.mikeboers.com/pyav/develop/index.html

MoviePy and ImageIO both convert videos by piping to FFmpeg - the same approach as `imagestack-pyper`.

PyAV provides python bindings to FFmpeg, which provides a rather low-level API. 
This may be overkill, and as stated on the PyAV homepage:

> If the ffmpeg command does the job without you bending over backwards, 
> PyAV is likely going to be more of a hindrance than a help.


For reading TIFF image stacks, there are the following options:

* [PIMS](https://github.com/soft-matter/pims) - The goal of PIMS is to provide 
    a "universal" interface for reading Image Sequences in Python.
    * Only provides "framework" classes for standardizing image reading API, e.g. the following classes:
        * `ImageReader` - Reads a single image.
        * `ImageSequence` - "Read a directory of sequentially numbered image files"
        * `ImageSequenceND` -  "Read a directory of multi-indexed image files"
        * `ReaderSequence` - "Construct a reader from a directory of ND image files."
    * The actual image reading is done by third party libraries, 
        e.g. `tifffile`, `libtiff`, or `PIL` for TIFF files,
        and `moviepy`, `PyAV`, and `ImageIO` for video files.
    * Supports plugins that can be installed separately,
        for instance `pims-nd2` or `nd2reader` for reading Nikon ND2 datasets.
    * Evaluation:
        While I like the concept of a "universal" image reading API, 
        I'm not sure I like the prospect that this implies, 
        namely that you never really know what library you will be using for reading image files.
        For instance, `pims.TiffStack` is aliasing different classes depending on which packages are available
        (tiffflie, libtiff, or PIL - in that order).
        Now, you can guarantee that you are using a certain library by using 
        `pims.TiffStack_tifffile`, but then you might as well just use `tifffile` directly.
        
* [ImageIO](https://imageio.github.io/) - tries to be the "universal" image reader library for python.
    * Used by many projects, including Skimage.
    * Supports plugins, and e.g. uses Gohlke's tifffile for reading tiff files.
    
* tifffile
    * Provides the following classes:
        * `TiffFile` - "Read image and metadata from TIFF, STK, LSM, and FluoView files."
        * `TiffPage` - "A TIFF image file directory (IFD)."
        * `TiffPageSeries` - "Series of TIFF pages with compatible shape and data type."
        * `TiffSequence` - sequence of individual image files.
    * As far as I can tell, will read the whole tiff file into memory - no option for streaming from disk.

* Pillow - Port of PIL (Python Image Library).

* OpenCV/CV2 - Open Computer Vision project. Provides bindings to the C++ library.


Projects that uses the above to read and process image files:

* skimage - relies on "plugins" for reading images - defaults to tifffile and ImageIO.


Other solutions for reading TIFF files and writing them as video:

* https://pypi.org/project/tiffstack2avi/ - Reads TIFF files in a directory and passes them to ffmpeg using:
    `ffmpeg -i  {tifdir}\frame%d.tif -vcodec ffv1 {tifdir}.avi"`
* https://pypi.org/project/pyimagevideo/


Other interesting projects:

* pimsviewer - "A graphical user interface (GUI) for PIMS."
    * https://github.com/soft-matter/pimsviewer


More irrelevant projects - do not consider these:

* [ImageStackPy](https://github.com/aniketkt/ImageStackPy) - Uses `matplotlib.pyplot.imread` to 
    read TIFF images in a directory and then perform various operations 
    (filters, transformations, object tracking, etc.) in a parallellized fashion.



See also:

* http://soft-matter.github.io/pims/v0.4.1/video.html
* https://github.com/soft-matter/pimsviewer
* 



