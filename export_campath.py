import bpy
import struct, time, sys, os, zlib, io
import mathutils
from mathutils.geometry import tesselate_polygon

def write_spline(spline):
  print("spline type:",spline.type)
  print("number of points:",len(spline.points))
  print("order_u",spline.order_u)
  print("order_v",spline.order_v)
  print("resolution_u",spline.resolution_u)
  print("resolution_v",spline.resolution_v)
  for p in spline.points:
    print("point:",p.co)
    print("tilt:",p.tilt)
    print("weight:",p.weight)

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

def save(operator, context, filepath):
  scene = context.scene
  
  for o in scene.objects:
    if o.type == 'CURVE':
      curve=o.data
      if curve.use_path:
        print("found curve path object, name is", curve.name)
        print("dimensions:",curve.dimensions)
        print("path duration:",curve.path_duration)
        print("splines length:",len(curve.splines))
        for s in curve.splines:
          write_spline(s)

        write_anim_data(curve.animation_data, curve.path_duration)

  return {'FINISHED'}
