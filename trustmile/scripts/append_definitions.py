import sys
import re
import os

if __name__ == '__main__':
    filename = sys.argv[1]
    print filename
    path = filename.split('/')[0]
    print path
    comps = filename.split('.')
    new_filename = comps[0] + '-ammended.' + comps[1]

    f = open(filename)
    new_string = ''
    for l in f.readlines():
        if l.find('$include') > 0:
            definitions = re.match('.*\'(\w+\.yml)\'', l).group(1)
            definitions_s = open(os.path.join(path, definitions)).read()
            new_string += definitions_s
        else:
            new_string += l

    yaml_file = new_string

    new_file = open(new_filename, 'w')

    new_file.write(yaml_file)

    new_file.close()
