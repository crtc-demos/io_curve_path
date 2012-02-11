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

def write_anim_data(fh, anim_data, frames):
  print("animation data, using nla:",anim_data.use_nla)
  print("drivers:",len(anim_data.drivers))
  print("nla tracks:",len(anim_data.nla_tracks))
  action = anim_data.action
  print("action range:",action.frame_range)
  print("action fcurves:",len(action.fcurves))
  for fcurve in action.fcurves:
    for frame in range(frames):
      fh.write("  {},\n".format(fcurve.evaluate(frame)))
  return 

def anim_data_or_null(foo):
  if foo == None:
    return "NULL"
  else:
    return "&"+foo

def write_spline(fh, curve, name, spline, num):
  if spline.type != 'NURBS':
    raise UserWarning("Spline not a NURBS")
  #print("number of points:",len(spline.points))
  order = spline.order_u
  resolution = spline.resolution_u

  knots_name = name + "_knots_" + str(num)
  fh.write("static float " + knots_name + "[][4] = {\n")
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
  
  if curve.animation_data == None:
    print("No animation data?")
    anim_data_name = None
    anim_data_length = 0
    anim_data_start = 0
    anim_data_end = 0
  else:
    anim_data_name = name + "_animdata_" + str(num)
    fh.write("static float " + anim_data_name + "[] = {\n")
    write_anim_data(fh, curve.animation_data, curve.path_duration)
    fh.write("};\n")
    anim_data_length = curve.path_duration
    anim_data_start = curve.animation_data.action.frame_range[0]
    anim_data_end = curve.animation_data.action.frame_range[1]
  
  fh.write("static spline_tracking_obj " + name + "_" + str(num) + " = {\n")
  fh.write("  .base = { .type = TRACKING_OBJ_PATH },\n")
  fh.write("  .spline = {\n")
  fh.write("    .length = {},\n".format(len(spline.points)))
  fh.write("    .order = {},\n".format(spline.order_u))
  fh.write("    .resolution = {},\n".format(spline.resolution_u))
  fh.write("    .knots = &{},\n".format(knots_name))
  fh.write("    .tilt = {},\n".format(tilt_name))
  fh.write("    .weight = {}\n".format(weight_name))
  fh.write("  },\n")
  fh.write("  .anim_data = {},\n".format(anim_data_or_null(anim_data_name)))
  fh.write("  .anim_frames = {},\n".format(anim_data_length))
  fh.write("  .anim_start = {},\n".format(anim_data_start))
  fh.write("  .anim_end = {}\n".format(anim_data_end))
  fh.write("};\n")

def write_static(fh, static_obj):
  s_name = safe_name(static_obj.name)
  loc = static_obj.location
  fh.write("static static_tracking_obj " + s_name + " = {\n")
  fh.write("  .base = { .type = TRACKING_OBJ_STATIC },\n")
  fh.write("  .pos = {{ {}, {}, {} }}\n".format(loc[0], loc[1], loc[2]))
  fh.write("};\n")
  return s_name

def write_curve(fh, curve):
  name = curve.name
  s_name = safe_name(curve.name)
  fh.write("/* Curve " + name + " animation path setting:"
           + str(curve.use_path) + " */\n")
  if curve.dimensions != '3D':
    raise UserWarning("Spline not 3D")
  for s in range(len(curve.splines)):
    write_spline(fh, curve, s_name, curve.splines[s], s)
  # huh, what happens if we have more than one curve?
  return s_name + "_0"

def addr_or_null(foo):
  if foo == None:
    return "NULL"
  else:
    return "(tracking_obj_base *) &"+foo

def constrained_to_curve(obj):
  if obj.type == 'CURVE' and obj.data.use_path:
    return obj
  else:
    for c in obj.constraints:
      if c.type == 'FOLLOW_PATH':
        return constrained_to_curve(c.target)
      else:
        print("Unknown constraint:",c.type)
    return None

def save(operator, context, filepath):
  scene = context.scene
  
  cam = scene.camera

  if cam.type == 'CAMERA':
    print ("the scene camera is a camera - good!")

  with open(filepath, "w") as fh:
    follow_path = None
    track_to = None

    for c in cam.constraints:
      print ("constraint type",c.type)
      print ("influence",c.influence)
      if c.type == 'FOLLOW_PATH':
        print ("Instance of FollowPathConstraint:",
               isinstance(c, bpy.types.FollowPathConstraint))
        print ("follow target",c.target)
        print ("which is a",c.target.type)
        if c.target.type == 'CURVE':
          curve = c.target.data
          curve_name = write_curve(fh, curve)
          follow_path = curve_name
        else:
          print ("That's not a curve, ignoring.")
      elif c.type == 'TRACK_TO':
        print ("Instance of TrackToConstraint:",
               isinstance(c, bpy.types.TrackToConstraint))
        cons_curve = constrained_to_curve(c.target)
        if cons_curve is not None:
          curve = cons_curve.data
          curve_name = write_curve(fh, curve)
          track_to = curve_name
        else:
          obj = c.target
          obj_name = write_static(fh, obj)
          track_to = obj_name
      else:
        print ("Ignoring constraint")

    cpath_name = os.path.splitext(os.path.basename(filepath))[0]

    safe_cpath_name = safe_name(cpath_name)

    fh.write("cam_path {} = {{\n".format(safe_cpath_name))
    fh.write("  .follow_path = {},\n".format(addr_or_null(follow_path)))
    fh.write("  .track_to = {}\n".format(addr_or_null(track_to)))
    fh.write("};\n");
  
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

#    write_anim_data(curve.animation_data, curve.path_duration)

  return {'FINISHED'}
