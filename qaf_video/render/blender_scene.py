"""Executed inside Blender, independent of its Python site-packages."""
if __name__=='__main__':
    import bpy,json,sys,math
    from mathutils import Vector
    config=json.load(open(sys.argv[sys.argv.index('--')+1]))
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=config['samples'];scene.cycles.use_denoising=True
    scene.render.resolution_x=config['width'];scene.render.resolution_y=config['height'];scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=config['output']
    def material(name,color,metal=0):
        mat=bpy.data.materials.new(name);mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Metallic'].default_value=metal;bsdf.inputs['Roughness'].default_value=.24;return mat
    emerald=material('Emerald',(0.026,.34,.24),.5);gold=material('Gold',(.65,.45,.16),.85);graphite=material('Graphite',(.015,.02,.025),.3)
    for loc,r,mat in [((-1,0,1),1,emerald),((1,0,.7),.7,gold),((0,-.8,.4),.4,emerald)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=r,location=loc);ob=bpy.context.object;ob.data.materials.append(mat)
        for poly in ob.data.polygons:poly.use_smooth=True
    bpy.ops.mesh.primitive_plane_add(size=200);bpy.context.object.data.materials.append(graphite)
    for loc,power,size in [((1,-3,6),1100,4),((-4,-1,3),700,3)]:
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(3,-6,3));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=48;scene.camera=camera
    scene.world.color=(.025,.025,.025);bpy.ops.render.render(write_still=True)
