# 🧩 Phase 1 – Interactive Transformation to Exoskeleton Configuration

## 🎯 Goal

This phase implements an **interactive visualization** where, upon pressing a button,  
the system transforms the **initial grid configuration** into its **Exoskeleton arrangement**.

Unlike the analytical version, here we skip intermediate states.  
Only the **initial** and **final (Exoskeleton)** configurations are displayed.

---

## 🧠 Conceptual Overview

- The program loads a **starting configuration** (set of nodes/tiles).
- When the **“Generate Exoskeleton”** button is pressed:
  1. The algorithm computes the Exoskeleton layout.
  2. All modules (nodes) reposition to form the Exoskeleton.
  3. The final result is rendered — showing all **boundary boxes** and **connections**.

---

## 🔹 Functional Requirements

### Input

- A `Grid` object containing tile positions and IDs.
- Loaded from a configuration file (e.g. `config.json`).

### Output

- Visualization showing:
  - Final Exoskeleton arrangement.
  - All nodes repositioned.
  - All boundary boxes visible.

---

## 🔹 Implementation Overview

### Step 1 – Define the GUI

Use **PySide6** to create a simple interface:

- One main window.
- A `QGraphicsView` or `matplotlib` canvas to display tiles.
- A button labeled **“Generate Exoskeleton”**.
