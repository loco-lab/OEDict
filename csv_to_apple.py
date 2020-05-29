import pyglossary
import sys


my_dict = pyglossary.Glossary()
my_dict.read(sys.argv[1], progressbar=False)
my_dict.write(sys.argv[2], 'AppleDict')
