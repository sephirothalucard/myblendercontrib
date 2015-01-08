import bpy
from script_auto_complete.modal_handler import ModalHandler
from script_auto_complete.text_editor_utils import *
from script_auto_complete.documentation import get_documentation

running = False
def start():
    global running
    running = True
def stop():
    global running
    running = False

class AutoCompleteSettingsPanel(bpy.types.Panel):
    bl_idname = "script_auto_complete.settings_panel"
    bl_label = "Auto Complete"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
        
    def draw(self, context):
        layout = self.layout
        if running: layout.operator("script_auto_complete.stop_auto_completion", icon = "PANEL_CLOSE")
        else: layout.operator("script_auto_complete.start_auto_completion", icon = "LIBRARY_DATA_DIRECT")
        if get_documentation().is_build:
            layout.operator("script_auto_complete.rebuild_documentation")
        

class StartAutoCompletion(bpy.types.Operator):
    bl_idname = "script_auto_complete.start_auto_completion"
    bl_label = "Start"
    
    @classmethod
    def poll(cls, context):
        return not running
    
    def modal(self, context, event):
        if not running:
            self.modal_handler.free()
            return { "FINISHED" }
    
        block_event = False
        if active_text_block_exists():
            context.area.tag_redraw()
            block_event = self.modal_handler.update(event)
            
        if not block_event:
            return { "PASS_THROUGH" }
        return { "RUNNING_MODAL" }

    def invoke(self, context, event):
        get_documentation().build_if_necessary()
        self.modal_handler = ModalHandler()
        context.window_manager.modal_handler_add(self)
        start()
        return { "RUNNING_MODAL" }
        
        
class RebuildDocumentation(bpy.types.Operator):
    bl_idname = "script_auto_complete.rebuild_documentation"
    bl_label = "Rebuild Documentation"
    
    @classmethod
    def poll(cls, context):
        return get_documentation().is_build
    
    def execute(self, context):
        get_documentation().build()
        return { "FINISHED" }
        
        
class StopAutoCompletion(bpy.types.Operator):
    bl_idname = "script_auto_complete.stop_auto_completion"
    bl_label = "Stop"
    
    @classmethod
    def poll(cls, context):
        return running
    
    def execute(self, context):
        stop()
        return { "FINISHED" }        