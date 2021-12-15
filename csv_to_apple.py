from pyglossary import Glossary
import sys

Glossary.init()

glos = Glossary()
glos.convert(
    inputFilename=sys.argv[1],
    outputFilename=sys.argv[2],
    outputFormat='AppleDict',
    readOptions={
        'delimiter': '@',
    },
)
