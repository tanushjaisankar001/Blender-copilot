bl_info = {
    "name": "AI Node Copilot V3.4",
    "author": "Tanush Jaisankar",
    "version": (3, 4, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > AI Copilot",
    "description": "Commercial-grade AI Copilot with Timeout & Kill Switch.",
    "category": "3D View",
}

import bpy
import urllib.request
import urllib.error
import json
import traceback
import threading
import queue
import time
import socket

ai_queue = queue.Queue()

_ai_state = {
    "original_prompt": "",
    "system_instruction": "",
    "api_key": ""
}

class AICopilotPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__ if __name__ != "__main__" else __package__

    api_key: bpy.props.StringProperty(
        name="Gemini API Key",
        description="Enter your Google Gemini API Key",
        default="",
        subtype='PASSWORD',
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "api_key")
        if not self.api_key:
            layout.label(text="⚠️ Please enter your API Key to use the Copilot!", icon='ERROR')


def ask_gemini_thread(prompt_text, system_instruction, api_key, task_type="PASS_1"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    
    max_retries = 3
    delay = 2.0
    
    for attempt in range(max_retries):
        try:
            # Added a strict 15-second timeout so it never hangs forever
            with urllib.request.urlopen(req, timeout=15.0) as response:
                result = json.loads(response.read().decode('utf-8'))
                code = result['candidates'][0]['content']['parts'][0]['text']
                clean_code = code.replace("```python", "").replace("```", "").strip()
                ai_queue.put({"status": "success", "code": clean_code, "task": task_type})
                return
                
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay *= 2
            else:
                ai_queue.put({"status": "error", "error": f"HTTP Error {e.code}"})
                return
        except socket.timeout:
            ai_queue.put({"status": "error", "error": "Request timed out. Google server is slow."})
            return
        except Exception as e:
            ai_queue.put({"status": "error", "error": str(e)})
            return
            
    ai_queue.put({"status": "error", "error": "Max retries reached. API quota likely exhausted."})


def check_ai_queue():
    if not bpy.context.scene.ai_is_thinking:
        return None
        
    try:
        result = ai_queue.get_nowait()
    except queue.Empty:
        return 0.1
        
    if result["status"] == "error":
        bpy.context.scene.ai_status_msg = f"❌ {result['error']}"
        bpy.context.scene.ai_is_thinking = False
        return None
        
    if result["task"] == "PASS_1":
        generated_code = result["code"]
        
        try:
            bpy.ops.ed.undo_push(message="Before AI Generation")
            exec(generated_code, globals(), locals())
            bpy.ops.ed.undo_push(message="AI Generation Completed")
            bpy.context.scene.ai_status_msg = "✅ Generation Successful!"
            bpy.context.scene.ai_is_thinking = False
            return None
            
        except Exception as first_error:
            error_msg = str(first_error)
            bpy.context.scene.ai_status_msg = "⚠️ Error caught. Self-healing..."
            
            correction_prompt = (
                f"I tried to run your code for: '{_ai_state['original_prompt']}', but got this error:\n{error_msg}\n\n"
                f"Broken code:\n{generated_code}\n\nFix it strictly using Blender 4.0 API. ONLY raw Python code."
            )
            thread = threading.Thread(target=ask_gemini_thread, args=(correction_prompt, _ai_state["system_instruction"], _ai_state["api_key"], "PASS_2"))
            thread.start()
            return 0.1
            
    elif result["task"] == "PASS_2":
        fixed_code = result["code"]
        try:
            bpy.ops.ed.undo_push(message="Before AI Generation")
            exec(fixed_code, globals(), locals())
            bpy.ops.ed.undo_push(message="AI Generation (Healed)")
            bpy.context.scene.ai_status_msg = "✅ Healed & Successful!"
        except Exception as fatal_error:
            traceback.print_exc()
            bpy.context.scene.ai_status_msg = "❌ Fatal Error. Check console."
            
        bpy.context.scene.ai_is_thinking = False
        return None


# --- EMERGENCY RESET OPERATOR ---
class NODE_OT_reset_copilot(bpy.types.Operator):
    bl_idname = "node.reset_copilot"
    bl_label = "Force Reset"
    bl_description = "Click this if the AI gets stuck thinking"

    def execute(self, context):
        context.scene.ai_is_thinking = False
        context.scene.ai_status_msg = "⚠️ Forcefully Reset"
        # Clear any junk left in the queue
        while not ai_queue.empty():
            try:
                ai_queue.get_nowait()
            except queue.Empty:
                break
        return {'FINISHED'}


class NODE_OT_generate_v3(bpy.types.Operator):
    bl_idname = "node.generate_v3"
    bl_label = "Ask Copilot"
    bl_description = "Send prompt and current state to AI Copilot"

    def get_universal_context(self, context):
        ctx = "CURRENT BLENDER STATE:\n"
        selected = context.selected_objects
        active = context.active_object
        
        if not selected:
            ctx += "- No objects currently selected.\n"
        else:
            ctx += f"- Active Object: '{active.name}' (Type: {active.type})\n"
            
        if active:
            gn_mod = next((mod for mod in active.modifiers if mod.type == 'NODES' and mod.node_group), None)
            if gn_mod:
                ctx += f"\nGEOMETRY NODES ON '{active.name}':\n"
                for n in gn_mod.node_group.nodes:
                    ctx += f" - Name: '{n.name}' | Type: {n.bl_idname}\n"
            
            if active.active_material and active.active_material.use_nodes:
                ctx += f"\nMATERIAL NODES ON '{active.name}' ({active.active_material.name}):\n"
                for n in active.active_material.node_tree.nodes:
                    ctx += f" - Name: '{n.name}' | Type: {n.bl_idname}\n"
        return ctx

    def execute(self, context):
        prefs = context.preferences.addons[__package__ if __package__ else __name__].preferences
        api_key = prefs.api_key
        
        if not api_key:
            context.scene.ai_status_msg = "❌ Missing API Key in Preferences!"
            return {'CANCELLED'}

        user_prompt = context.scene.ai_node_prompt
        if not user_prompt.strip():
            context.scene.ai_status_msg = "⚠️ Prompt is empty!"
            return {'CANCELLED'}
        
        if context.scene.ai_is_thinking:
            return {'CANCELLED'}

        context.scene.ai_is_thinking = True
        context.scene.ai_status_msg = "Thinking..."
        
        current_state_text = self.get_universal_context(context)
        
        system_instruction = (
            "You are an industrial-grade Blender 4.0+ Python Copilot. "
            "You handle BOTH Geometry Nodes AND Materials (Shader Nodes). "
            "CRITICAL BULLETPROOF RULES: "
            "1. DELETING/SELECTING: NEVER use bpy.ops.object.delete(). ALWAYS use: obj = bpy.data.objects.get('Name'); if obj: bpy.data.objects.remove(obj, do_unlink=True). "
            "2. ADDING MESHES: STRICT API ONLY: bpy.ops.mesh.primitive_cube_add(), bpy.ops.mesh.primitive_uv_sphere_add(), bpy.ops.mesh.primitive_cylinder_add(), bpy.ops.mesh.primitive_cone_add(). Capture obj immediately. "
            "3. GEO TREES: Create with bpy.data.node_groups.new('Tree', 'GeometryNodeTree'). Wipe sockets with node_tree.interface.clear() then explicitly create new 'Geometry' sockets. "
            "4. MATERIALS: Create with mat = bpy.data.materials.new('Name'); mat.use_nodes = True. Get BSDF using: bsdf = mat.node_tree.nodes.get('Principled BSDF'). "
            "BLENDER 4.0 BSDF SOCKETS: 'Specular' is now 'Specular IOR Level'. 'Transmission' is 'Transmission Weight'. 'Emission' is 'Emission Color'. NEVER use old names. "
            "5. NODE NAMES & MODIFIERS: Strict PascalCase. Align Euler to Vector is 'FunctionNodeAlignEulerToVector'. Wireframe modifier replace property is strictly 'use_replace' (NOT use_replace_original). Object Info nodes assign via socket, NEVER via property. Shader nodes use 'ShaderNode'. "
            "6. VECTORS/COLORS: Pass tuples for vectors (0.1, 0.1, 0.1). Colors use 4 floats (R,G,B,A). "
            "IMPORTANT: Output ONLY valid, raw Python code. Do not use markdown."
        )

        full_prompt = f"{current_state_text}\n\nUSER REQUEST: {user_prompt}"
        
        _ai_state["original_prompt"] = user_prompt
        _ai_state["system_instruction"] = system_instruction
        _ai_state["api_key"] = api_key
        
        while not ai_queue.empty():
            try:
                ai_queue.get_nowait()
            except queue.Empty:
                break
            
        thread = threading.Thread(target=ask_gemini_thread, args=(full_prompt, system_instruction, api_key, "PASS_1"))
        thread.start()

        if not bpy.app.timers.is_registered(check_ai_queue):
            bpy.app.timers.register(check_ai_queue)
        
        return {'FINISHED'}


class VIEW3D_PT_ai_node_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AI Copilot'
    bl_label = "Universal Copilot V3.4"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="Command your scene:")
        layout.prop(scene, "ai_node_prompt", text="") 
        layout.separator() 
        
        # Modified row to include the Kill Switch when thinking
        row = layout.row(align=True)
        if scene.ai_is_thinking:
            row.operator("node.generate_v3", text="Thinking...", icon='TIME')
            row.operator("node.reset_copilot", text="", icon='X') # The Kill Switch
        else:
            row.operator("node.generate_v3", text="Execute")
            
        layout.separator()
        
        box = layout.box()
        box.label(text=scene.ai_status_msg)

classes = (
    AICopilotPreferences,
    NODE_OT_generate_v3,
    NODE_OT_reset_copilot,
    VIEW3D_PT_ai_node_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ai_node_prompt = bpy.props.StringProperty(name="Prompt", default="")
    bpy.types.Scene.ai_status_msg = bpy.props.StringProperty(name="Status", default="Ready")
    bpy.types.Scene.ai_is_thinking = bpy.props.BoolProperty(default=False)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ai_node_prompt
    del bpy.types.Scene.ai_status_msg
    del bpy.types.Scene.ai_is_thinking
    if bpy.app.timers.is_registered(check_ai_queue):
        bpy.app.timers.unregister(check_ai_queue)

if __name__ == "__main__":
    register()