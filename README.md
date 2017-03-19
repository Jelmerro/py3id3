# Py3ID3

The mp3 tagger with no hidden magic.

Every mp3 tag editor has a different focus.
There are thousands of them,
because everybody has a different way to organize their music.
This program was purely made to be a no-magic tag editor,
meaning that every change to the tags is made by the user,
and will be instantly visible in the gui.
This project is created for Python 3 to manage ID3 tags.
Py3ID3 uses stagger to read and write tags and tkinter to create a gui.
This is my first project using these packages,
so it can probably be improved a lot.

# Features
* View existing tags
* Edit or remove tags
* Limit changes to relevant fields
* Multiple files supported
* Convert between id3 (V2) versions
* Automatic track numbering
* Optionally add leading zeros to the track number
* Will clean obscure tags by default
* Warns on exit if files are opened

# Requirements
* [stagger](https://github.com/lorentey/stagger "Github")  
  Download it from from github (tested with 1.0.1),  
  or install it with `pip install stagger`.
* [tkinter](https://wiki.python.org/moin/TkInter "Python Wiki")  
  Should be bundled with the Windows installer,  
  Linux users need to install tkinter separately.  
  Usually with `sudo apt install python3-tk`.

# License
Py3ID3 itself is MIT licensed, see LICENSE for details.  
Both stagger and tkinter are covered by different licenses.
