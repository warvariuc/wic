#!/usr/bin/python3

# generate qrc file with all icons within `icons` folder

import os, sys

cur_dir = os.path.dirname(__file__)
icons_dir = os.path.join(cur_dir, 'icons')

qrc_file = open(os.path.join(cur_dir, 'widgets.qrc'), 'w')

qrc_file.write("""
<RCC>
  <qresource>""")

for root_path, dir_names, file_names in os.walk(icons_dir):
    for file_name in file_names:
        file_path = os.path.join(root_path, file_name)[2:]
        print(file_path)
        qrc_file.write("\n    <file>%s</file>" % file_path)

    
qrc_file.write("""
  </qresource>
</RCC>
""")

qrc_file.close()
