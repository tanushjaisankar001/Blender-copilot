# 🚀 Universal AI Node Copilot for Blender (V-2.0)

An industrial-grade, AI-powered Copilot for Blender 4.0+. This add-on connects Blender directly to Google's Gemini API, allowing you to generate complex Geometry Node trees, procedural materials, and complete scenes entirely through natural language.

Designed with a resilient, non-blocking asynchronous architecture and an autonomous self-healing loop.

## ✨ What's New in V-2.0: The "Studio" Update

V-2.0 is a complete engine overhaul, transforming the tool from a basic script into a commercial-grade add-on.

### 🧠 The Async Engine & Self-Healing Loop
* **Zero UI Freezing:** Code generation runs on a background thread. You can continue working, modeling, or moving the camera while the AI thinks.
* **Autonomous Self-Healing:** If the AI writes broken Python code or uses a deprecated API call, the engine intercepts the traceback error before Blender crashes, silently sends the error back to the LLM, and forces it to rewrite a "Healed Draft" on the fly.
* **Network Resilience:** Built-in Exponential Backoff handles API rate limits (HTTP 429), and a strict 15-second timeout prevents the connection from hanging.

### 🎨 Material & Shader Mastery
* **Shader Node Support:** The "Universal Eye" context-gatherer now reads your active object's Material/Shader nodes alongside Geometry Nodes, allowing you to prompt for complex, procedural materials.
* **Strict Blender 4.0+ Compliance:** The AI is strictly prompted to understand the Blender 4.0 `Principled BSDF` overhaul (e.g., using `Emission Color` instead of `Emission`, and `Specular IOR Level`).

### 🖥️ UX & Integration
* **Secure API Key Integration:** API keys are no longer hardcoded. Securely enter your Gemini API key via Blender's built-in **Edit > Preferences > Add-ons** menu.
* **Native Undo Wrapper:** Every successful AI generation is wrapped in a single history step. If you don't like the result, press `Ctrl + Z` (or `Cmd + Z`) to instantly wipe the generation and restore your scene.
* **Inline Status Monitor & Kill Switch:** Clean, text-based status updates (`Ready` ➔ `Thinking...` ➔ `✅ Successful!`) with an emergency `[ X ]` kill switch to force-stop the background thread if needed.

---

## 🛠️ Installation

1. Click **Code > Download ZIP** on this repository.
2. Open Blender 4.0+ and go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select the downloaded ZIP file.
4. Check the box to enable **3D View: AI Node Copilot V2**.
5. Click the dropdown arrow next to the add-on name to open the Preferences.
6. Paste your **Google Gemini API Key** into the password field.

## 🕹️ How to Use

1. Press `N` in the 3D Viewport to open the right-side toolbar.
2. Click on the **AI Copilot** tab.
3. Select an object (or leave the scene empty).
4. Type your prompt into the text box and click **Execute**.

### 📝 Example Prompts

**Procedural Geometry (The Sea Urchin):**
> "Create a UV sphere. Create a separate, tall, thin cone object and hide it. Add a geometry nodes setup to the sphere that distributes points on faces, instances the hidden cone object onto those points, and aligns their euler rotation to the face normals using the Z axis."

**Procedural Materials:**
> "Create a cube. Create a glowing blue glass material and apply it to the cube."

**Full Scene Generation (Synthwave):**
> "Delete all objects. Create a massive plane and scale it up by 10. Add a wireframe modifier to the plane. Create a glowing neon pink material using an emission shader and apply it to the plane. Create a UV sphere, move it up on the Z axis by 5 units, and apply a glowing yellow emission material to it to look like a sun."

---

## 🏗️ Architecture Note
This add-on demonstrates advanced LLM integration with strict API environments. Because the AI is inherently "blind," it performs best when given structural, mathematical, and procedural "recipes" (like arrays, scatter functions, and modifiers) rather than highly specific topological requests (like "model a human face"). 

*Developed by Tanush Jaisankar.*
