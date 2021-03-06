#!/usr/bin/env python

############################################################################
#
# MODULE:       i.script
# AUTHOR(S):    Ismail Baris
# PURPOSE:      Import Scripts from a package to GRASS GIS. Maybe requires sudo.
#
# COPYRIGHT:    (C) Ismail Baris and Nils von Norsinski
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%Module
#% description: Import Scripts from a package to GRASS GIS.
#% keyword: script
#% keyword: auxiliary
#% keyword: import
#%end

# Input Section --------------------------------------------------------------------------------------------------------
#%option G_OPT_M_DIR
#% key: input_dir
#% description: Directory of python files.
#% required: yes
#%guisection: Input
#%end

#%option G_OPT_M_DIR
#% key: export_path
#% description: Script directory of GRASS GIS (automatically in Linux systems).
#% required: no
#%guisection: Input
#%end

# Filter Section -------------------------------------------------------------------------------------------------------
#%option
#% key: pattern
#% description: The pattern of file names.
#% guisection: Filter
#%end

#%option
#% key: exclusion
#% description: Which files or pattern should be excluded?.
#% guisection: Filter
#%end

# Optional Section -----------------------------------------------------------------------------------------------------
#%flag
#% key: p
#% description: Print the detected files and exit.
#% guisection: Optional
#%end

#%flag
#% key: r
#% description: Replace script.
#% guisection: Optional
#%end


import os
import re
import shutil
import sys

try:
    import grass.script as gs
except ImportError:
    pass


class Grassify(object):
    """
    Import Scripts from a package to GRASS GIS.

    This class will copy any suitable python file like 'i_dr_import.py' into the GRASS script folder without
    the '.py' extension and changes the name to 'i.dr.import'. This class will exclude such files like
    '__init__.py' or 'setup.py'. For more exclusions the parameter `exclusion` can be used.

    Parameters
    ----------
    input_dir : str
        Directory of python files
    export_path : str, optional
        Script directory of GRASS GIS (automatically in Linux systems).
    pattern : str, optional
        The pattern of file names.
    exclusion : str
         Which files or pattern should be excluded?.

    Attributes
    ----------
    extension : list
        A list which contains all supported GRASS GIS candidates.
    exclusion : str
    import_path : str
        Dir parameter.
    export_path : str
    filter_p : str
        Combines pattern and extension.
    files : list
        All detected files.

    Methods
    -------
    copy(replace=False)
        Copy files.
    print_products()
        Print all detected files.

    Examples
    --------
    The general usage is
    ::
        $ i.script [-r-p] input_dir=string [pattern=string] [exclusion=string] [export_path=string] [--verbose] [--quiet]


    Import all suitable python files from a directory into the GRASS script folder
    ::
        $ i.script input_dir=/home/user/package


    Import all suitable python files from a directory into the GRASS script folder and exclude all files that
    include the string 'test'
    ::
        $ i.script input_dir=/home/user/package exclude=test.*

    Note
    ----
    This class copies all files and replaces all '_' with '.'.

    Notes
    -----
    **Flags:**
        * r : Overwrite file if it is existent **(be careful padawan!)**
        * p : Print the detected files and exit.
    """

    def __init__(self, input_dir, export_path=None, pattern=None, exclusion=None):
        # Self Definitions ---------------------------------------------------------------------------------------------
        self.extension = '.py'

        self.candidates = ['grass70', 'grass71', 'grass72', 'grass73', 'grass74']
        if exclusion is None:
            self.exclusion = ['__init__.py', '__version__.py', 'setup_grass.py', 'gscpy.py', 'setup.py']
        else:
            self.exclusion = exclusion

        # Initialize Directory -----------------------------------------------------------------------------------------
        if not os.path.exists(input_dir):
            gs.fatal(_('Input directory <{0}> not exists').format(input_dir))
        else:
            self.import_path = input_dir

        # < Try to find the script directory of GRASS GIS > ------------
        if export_path is None:
            for item in self.candidates:
                export_path = '/usr/lib/' + item + '/scripts'

                if os.path.exists(export_path):
                    self.export_path = export_path

        elif export_path is not None:
            if not os.path.exists(export_path):
                os.makedirs(export_path)

            self.export_path = export_path

        # Create Pattern and find files --------------------------------------------------------------------------------
        if pattern is None:
            filter_p = '.*' + self.extension
        else:
            filter_p = pattern

        gs.debug('Filter: {}'.format(filter_p), 1)
        self.files = self.__filter(filter_p)

        if self.files is []:
            gs.message(_('No files detected. Note, that must be a point for * like: pattern = str.* '))
            return

    # ------------------------------------------------------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------------------------------------------------------
    def copy(self, replace=False):
        filename = [os.path.basename(item) for item in self.files]
        filename_split = [os.path.splitext(item) for item in filename]

        for i in range(len(filename_split)):
            old_name = self.files[i]
            base = filename_split[i][0]
            base = base.replace('_', '.')

            new_name = os.path.join(self.export_path, base)

            if not os.path.exists(new_name) or replace:
                shutil.copy(old_name, new_name)
            elif not replace and os.path.exists(new_name):
                pass
                # gs.fatal(_('Script <{0}> exists. Try to set the replace flag').format(base))

        return 0

    def print_products(self):
        for f in self.files:
            sys.stdout.write('Detected Files <{0}> {1}'.format(f, os.linesep))

    # ------------------------------------------------------------------------------------------------------------------
    # Private Methods
    # ------------------------------------------------------------------------------------------------------------------
    def __filter(self, filter_p):
        pattern = re.compile(filter_p)
        files = []

        for rec in os.walk(self.import_path):
            if not rec[-1]:
                continue

            match = filter(pattern.match, rec[-1])
            if match is None:
                continue

            for f in match:
                if f in self.exclusion:
                    pass
                elif f.endswith(self.extension):
                    files.append(os.path.join(rec[0], f))
                else:
                    pass

        return files


def change_dict_value(dictionary, old_value, new_value):
    """
    Change a certain value from a dictionary.

    Parameters
    ----------
    dictionary : dict
        Input dictionary.
    old_value : str, NoneType, bool
        The value to be changed.
    new_value : str, NoneType, bool
        Replace value.

    Returns
    -------
    dict
    """
    for key, value in dictionary.items():
        if value == old_value:
            dictionary[key] = new_value

    return dictionary


def main():
    grassify = Grassify(options['input_dir'], export_path=options['export_path'], pattern=options['pattern'],
                        exclusion=options['exclusion'])

    if flags['p']:
        grassify.print_products()
        return 0

    grassify.copy(replace=flags['r'])

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    options = change_dict_value(options, '', None)

    sys.exit(main())

files = ["/home/ibaris/Dropbox/Dropbox/GitHub/gscpy/gscpy/i_script.py",
         "/home/ibaris/Dropbox/Dropbox/GitHub/gscpy/gscpy/ds1_download/ds1.download.py",
         "/home/ibaris/Dropbox/Dropbox/GitHub/gscpy/gscpy/pr_geocode/pr_geocode.py",
         "/home/ibaris/Dropbox/Dropbox/GitHub/gscpy/gscpy/i_import/i_fr_import.py",
         "/home/ibaris/Dropbox/Dropbox/GitHub/gscpy/gscpy/i_import/i_dr_import.py",
         "/home/ibaris/Dropbox/Dropbox/GitHub/gscpy/gscpy/g_db/g_database.py",
         "/home/ibaris/Dropbox/Dropbox/GitHub/gscpy/gscpy/g_db/g_c_mapset.py"]
