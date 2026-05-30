# CONTINUUM-ARENA // SECTOR ONSLAUGHT SYSTEM

An interactive, responsive 2D cyberpunk arcade tactical simulation built using **Python**, **Pygame**, and **Asyncio**. The engine features advanced time-manipulation mechanics, full keyboard/mouse responsiveness, dynamic canvas adjustments, and is architected to run seamlessly across local hardware, headless cloud servers (like Google Colab), and standard web browsers via Emscripten compilation.

## 🚀 Live Demo


---

## 🛠️ Key Architectural Features

*   **Temporal Control Engine ("God Powers"):** Real-time manipulation of the match matrix including custom frame rewinding (holding `R` restores health, positioning, and active projectile vectors), system freeze toggling, and global slow-motion dampening.
*   **Dual-Environment Resilience:** Built-in headless detection that safely intercepts missing video/audio hardware drivers on cloud server instances (such as Google Colab or Jupyter notebooks) using dummy fallbacks to prevent runtime crashes.
*   **Cross-Platform Browser Readiness:** Structured around asynchronous event loops (`asyncio` and `await`), making the codebase 100% compliant with **Pygbag** web compilation for instant, native browser deployment.
*   **Responsive Vector Canvas:** Real-time responsive layout grid with multi-line word-wrapping and structural UI positioning relative to the system viewport dimensions.
*  **AI Combat Engine:** Enemy tracks nearest target, adjusts approach distance, fires probabilistically, accelerates in Sudden Death.
*  **Mystery Box:** Slot-machine style roulette awards Plasma Cannon, +400 HP Shield Pack, or 2× Damage Booster.
*  **Mission Tracker:** 5 live missions: collect orbs, land hits, deal damage, use rewind, trigger Sudden Death.
*  **Time Orb Pickup:** Golden orbs spawn every 2.5s. Collecting one grants +200 HP and +5s to match timer.

---

## 🎮 Game Modes & Simulations

*   **1 Bot Challenge:** Standard tactical engagement against a localized single target droid matrix.
*   **Local 2-Player Split:** Local cross-input battle matching. Player 1 maps onto `WASD` + `SPACEBAR` while Player 2 utilizes `ARROW KEYS` + `RIGHT CTRL`.
*   **Multi-Bot Crossfire Layouts:** Aggressive multi-agent configurations simulating high-density dodge corridors against up to 3 autonomous enemy units simultaneously.
*   **Critical Onslaught (Sudden Death):** A high-stakes emergency state triggered under 20 seconds remaining, forcing environmental red shift visual grids and multiplying bot damage.

---
### 🎮 Controls & Hotkeys

* **Move:** `W`, `A`, `S`, `D` (Player 1) | `Arrow Keys` (Player 2)
* **Shoot:** `SPACEBAR` (Player 1) | `Right Ctrl` (Player 2)
* **Chrono-Rewind:** Hold `R`
* **Fullscreen Mode:** Press `F` or click the **🖥️ FULLSCREEN MODE** button in the top right corner of the dashboard header.


---
