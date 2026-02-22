# AI Node Copilot for Blender 🧊🤖

A state-aware, conversational AI agent that procedurally generates and edits Geometry Nodes in Blender 5.0+. Powered by Python, the Blender API (`bpy`), and the Google Gemini LLM.

## 🚀 Overview
Unlike standard "one-shot" AI code generators, this Copilot acts as a true agentic assistant. It reads the current state of your 3D environment, maintains conversational context, and features an automated self-healing loop to catch and fix its own compilation errors in real-time.

### Key Features
* **Conversational Editing:** Give iterative commands (e.g., "Add cones", then "Replace cones with cubes", then "Randomize their scale"). 
* **Context Extraction (The "Eye"):** Before pinging the LLM, the add-on scans the active object, compiling a text-based map of all existing nodes, properties, and socket links to inject into the AI's prompt.
* **Self-Healing Loop:** If the AI hallucinates a Blender API call or mismatches a data type (like passing a float to a vector socket), the script catches the `Traceback` error, hides it from Blender to prevent crashes, and passes the error back to the LLM for an automated secondary rewrite.
* **Native UI Integration:** Fully integrated into the Blender 3D Viewport sidebar for a seamless workflow.

## 🧠 Architecture
1. **State Extraction:** Python translates the visual node tree into structured text data.
2. **Context Injection:** The user prompt and the state data are merged with rigid Blender 4.0+ API rules (handling strict PascalCase naming conventions, UI interface sockets, and vector typing).
3. **Execution & Verification:** The AI returns raw Python code. The `exec()` function attempts to run it.
4. **Correction:** If execution fails, the agent is prompted with the exact stack trace to self-correct.

## 🛠️ Installation & Setup
1. Download this repository as a `.zip` file.
2. Open Blender > Edit > Preferences > Get Extensions > Install from Disk.
3. Select the `.zip` file.
4. **Important:** Open the `__init__.py` file and paste your Google Gemini API key into the `GEMINI_API_KEY` variable.

## 💻 Usage
1. Open the **AI Copilot** tab in the View3D sidebar (press `N`).
2. Select any object in your scene.
3. Type your prompt (e.g., *"Create a setup that instances cubes onto a UV sphere"*).
4. Watch the Copilot build and wire the nodes automatically. 
5. Continue chatting to refine and edit the existing setup.
