bl_info = {
    "name": "AI Node Copilot",
    "author": "Tanush Jaisankar",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > AI Copilot",
    "description": "Conversational AI Copilot for editing Blender nodes",
    "category": "Node",
}

import bpy
import urllib.request
import json
import traceback

# Paste your API key inside the quotes below
GEMINI_API_KEY = "YOUR_API_KEY_HERE"

class NODE_OT_generate_from_text(bpy.types.Operator):
    bl_idname = "node.generate_from_text"
    bl_label = "Ask Copilot"
    bl_description = "Send prompt and current state to AI Copilot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_prompt = context.scene.ai_node_prompt
        obj = context.active_object
        
        if not user_prompt.strip() or not obj:
            self.report({'WARNING'}, "Need a prompt and an active object!")
            return {'CANCELLED'}

        # --- THE "EYE": STATE EXTRACTION ---
        def get_tree_context(obj):
            gn_mod = next((mod for mod in obj.modifiers if mod.type == 'NODES' and mod.node_group), None)
            if not gn_mod: 
                return "CURRENT STATE: Clean slate. No Geometry Nodes exist on this object yet."
            
            tree = gn_mod.node_group
            ctx = f"CURRENT STATE (Modifier: '{gn_mod.name}', Tree: '{tree.name}'):\nEXISTING NODES:\n"
            for n in tree.nodes:
                ctx += f" - Name: '{n.name}' | Type: {n.bl_idname}\n"
            ctx += "EXISTING LINKS:\n"
            for l in tree.links:
                ctx += f" - {l.from_node.name} [{l.from_socket.name}] -> {l.to_node.name} [{l.to_socket.name}]\n"
            return ctx

        current_state_text = get_tree_context(obj)
        print("\n--- WHAT THE AI SEES ---")
        print(current_state_text)
        
        # --- THE COPILOT PROMPT ---
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        system_instruction = (
            "You are a Blender Copilot, a conversational AI editor for Geometry Nodes. "
            "You will be given the CURRENT STATE of the user's node tree, and their REQUEST. "
            "ALWAYS start your code by defining the tree, e.g., node_tree = bpy.context.active_object.modifiers['GeoNodes'].node_group "
            "If the tree is empty, build it from scratch using: gn_mod = obj.modifiers.new('GeoNodes', 'NODES'); gn_mod.node_group = bpy.data.node_groups.new('GeoTree', 'GeometryNodeTree'); node_tree = gn_mod.node_group. "
            "CRITICAL BLENDER 4.0+ API RULES: "
            "1. NEW TREES: Create input/output nodes using node_tree.nodes.new('NodeGroupInput') and 'NodeGroupOutput'. "
            "2. Node types MUST use PascalCase. "
            "3. UTILITY NODES: Math and Random Value use 'FunctionNode' (e.g., 'FunctionNodeRandomValue'). "
            "4. RANDOM VALUE: To set to vector, use exactly: node.data_type = 'FLOAT_VECTOR'. CRITICAL: Do NOT attempt to set the 'Min' or 'Max' default values manually via Python, just link its output directly. "
            "5. VECTORS: For 3D vector inputs, pass a tuple: (0.1, 0.1, 0.1). "
            "IMPORTANT: Output ONLY valid, raw Python code. Do not use markdown."
        )

        full_prompt = f"{current_state_text}\n\nUSER REQUEST: {user_prompt}"

        def ask_gemini(prompt_text):
            data = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "systemInstruction": {"parts": [{"text": system_instruction}]}
            }
            payload = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                code = result['candidates'][0]['content']['parts'][0]['text']
                return code.replace("```python", "").replace("```", "").strip()

        try:
            self.report({'INFO'}, "Copilot is thinking...")
            
            # PASS 1
            generated_code = ask_gemini(full_prompt)
            print("\n--- FIRST DRAFT ---")
            print(generated_code)
            
            try:
                exec(generated_code, globals(), locals())
                self.report({'INFO'}, "Copilot updated the nodes!")
                
            except Exception as first_error:
                error_msg = str(first_error)
                print(f"Draft failed: {error_msg}. Self-healing...")
                self.report({'WARNING'}, "Copilot made a typo. Auto-correcting...")
                
                # PASS 2: SELF-HEALING
                correction_prompt = (
                    f"I tried to run your code for the request: '{user_prompt}', but Blender threw this error:\n{error_msg}\n\n"
                    f"Here is your broken code:\n{generated_code}\n\n"
                    f"Fix the code. Output ONLY raw Python code."
                )
                fixed_code = ask_gemini(correction_prompt)
                exec(fixed_code, globals(), locals())
                self.report({'INFO'}, "Copilot recovered and updated nodes!")

        except Exception as final_error:
            print(f"\n--- FATAL ERROR ---")
            traceback.print_exc() 
            self.report({'ERROR'}, "Copilot failed. Check console.")
            
        return {'FINISHED'}

class VIEW3D_PT_ai_node_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AI Copilot'
    bl_label = "Node Copilot"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="Chat with your nodes:")
        layout.prop(scene, "ai_node_prompt", text="") 
        layout.separator() 
        layout.operator("node.generate_from_text", text="Ask Copilot", icon='COMMUNITY')

classes = (
    NODE_OT_generate_from_text,
    VIEW3D_PT_ai_node_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ai_node_prompt = bpy.props.StringProperty(
        name="Prompt",
        description="Tell Copilot what to build or change",
        default=""
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ai_node_prompt

if __name__ == "__main__":
    register()