# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

# Generic helper functions, to be used by any modules.

import bmesh
import array


def bmesh_copy_from_object(obj, transform=True, triangulate=True):
    """
    Returns a transformed, triangulated copy of the mesh
    """

    assert(obj.type == 'MESH')

    me = obj.data
    if obj.mode == 'EDIT':
        bm_orig = bmesh.from_edit_mesh(me)
        bm = bm_orig.copy()
    else:
        bm = bmesh.new()
        bm.from_mesh(me)

    # TODO. remove all customdata layers.
    # would save ram

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces, use_beauty=True)

    return bm


def bmesh_from_object(obj):
    """
    Object/Edit Mode get mesh, use bmesh_to_object() to write back.
    """
    me = obj.data
    is_editmode = (obj.mode == 'EDIT')
    if is_editmode:
        bm = bmesh.from_edit_mesh(me)
    else:
        bm = bmesh.new()
        bm.from_mesh(me)
    return bm


def bmesh_to_object(obj, bm):
    """
    Object/Edit Mode update the object.
    """
    me = obj.data
    is_editmode = (obj.mode == 'EDIT')
    if is_editmode:
        bmesh.update_edit_mesh(me, True)
    else:
        bm.to_mesh(me)
    # grr... cause an update
    if me.vertices:
        me.vertices[0].co[0] = me.vertices[0].co[0]


def bmesh_calc_volume(bm):
    """
    Calculate the volume of a triangulated bmesh.
    """
    def tri_signed_volume(p1, p2, p3):
        return p1.dot(p2.cross(p3)) / 6.0
    return abs(sum((tri_signed_volume(*(v.co for v in f.verts))
                    for f in bm.faces)))


def bmesh_calc_area(bm):
    """
    Calculate the surface area.
    """
    return sum(f.calc_area() for f in bm.faces)


def bmesh_check_self_intersect_object(obj):
    """
    Check if any faces self intersect

    returns an array of edge index values.
    """
    import bpy

    # Heres what we do!
    #
    # * Take original Mesh.
    # * Copy it and triangulate it (keeping list of original edge index values)
    # * Move the BMesh into a temp Mesh.
    # * Make a temp Object in the scene and assign the temp Mesh.
    # * For every original edge - ray-cast on the object to find which intersect.
    # * Report all edge intersections.

    # Triangulate
    bm = bmesh_copy_from_object(obj, transform=False, triangulate=False)
    face_map_index_org = {f: i for i, f in enumerate(bm.faces)}
    ret = bmesh.ops.triangulate(bm, faces=bm.faces, use_beauty=False)
    face_map = ret["face_map"]
    # map new index to original index
    face_map_index = {i: face_map_index_org[face_map.get(f, f)] for i, f in enumerate(bm.faces)}
    del face_map_index_org
    del ret

    # Create a real mesh (lame!)
    scene = bpy.context.scene
    me_tmp = bpy.data.meshes.new(name="~temp~")
    bm.to_mesh(me_tmp)
    bm.free()
    obj_tmp = bpy.data.objects.new(name=me_tmp.name, object_data=me_tmp)
    scene.objects.link(obj_tmp)
    scene.update()
    ray_cast = obj_tmp.ray_cast

    faces_error = set()

    EPS_NORMAL = 0.0001
    EPS_CENTER = 0.00001  # should always be bigger

    for ed in me_tmp.edges:
        v1i, v2i = ed.vertices
        v1 = me_tmp.vertices[v1i]
        v2 = me_tmp.vertices[v2i]

        # setup the edge with an offset
        co_1 = v1.co.copy()
        co_2 = v2.co.copy()
        co_mid = (co_1 + co_2) * 0.5
        no_mid = (v1.normal + v2.normal).normalized() * EPS_NORMAL
        co_1 = co_1.lerp(co_mid, EPS_CENTER) + no_mid
        co_2 = co_2.lerp(co_mid, EPS_CENTER) + no_mid

        co, no, index = ray_cast(co_1, co_2)
        if index != -1:
            faces_error.add(face_map_index[index])

    scene.objects.unlink(obj_tmp)
    bpy.data.objects.remove(obj_tmp)
    bpy.data.meshes.remove(me_tmp)

    return array.array('i', faces_error)


def bmesh_face_points_random(f, num_points=1, margin=0.05):
    import random
    from random import uniform
    uniform_args = 0.0 + margin, 1.0 - margin

    # for pradictable results
    random.seed(f.index)

    vecs = [v.co for v in f.verts]

    for i in range(num_points):
        u1 = uniform(*uniform_args)
        u2 = uniform(*uniform_args)
        u_tot = u1 + u2

        if u_tot > 1.0:
            u1 = 1.0 - u1
            u2 = 1.0 - u2

        side1 = vecs[1] - vecs[0]
        side2 = vecs[2] - vecs[0]

        yield vecs[0] + u1 * side1 + u2 * side2


def bmesh_check_thick_object(obj, thickness):
    
    import bpy

    # Triangulate
    bm = bmesh_copy_from_object(obj, transform=True, triangulate=False)
    # map original faces to their index.
    face_index_map_org = {f: i for i, f in enumerate(bm.faces)}
    ret = bmesh.ops.triangulate(bm, faces=bm.faces, use_beauty=False)
    face_map = ret["face_map"]
    del ret
    # old edge -> new mapping

    # Convert new/old map to index dict.

    # Create a real mesh (lame!)
    scene = bpy.context.scene
    me_tmp = bpy.data.meshes.new(name="~temp~")
    bm.to_mesh(me_tmp)
    # bm.free()  # delay free
    obj_tmp = bpy.data.objects.new(name=me_tmp.name, object_data=me_tmp)
    scene.objects.link(obj_tmp)
    scene.update()
    ray_cast = obj_tmp.ray_cast

    EPS_BIAS = 0.0001

    faces_error = set()

    bm_faces_new = bm.faces[:]

    for f in bm_faces_new:
        no = f.normal
        no_sta = no * EPS_BIAS
        no_end = no * thickness
        for p in bmesh_face_points_random(f, num_points=6):
            # Cast the ray backwards
            p_a = p - no_sta
            p_b = p - no_end

            co, no, index = ray_cast(p_a, p_b)

            if index != -1:
                # Add the face we hit
                for f_iter in (f, bm_faces_new[index]):
                    # if the face wasn't triangulated, just use existing
                    f_org = face_map.get(f_iter, f_iter)
                    f_org_index = face_index_map_org[f_org]
                    faces_error.add(f_org_index)

    # finished with bm
    bm.free()

    scene.objects.unlink(obj_tmp)
    bpy.data.objects.remove(obj_tmp)
    bpy.data.meshes.remove(me_tmp)

    return array.array('i', faces_error)
