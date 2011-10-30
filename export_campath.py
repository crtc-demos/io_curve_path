import bpy
import struct, time, sys, os, zlib, io
import mathutils
from mathutils.geometry import tesselate_polygon

# Return a name which is suitable for use as a C variable.
def safe_name(name):
  out=[]
  for idx in range(len(name)):
    char=name[idx]
    if char.isalpha() or (idx > 0 and char.isdigit()):
      out.append(char)
    else:
      out.append('_'+char if char.isdigit() else '_')
  return ''.join(out)

def write_spline(fh, name, spline, num):
  if spline.type != 'NURBS':
    raise UserWarning("Spline not a NURBS")
  #print("number of points:",len(spline.points))
  order = spline.order_u
  resolution = spline.resolution_u

  knots_name = name + "_knots_" + str(num)
  fh.write("static guVector " + knots_name + "[] = {\n")
  for p in spline.points:
    x,y,z,w = p.co
    fh.write("  {{ {}, {}, {}, {} }},\n".format(x,y,z,w))
  fh.write("};\n")

  tilt_name = name + "_tilt_" + str(num)
  fh.write("static float " + tilt_name + "[] = {\n")
  for p in spline.points:
    fh.write("  {},\n".format(p.tilt))
  fh.write("};\n")
  
  weight_name = name + "_weight_" + str(num)
  fh.write("static float " + weight_name + "[] = {\n")
  for p in spline.points:
    fh.write("  {},\n".format(p.weight))
  fh.write("};\n")
  
  fh.write("spline_info " + name + "_" + str(num) + " = {\n")
  fh.write("  .length = {},\n".format(len(spline.points)))
  fh.write("  .order = {},\n".format(spline.order_u))
  fh.write("  .resolution = {},\n".format(spline.resolution_u))
  fh.write("  .knots = &{},\n".format(knots_name))
  fh.write("  .tilt = &{},\n".format(tilt_name))
  fh.write("  .weight = &{}\n".format(weight_name))
  fh.write("};\n")

def write_anim_data(anim_data, frames):
  print("animation data, using nla:",anim_data.use_nla)
  print("drivers:",len(anim_data.drivers))
  print("nla tracks:",len(anim_data.nla_tracks))
  action=anim_data.action
  print("action range:",action.frame_range)
  print("action fcurves:",len(action.fcurves))
  for fcurve in action.fcurves:
    for frame in range(frames):
      print("at",frame,"val is",fcurve.evaluate(frame))

def write_curve(fh, curve):
  name=curve.name
  fh.write("/* Curve " + name + " animation path setting:"
           + str(curve.use_path) + " */\n")
  if curve.dimensions != '3D':
    raise UserWarning("Spline not 3D")
  for s in range(len(curve.splines)):
    write_spline(fh, safe_name(name), curve.splines[s], s)

def save(operator, context, filepath):
  scene = context.scene
  
  cam=scene.camera

  if cam.type == 'CAMERA':
    print ("the scene camera is a camera - good!")

  with open(filepath, "w") as fh:
    for c in cam.constraints:
      print ("constraint type",c.type)
      print ("influence",c.influence)
      if c.type == 'FOLLOW_PATH':
        print ("Instance of FollowPathConstraint:",
               isinstance(c, bpy.types.FollowPathConstraint))
        print ("follow target",c.target)
        print ("which is a",c.target.type)
        if c.target.type == 'CURVE':
          curve=c.target.data
          write_curve(fh, curve)
        else:
          print ("That's not a curve, ignoring.")
      elif c.type == 'TRACK_TO':
        print ("Instance of TrackToConstraint:",
               isinstance(c, bpy.types.TrackToConstraint))
      else:
        print ("Ignoring constraint")
  
#  for o in scene.objects:
#    if o.type == 'CAMERA':
#      print ("found camera")
#      cam=o.data
      
#    elif o.type == 'CURVE':
#      curve=o.data
#      if curve.use_path:
#        print("found curve path object, name is", curve.name)
#        print("dimensions:",curve.dimensions)
#        print("path duration:",curve.path_duration)
#        print("splines length:",len(curve.splines))
#        for s in curve.splines:
#          write_spline(s)

#        write_anim_data(curve.animation_data, curve.path_duration)

  return {'FINISHED'}
