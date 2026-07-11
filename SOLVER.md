\# SOLVER.md



\# TreasureMasterBot Solver



\## Purpose



The Solver is responsible for making decisions.



The Solver never:



\- reads images

\- performs OpenCV

\- executes ADB commands



The Solver receives structured data from the Vision Engine and returns Actions.



\---



\# Input



DetectionResult



Contains:



\- GameState

\- Target

\- EmbeddedProjectiles

\- CurrentProjectile

\- Buttons

\- Confidence

\- Timestamp



\---



\# Output



Action



Supported actions:



\- TapAction

\- WaitAction

\- IdleAction



Automation executes these actions.



\---



\# Decision Pipeline



DetectionResult



↓



Validate Data



↓



Predict Rotation



↓



Predict Collision



↓



Evaluate Safe Window



↓



Choose Action



↓



Return Action



\---



\# Validation



Before making any decision:



Verify:



\- Target detected

\- Center valid

\- Rotation stable

\- Confidence above threshold



If validation fails:



Return IdleAction.



\---



\# Rotation Prediction



Estimate:



\- Current angle

\- Angular velocity

\- Rotation direction



Predict:



Target position after:



10 ms



20 ms



30 ms



40 ms



50 ms



\---



\# Collision Prediction



For every projectile:



Calculate:



Angular distance



↓



Future position



↓



Collision probability



↓



Safe / Unsafe



\---



\# Safe Window



Safe Window is defined as:



No projectile occupies the predicted impact angle.



The Solver must always choose the earliest safe opportunity.



\---



\# Throw Strategy



Priority:



1\.



Immediate Safe Throw



↓



2\.



Wait for Safe Window



↓



3\.



Idle



Never throw into uncertain situations.



\---



\# Risk Levels



LOW



↓



MEDIUM



↓



HIGH



↓



CRITICAL



CRITICAL must never throw.



\---



\# Timing



Target reaction time:



< 1 ms



Never block execution.



\---



\# Error Handling



If:



Target lost



↓



Return IdleAction



If:



Rotation unstable



↓



Wait



If:



Confidence low



↓



Wait



Never guess.



\---



\# Recovery



If repeated failures occur:



Pause



↓



Re-detect target



↓



Continue



\---



\# Future Improvements



Adaptive timing



Dynamic prediction



Latency compensation



Human-like delays



Performance learning



\---



\# Performance Goals



Decision time:



< 1 ms



Accuracy:



99%



Wrong throws:



Near zero



\---



\# Development Rules



The Solver must remain deterministic.



Given identical DetectionResults:



The Solver must always return the same Action.



No randomness.



No AI.



No hidden state.



\---



\# Final Goal



The Solver should make the optimal decision every frame.



It should maximize successful throws while minimizing collision risk.



The Solver should require no human intervention.

