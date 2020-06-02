import sys
import os

import json
import csv

if __name__ == "__main__":
    fname = sys.argv[1]

    try:
        outfile = sys.argv[2]
    except IndexError:
        outfile = fname.split(".")[0] + '.csv'
        
    with open(fname) as fl:
        data = json.load(fl)


    # keys are words, values are {defns, headwords}

    nlines = 0
    with open(outfile, 'w') as fl:
        for word, info in data.items():
            for defn in info['defns']:
                defn = defn.replace('\n', '')
#                defn = defn.replace('"', '""').replace(',', '')
                alternatives = ",".join(info['headwords'])

                # We use '@' as the delimiter because commas appear in the fields.
                fl.write(f'{word}@{defn}@{alternatives}\n')
                nlines += 1

    # The following just reads the file we made to test that nothing went
    # completely awry.
    with open(outfile,'r') as fl:
        csv_reader = csv.reader(fl, dialect='excel', delimiter='@')
        lines = []
        for i, line in enumerate(csv_reader):
            lines.append(line)
            assert len(line) == 3, f"line {i} had {len(line)} entries. Line={line}"
            
    print(f"Actual number of lines: {nlines}")
    print(f"Read number of lines: {len(lines)}")
#    print(lines)
    assert len(lines) == nlines
