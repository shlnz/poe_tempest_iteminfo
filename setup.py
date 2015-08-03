from distutils.core import setup
import py2exe

setup(
    name="POE Tempests",
    author="Jens Thom",
    version="0.2.1",
    options={'py2exe': {'bundle_files': 1, 'compressed': True}},
    zipfile=None,
    console=[{"script": "poe_tempest.py",
              "icon_resources": [(1, "icon.ico")],
              "dest_base":"poe_tempest"
              }],)
