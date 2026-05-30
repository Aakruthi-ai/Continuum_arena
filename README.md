# CONTINUUM-ARENA // SECTOR ONSLAUGHT SYSTEM

An interactive, responsive 2D cyberpunk arcade tactical simulation built using **Python**, **Pygame**, and **Asyncio**. The engine features advanced time-manipulation mechanics, full keyboard/mouse responsiveness, dynamic canvas adjustments, and is architected to run seamlessly across local hardware, headless cloud servers (like Google Colab), and standard web browsers via Emscripten compilation.

## 🚀 Live Demo
*Deploy your hosted link here! (e.g., https://yourusername.github.io/chrono-arena/)*

---

## 🛠️ Key Architectural Features

*   **Temporal Control Engine ("God Powers"):** Real-time manipulation of the match matrix including custom frame rewinding (holding `R` restores health, positioning, and active projectile vectors), system freeze toggling, and global slow-motion dampening.
*   **Dual-Environment Resilience:** Built-in headless detection that safely intercepts missing video/audio hardware drivers on cloud server instances (such as Google Colab or Jupyter notebooks) using dummy fallbacks to prevent runtime crashes.
*   **Cross-Platform Browser Readiness:** Structured around asynchronous event loops (`asyncio` and `await`), making the codebase 100% compliant with **Pygbag** web compilation for instant, native browser deployment.
*   **Responsive Vector Canvas:** Real-time responsive layout grid with multi-line word-wrapping and structural UI positioning relative to the system viewport dimensions.

---

## 🎮 Game Modes & Simulations

*   **1 Bot Challenge:** Standard tactical engagement against a localized single target droid matrix.
*   **Local 2-Player Split:** Local cross-input battle matching. Player 1 maps onto `WASD` + `SPACEBAR` while Player 2 utilizes `ARROW KEYS` + `RIGHT CTRL`.
*   **Multi-Bot Crossfire Layouts:** Aggressive multi-agent configurations simulating high-density dodge corridors against up to 3 autonomous enemy units simultaneously.
*   **Critical Onslaught (Sudden Death):** A high-stakes emergency state triggered under 20 seconds remaining, forcing environmental red shift visual grids and multiplying bot damage.

---
