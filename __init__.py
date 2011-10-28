bl_info = {
    "name": "Camera path export",
    "description": "export camera paths in some custom format",
    "author": "Julian Brown",
    "version": (1,0),
    "blender": (2, 5, 8),
    "api": 31236,
    "location": "File > Import-Export",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

class ExportCampath(bpy.types.Operator, ExportHelper):
  '''Save a camera path'''
  bl_idname = "export_campath.xyz"
  bl_label = "Export Camera Path"
  filename_ext = ".xyz"
  filter_glob = StringProperty(default="*.xyz", options={'HIDDEN'})
  def execute(self, context):
    from . import export_campath
    return export_campath.save(self, context, **self.as_keywords(ignore=("check_existing", "filter_glob")))

def menu_func_export(self, context):
  self.layout.operator(ExportCampath.bl_idname, text="Camera path (.xyz)")
  
def register():
  bpy.utils.register_module(__name__);
  bpy.types.INFO_MT_file_export.append(menu_func_export);

def unregister():
  bpy.utils.unregister_module(__name__);
  bpy.types.INFO_MT_file_export.remove(menu_func_export);

if __name__ == "__main__":
  register()
