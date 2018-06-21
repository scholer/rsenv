#!/usr/bin/python

## This simple script simply takes the lines in two files and compares them using set logic.
### Provide the file names as arguments when invoking this script.

import sys

# Do I care about the order ( fileA, fileB vs fileB, fileA
fdata = list()

print "\n\nEntries in files:"
args = sys.argv[1:]
for arg in args:
    with open(arg, 'rU') as f:
        content = [line.rstrip() for line in f]
        print str(len(content)) + " entries in file: " + arg
        fdata.append(content)
#print fdata

sets = list()
print "\nUnique entries:"

#for fn,d in fdata.items():
i = 0
for d in fdata:
    fset = set(d)
    print str(len(fset)) + " unique entries in file: " + args[i]
    i += 1
    sets.append(fset)

if len(sets) < 2:
    print len(sets)
    print "To proceed, this script requires at least two valid files..."
    exit()

# http://docs.python.org/library/sets.html
#print "ALL entries:"
#print sets[0] | sets[1] # equivalent to a.union(b)

print "COMMON entries:"
print sets[0] & sets[1] # equivalent to a.intersection(b)

print "\nIn " + args[0] + " and not in " + args[1] + ":"
print sets[0] - sets[1] # equivalent to a.difference(b)

print "\nIn " + args[1] + " and not in " + args[0] + ":"
print sets[1] - sets[0]


## FINAL HINT: TO FIND AN OLIGO IN THE DATABASE, USE THE FOLLOWING QUERY:
"""
SELECT o.id AS oligo_id, o.sequence_with_mods AS sequence, m.id AS module_id, m.name AS module_name, mc.id AS mc_id, mc.name AS mc_name,
       mo.annotation_cadnano_start AS c_start, mo.annotation_cadnano_end AS c_end, mo.annotation_xover AS xover, mo.annotation_sarse AS sarse
FROM (SELECT * FROM om.oligos WHERE sequence_with_mods = 'GCGCCGCTTTTCGGGCGCTAGGGCGCTTTTTTTAAAGAA') AS o
LEFT JOIN om.module_oligos mo ON mo.oligo_id = o.id
LEFT JOIN om.modules m ON mo.module_id = m.id
JOIN om.moduleclasses mc ON mc.id = m.moduleclass_id
ORDER BY m.name, mc.id
;
"""
