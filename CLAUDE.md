\# CLAUDE.md



\# TreasureMasterBot Development Rules



\## Mission



TreasureMasterBot is a professional desktop automation application for the Android game Treasure Master.



The primary objective is to complete levels autonomously with high reliability while maintaining a modular, clean and maintainable codebase.



Every design decision should prioritize:



\- Reliability

\- Maintainability

\- Performance

\- Readability

\- Extensibility



\---



\# General Rules



Always understand the existing code before making changes.



Never rewrite working functionality.



Never remove features unless explicitly requested.



Prefer improving existing modules instead of replacing them.



Generate production-quality code only.



No placeholder implementations.



No TODO comments instead of working code.



Always use type hints.



Always document public classes and functions.



Always keep compatibility with existing modules.



\---



\# Development Workflow



Before modifying code:



1\. Read the repository.

2\. Understand the architecture.

3\. Explain the implementation plan.

4\. List affected files.

5\. Implement only the requested feature.

6\. Explain every important design decision.

7\. Verify consistency.



Never skip these steps.



\---



\# Architecture Rules



The project consists of independent modules.



Core modules:



\- core

\- vision

\- solver

\- automation

\- gui



Each module has exactly one responsibility.



Never mix responsibilities.



Examples:



Vision never performs taps.



Automation never performs detection.



Solver never accesses OpenCV directly.



GUI never contains game logic.



\---



\# Vision Rules



The Vision Engine is responsible only for understanding the game screen.



Responsibilities:



\- Detect game board

\- Detect rotating target

\- Detect embedded knives

\- Detect current projectile

\- Detect UI buttons

\- Detect advertisements

\- Detect game state



Vision returns structured data only.



Vision never performs taps.



Vision never makes decisions.



Use only classical OpenCV unless explicitly requested.



Avoid unnecessary AI models.



\---



\# Solver Rules



The Solver decides:



\- when to throw

\- when to wait

\- when to continue

\- when to recover



The Solver never reads images directly.



The Solver receives only structured objects from the Vision Engine.



\---



\# Automation Rules



Automation executes actions.



Responsibilities:



\- Tap

\- Swipe

\- Long Press

\- Wait

\- Recovery



Automation never performs image processing.



Automation never contains game logic.



\---



\# GUI Rules



GUI is only an interface.



Responsibilities:



\- Live Preview

\- FPS

\- Logs

\- Buttons

\- Settings

\- Debug Overlay



GUI never performs game logic.



\---



\# Performance Requirements



Target Preview FPS:



60 FPS



Vision Processing:



30 FPS minimum



Memory:



Below 500 MB



CPU:



Below 20%



The application must remain responsive at all times.



\---



\# Code Style



Use:



\- dataclasses

\- Enum

\- pathlib

\- logging

\- typing



Avoid:



\- global mutable state

\- duplicated code

\- magic numbers

\- unnecessary inheritance



Prefer composition over inheritance.



\---



\# Error Handling



The application must never crash because:



\- board not detected

\- advertisement shown

\- unexpected popup

\- capture failure

\- ADB timeout



Always recover gracefully.



\---



\# Logging



Log important events:



\- Device Connected

\- Capture Started

\- Frame Processed

\- Detection Completed

\- Solver Decision

\- Action Executed

\- Advertisement Detected

\- Recovery Started

\- Recovery Completed



\---



\# Testing



Every new module should be testable independently.



Detection modules must work on stored screenshots before being integrated into live capture.



Never merge untested detection logic.



\---



\# Before Writing Code



Always answer:



1\. What will be changed?

2\. Which files will change?

3\. Why is the change necessary?

4\. Are there simpler alternatives?

5\. Will compatibility be preserved?



Only then begin implementation.



\---



\# Output Rules



Generate complete files.



Do not generate partial snippets.



Do not omit imports.



Do not omit documentation.



Do not omit type hints.



Do not leave placeholder methods.



Always generate production-ready code.



\---



\# Treasure Master Rules



Assume the game is always played in portrait mode.



The primary gameplay loop is:



1\. Detect current game state.

2\. Detect rotating target.

3\. Detect embedded knives.

4\. Estimate safe throw timing.

5\. Execute tap.

6\. Verify result.

7\. Continue until level completion.

8\. Detect and close advertisements if needed.

9\. Proceed to the next level.



Every module should support this gameplay loop.



\---



\# Final Rule



Think before coding.



Quality is more important than speed.



Never sacrifice architecture for short-term convenience.

