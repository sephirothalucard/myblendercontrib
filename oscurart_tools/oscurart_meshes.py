import bpy
import math
import sys
import os
import stat
import bmesh
import time
import random

C = bpy.context
D = bpy.data

##-----------------------------RECONST---------------------------
def defReconst(self, OFFSET):
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    OBJETO = bpy.context.active_object
    OBDATA = bmesh.from_edit_mesh(OBJETO.data)
    OBDATA.select_flush(False)
    for vertice in OBDATA.verts[:]:
        if abs(vertice.co[0]) < OFFSET:
            vertice.co[0] = 0
    bpy.ops.mesh.select_all(action="DESELECT")
    for vertices in OBDATA.verts[:]:
      if vertices.co[0] < 0:
        vertices.select = 1
    bpy.ops.mesh.delete()
    bpy.ops.object.modifier_add(type='MIRROR')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.uv_texture_add()
    LENUVLISTSIM = len(bpy.data.objects[OBJETO.name].data.uv_textures)
    LENUVLISTSIM = LENUVLISTSIM - 1
    OBJETO.data.uv_textures[LENUVLISTSIM:][0].name = "SYMMETRICAL"
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=False, use_subsurf_data=0)
    bpy.ops.object.mode_set(mode="OBJECT", toggle= False)
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Mirror")
    bpy.ops.object.mode_set(mode="EDIT", toggle= False)
    OBDATA = bmesh.from_edit_mesh(OBJETO.data)
    OBDATA.select_flush(0)
    bpy.ops.mesh.uv_texture_add()
    LENUVLISTASIM = len(OBJETO.data.uv_textures)
    LENUVLISTASIM = LENUVLISTASIM  - 1
    OBJETO.data.uv_textures[LENUVLISTASIM:][0].name = "ASYMMETRICAL"
    OBJETO.data.uv_textures.active = OBJETO.data.uv_textures["ASYMMETRICAL"]
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=False, use_subsurf_data=0)

class reConst (bpy.types.Operator):
    bl_idname = "mesh.reconst_osc"
    bl_label = "ReConst Mesh"
    bl_options = {"REGISTER", "UNDO"}
    OFFSET=bpy.props.FloatProperty(name="Offset", default=0.001, min=-0, max=0.1)

    def execute(self,context):
        defReconst(self, self.OFFSET)
        return {'FINISHED'}

## -----------------------------------SELECT LEFT---------------------
def side (self, nombre, offset):

    bpy.ops.object.mode_set(mode="EDIT", toggle=0)
    OBJECT = bpy.context.active_object
    ODATA = bmesh.from_edit_mesh(OBJECT.data)
    MODE = bpy.context.mode
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    for VERTICE in ODATA.verts[:]:
        VERTICE.select = False
    if nombre == False:
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] < (offset):
                VERTICES.select = 1
    else:
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] > (offset):
                VERTICES.select = 1
    ODATA.select_flush(False)
    bpy.ops.object.mode_set(mode="EDIT", toggle=0)

class SelectMenor (bpy.types.Operator):
    bl_idname = "mesh.select_side_osc"
    bl_label = "Select Side"
    bl_options = {"REGISTER", "UNDO"}

    side = bpy.props.BoolProperty(name="Greater than zero", default=False)
    offset = bpy.props.FloatProperty(name="Offset", default=0)
    def execute(self,context):

        side(self, self.side, self.offset)

        return {'FINISHED'}


##-------------------------RESYM VG----------------------------------



class resymVertexGroups (bpy.types.Operator):
    bl_idname = "mesh.resym_vertex_weights_osc"
    bl_label = "Resym Vertex Weights"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):

        OBACTIVO = bpy.context.active_object
        VGACTIVO = OBACTIVO.vertex_groups.active.index
        
        bpy.ops.object.mode_set(mode='EDIT')
        BM = bmesh.from_edit_mesh(bpy.context.object.data)  
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        SELVER=[VERT.index for VERT in BM.verts[:] if VERT.select]   
        
        SYSBAR = os.sep     
         
        FILEPATH=bpy.data.filepath
        ACTIVEFOLDER=FILEPATH.rpartition(SYSBAR)[0]
        ENTFILEPATH= "%s%s%s_%s_SYM_TEMPLATE.xml" %  (ACTIVEFOLDER, SYSBAR, bpy.context.scene.name, bpy.context.object.name)
        XML=open(ENTFILEPATH ,mode="r")        
        SYMAP = eval(XML.readlines()[0])      
        INL = [VERT for VERT in SYMAP if SYMAP[VERT] in SELVER if VERT!= SYMAP[VERT]] 
        bpy.ops.mesh.select_all(action='DESELECT')
        for VERT in INL:
            BM.verts[VERT].select = True
        bpy.ops.object.vertex_group_assign(new=False)    
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')        
        for VERT in INL:
            for i, GRA in enumerate(OBACTIVO.data.vertices[SYMAP[VERT]].groups[:]):
                if GRA.group == VGACTIVO:
                    print (i)
                    EM = i                    

            for a, GRA in enumerate(OBACTIVO.data.vertices[VERT].groups[:]):     
                if GRA.group == VGACTIVO:
                    print (a)
                    REC = a

                    
            OBACTIVO.data.vertices[VERT].groups[REC].weight = OBACTIVO.data.vertices[SYMAP[VERT]].groups[EM].weight  
        XML.close()
        SYMAP.clear()  
      

        print("===============(JOB DONE)=============")
        return {'FINISHED'}


###------------------------IMPORT EXPORT GROUPS--------------------

class OscExportVG (bpy.types.Operator):
    bl_idname = "file.export_groups_osc"
    bl_label = "Export Groups"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        
        OBSEL=bpy.context.active_object
        FILEPATH = bpy.data.filepath
        
        with open(os.path.join(os.path.split(FILEPATH)[0],"%s.xml" % (OBSEL.name)), mode = "w") as FILE:
            VERTLIST = []
            LENVER = len(OBSEL.data.vertices)
            for VG in OBSEL.vertex_groups:
                BONELIST = []
                for VERTICE in range(0,LENVER):
                    try:
                        BONELIST.append((VERTICE,VG.weight(VERTICE),VG.name,))
                    except:
                        pass
                VERTLIST.append(BONELIST)
            NAMEGROUPLIST=[]
            for VG in OBSEL.vertex_groups:
                NAMEGROUPLIST.append(VG.name)
            VERTLIST.append(NAMEGROUPLIST)
            FILE.write(str(VERTLIST))

        with open(os.path.join(os.path.split(FILEPATH)[0],"%s_DATA.xml" % (OBSEL.name)), mode = "w") as FILE:
            DATAVER = []
            for VERT in OBSEL.data.vertices[:]:
                LISTVGTEMP = []
                for VGTEMP, GROUP in enumerate(VERT.groups[:]):
                    LISTVGTEMP.append((GROUP.group,VGTEMP))
                LISTVGTEMP=sorted(LISTVGTEMP)
                for TEMP, GROUP in enumerate(VERT.groups[:]):
                    DATAVER.append((VERT.index,TEMP,VERT.groups[LISTVGTEMP[TEMP][1]].weight))
            FILE.write(str(DATAVER))

        return {'FINISHED'}

class OscImportVG (bpy.types.Operator):
    bl_idname = "file.import_groups_osc"
    bl_label = "Import Groups"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):

        OBSEL = bpy.context.active_object
        if os.sys.platform.count("win"):
            print("WINDOWS")
            BAR = "\\"
        else:
            print("LINUX")
            BAR = "/"

        FILEPATH = bpy.data.filepath
        FILE = open(FILEPATH.rpartition(BAR)[0] + BAR + OBSEL.name + ".xml", mode="r")
        VERTLIST = FILE.readlines(0)
        VERTLIST = eval(VERTLIST[0])
        VERTLISTR = VERTLIST[:-1]
        GROUPLIST = VERTLIST[-1:]
        VGINDEX = 0


        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        for GROUP in GROUPLIST[0]:
            bpy.ops.object.vertex_group_add()
            OBSEL.vertex_groups[-1].name=GROUP



        for VG in OBSEL.vertex_groups[:]:
            bpy.ops.object.vertex_group_set_active(group=VG.name)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            for VERTI in VERTLISTR[VG.index]:
                OBSEL.data.vertices[VERTI[0]].select=1
            bpy.context.tool_settings.vertex_group_weight=1
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_assign(new=False)

        FILE.close()


        ## ----------- LEVANTO DATA ----
        # VARIABLES
        FILEPATH = bpy.data.filepath
        FILE = open(FILEPATH.rpartition(BAR)[0]+BAR+OBSEL.name+"_DATA.xml", mode="r")
        DATAPVER = FILE.readlines(0)
        DATAPVER = eval(DATAPVER[0])

        bpy.ops.object.mode_set(mode='OBJECT')
        for VERT in DATAPVER:
            OBSEL.data.vertices[VERT[0]].groups[VERT[1]].weight = VERT[2]
        FILE.close()
        # PASO A MODO PINTURA DE PESO
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        return {'FINISHED'}



## ------------------------------------ RESYM MESH--------------------------------------


def reSymSave (self):
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    BM = bmesh.from_edit_mesh(bpy.context.object.data)   
     
    L = {VERT.index : [VERT.co[0],VERT.co[1],VERT.co[2]] for VERT in BM.verts[:] if VERT.co[0] < 0.0001}
    R = {VERT.index : [-VERT.co[0],VERT.co[1],VERT.co[2]]  for VERT in BM.verts[:] if VERT.co[0] > -0.0001}
    
    SYMAP = {VERTL : VERTR for VERTR in R for VERTL in L if R[VERTR] == L[VERTL] }            
        
    FILEPATH=bpy.data.filepath
    ACTIVEFOLDER = os.path.split(FILEPATH)[0]
    ENTFILEPATH= "%s_%s_SYM_TEMPLATE.xml" %  (os.path.join(ACTIVEFOLDER, bpy.context.scene.name), bpy.context.object.name)
    with open(ENTFILEPATH ,mode="w") as file:   
        file.writelines(str(SYMAP))
        SYMAP.clear()

def reSymMesh (self, SELECTED, SIDE):    
    bpy.ops.object.mode_set(mode='EDIT')    
    BM = bmesh.from_edit_mesh(bpy.context.object.data)    
    FILEPATH=bpy.data.filepath
    ACTIVEFOLDER = os.path.split(FILEPATH)[0]
    ENTFILEPATH= "%s_%s_SYM_TEMPLATE.xml" %  (os.path.join(ACTIVEFOLDER,bpy.context.scene.name), bpy.context.object.name)
    with open(ENTFILEPATH ,mode="r") as file: 
        SYMAP = eval(file.readlines()[0])    
        if SIDE == "+-":
            if SELECTED:
                for VERT in SYMAP:
                    if BM.verts[SYMAP[VERT]].select:
                        if VERT == SYMAP[VERT]:
                            BM.verts[VERT].co[0] = 0
                            BM.verts[VERT].co[1] = BM.verts[SYMAP[VERT]].co[1]
                            BM.verts[VERT].co[2] = BM.verts[SYMAP[VERT]].co[2]            
                        else:    
                            BM.verts[VERT].co[0] = -BM.verts[SYMAP[VERT]].co[0]
                            BM.verts[VERT].co[1] = BM.verts[SYMAP[VERT]].co[1]
                            BM.verts[VERT].co[2] = BM.verts[SYMAP[VERT]].co[2]        
            else:    
                for VERT in SYMAP:
                    if VERT == SYMAP[VERT]:
                        BM.verts[VERT].co[0] = 0
                        BM.verts[VERT].co[1] = BM.verts[SYMAP[VERT]].co[1]
                        BM.verts[VERT].co[2] = BM.verts[SYMAP[VERT]].co[2]            
                    else:    
                        BM.verts[VERT].co[0] = -BM.verts[SYMAP[VERT]].co[0]
                        BM.verts[VERT].co[1] = BM.verts[SYMAP[VERT]].co[1]
                        BM.verts[VERT].co[2] = BM.verts[SYMAP[VERT]].co[2]
        else:
            if SELECTED:
                for VERT in SYMAP:
                    if BM.verts[VERT].select:
                        if VERT == SYMAP[VERT]:
                            BM.verts[SYMAP[VERT]].co[0] = 0
                            BM.verts[SYMAP[VERT]].co[1] = BM.verts[VERT].co[1]
                            BM.verts[SYMAP[VERT]].co[2] = BM.verts[VERT].co[2]            
                        else:    
                            BM.verts[SYMAP[VERT]].co[0] = -BM.verts[VERT].co[0]
                            BM.verts[SYMAP[VERT]].co[1] = BM.verts[VERT].co[1]
                            BM.verts[SYMAP[VERT]].co[2] = BM.verts[VERT].co[2]        
            else:    
                for VERT in SYMAP:
                    if VERT == SYMAP[VERT]:
                        BM.verts[SYMAP[VERT]].co[0] = 0
                        BM.verts[SYMAP[VERT]].co[1] = BM.verts[VERT].co[1]
                        BM.verts[SYMAP[VERT]].co[2] = BM.verts[VERT].co[2]            
                    else:    
                        BM.verts[SYMAP[VERT]].co[0] = -BM.verts[VERT].co[0]
                        BM.verts[SYMAP[VERT]].co[1] = BM.verts[VERT].co[1]
                        BM.verts[SYMAP[VERT]].co[2] = BM.verts[VERT].co[2]                    
        
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        SYMAP.clear()
        
class OscResymSave (bpy.types.Operator):
    bl_idname = "mesh.resym_save_map"
    bl_label = "Resym save XML Map"
    bl_options = {"REGISTER", "UNDO"}

    def execute (self, context):
        reSymSave(self)
        return {'FINISHED'}

class OscResymMesh (bpy.types.Operator):
    bl_idname = "mesh.resym_mesh"
    bl_label = "Resym save Apply XML"
    bl_options = {"REGISTER", "UNDO"}

    selected=bpy.props.BoolProperty(default=False, name="Only Selected")
    
    side = bpy.props.EnumProperty(
            name="Side:",
            description="Select Side.",
            items=(('+-', "+X to -X", "+X to -X"),
                   ('-+', "-X to +X", "-X to +X")),
            default='+-',
            )    
    
    def execute (self, context):
        reSymMesh(self, self.selected,self.side)
        return {'FINISHED'}
    


## -------------------------- OBJECT TO MESH --------------------------------------

def DefOscObjectToMesh():
    ACTOBJ = bpy.context.object
    MESH = ACTOBJ.to_mesh(scene=bpy.context.scene, apply_modifiers=True, settings="RENDER", calc_tessface=True)
    OBJECT = bpy.data.objects.new(("%s_Freeze") % (ACTOBJ.name), MESH)
    bpy.context.scene.objects.link(OBJECT)

class OscObjectToMesh(bpy.types.Operator):
    bl_idname = "mesh.object_to_mesh_osc"
    bl_label = "Object To Mesh"

    @classmethod
    def poll(cls, context):
        return True if context.active_object is not None and context.object.type == "MESH" else False

    def execute(self, context):
        DefOscObjectToMesh()
        return {'FINISHED'}


## ----------------------------- OVERLAP UV --------------------------------------------


def DefOscOverlapUv():
    rd = 4
    ACTOBJ = bpy.context.object
    inicio= time.time()
    bpy.ops.mesh.faces_mirror_uv(direction='POSITIVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    SELUVVERT = [ver for ver in ACTOBJ.data.uv_layers[ACTOBJ.data.uv_textures.active.name].data[:] if ver.select]
    MAY = [ver for ver in SELUVVERT if ver.uv[0] > .5]
    
    for vl in MAY:
        vl.uv = (1-vl.uv[0],vl.uv[1])   
                   
    bpy.ops.object.mode_set(mode='EDIT')
    print("Time elapsed: %4s seconds" % (time.time()-inicio))

class OscOverlapUv(bpy.types.Operator):
    bl_idname = "mesh.overlap_uv_faces"
    bl_label = "Overlap Uvs"


    def execute(self, context):
        DefOscOverlapUv()
        return {'FINISHED'}
