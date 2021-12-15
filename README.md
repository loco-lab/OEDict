# OEDict
Old English dictionary parser

The goal of this project is to parse the Bosworth and Toller Anglo-Saxon dictionary into modern formats.

We are basing the parser on the digital text version available here:<br>
https://www.ling.upenn.edu/~kurisuto/germanic/oe_bosworthtoller_about.html

## Instructions

```
git clone git@github.com:ilius/pyglossary.git
cd pyglossary
pip install .
```

From this repository, you can then use `csv_to_apple.py` to create an Apple xml dictionary, which can then be compiled and imported to Dictionary. This requires the Dictionary Development Kit from XCode.
```
python csv_to_apple.py oe_bt.csv oe_bt.xml
cd oe_bt.xml
make
make install
```

`pyglossary` can be used to convert to a variety of other formats as well.


## Credits
We acknowledge the following contributions to create the text version:
- Scanning and initial OCR was funded by Joel Dean grants at Swarthmore College, summer 2001 and summer 2002.
- Jason Burton: Scanned the entire text during summer 2001, and performed preliminary OCR.
- B. Dan Fairchild: Revised OCR work and performed a preliminary round of automated corrections, summer 2002.
- Margaret Hoyt: Image postprocessing on pages b0400-b1000, summer 2003.
- Grace Mrowicki and Michael O'Keefe: Hand correction of some pages (prior to initiation of web-based correction system), summer 2003.
- Sarah Hartman, Finlay Logan, and Sean Crist: Correction of headwords in the 1921 supplement, spring/summer 2005.
- Thomas McFadden: Correction of page headers, summer 2005. Kari Swingle: Joel Dean grantee, summer 2001
- David Harrison: Joel Dean grantee, summer 2002
- Sean Crist: Initiated project; Principal Investigator under Joel Dean grantees, summer 2001/2002; major software design and programming; global correction; image postprocessing except on pages b0401-b1000.
- Thanks to Ian Sandy for pointing out a few image files which contained the wrong page image.
