**Continuum Arena**

---
A fast-paced, cyberpunk vector-graphics arcade simulation built in Python using Pygame. Choose your chassis identity, allocate core attribute points, and jump into procedural combat maps where you must clear critical mission parameters while avoiding or terminating hostile rogue droids.
---

🚀 Key Architectural Updates
Interactive Visual Tutorial: The documentation tab now hosts an active, path-finding vector simulation displaying real-time movement, orb acquisition mechanisms, and visual splash feedback.

On-Screen Input Layout: Clear W, A, S, D tactical layout keys are rendered directly onto the tutorial interface to orient new operators instantly.

Dynamic Mission Generation: No two runs are identical. Entering the field generates randomized parameters across total core data metrics.

Procedural Map Structures: Map boundaries change configuration automatically per initialization, scattering unique sizing and placement arrays for structural obstacle blocks.

---

Combat Matrix Rules
Golden Time Orbs: Spawns randomly. Collecting them immediately provides +200 HP structural repair and grants a +5-second match timer extension.

Mystery Drops (? Boxes): Rolls one of four powerful chassis overhauls:

Auto-Rapid Lasers (Fast continuous stream output)

Matrix Defensive Shield (+300 dedicated shield HP protection)

Overcharge ATK (Lasers scale up to triple damage multipliers)

Regen Core (Instantly restores an extra +350 HP)

Victory Conditions: To successfully pass the simulation, you must finish every individual mission parameter logged in your left tracking grid AND wipe out the hostile bots before the timer hits 0. Removing all bots while missions remain incomplete results in a system processing failure!

---

Engine Code ArchitectureAsynchronous Loop Architecture (asyncio): Fully optimized for dual execution loops, preventing thread blocking during demanding UI refreshes.Procedural Math Matrices: Bullet tracking, entity directional angles, and visual bobbing dynamics are running clean calculations using real-time scalar geometry ($math.atan2$, $math.cos$, $math.sin$).Dynamic Snapshot System: The time-rewind state cache tracking dynamically records standard lists containing target states, layout positions, active projectiles, and target counts frame-by-frame for seamless execution.

---
