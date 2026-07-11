\# PROJECT.md



\# TreasureMasterBot



\## Project Overview



TreasureMasterBot is a professional desktop automation application designed exclusively for the Android game Treasure Master.



The application captures the game screen in real time, analyzes the current game state using computer vision, determines the optimal moment to throw, and performs touch actions through ADB.



The application is intended to play autonomously for extended periods while maintaining high reliability.



\---



\# Primary Goal



The bot should:



\- Complete levels automatically

\- Reach the highest possible level

\- Recover from errors

\- Continue indefinitely

\- Require no human interaction after startup



\---



\# Platform



Host:



Windows 11



Language:



Python 3.14+



Framework:



PySide6



Libraries:



\- OpenCV

\- NumPy

\- ADB

\- scrcpy



\---



\# Gameplay Overview



Treasure Master is a timing-based game.



The player throws projectiles toward a rotating target.



The objective is to hit the target while avoiding collisions with existing projectiles.



Each successful throw embeds a new projectile.



When all required projectiles have been thrown successfully, the level is completed.



\---



\# Core Gameplay Loop



Capture Frame



↓



Detect Game State



↓



Detect Target



↓



Detect Existing Projectiles



↓



Estimate Rotation



↓



Predict Safe Throw Window



↓



Execute Tap



↓



Verify Result



↓



Repeat



\---



\# Vision Responsibilities



The Vision Engine must detect:



\- Rotating target

\- Target center

\- Rotation direction

\- Angular velocity

\- Embedded projectiles

\- Current projectile

\- UI buttons

\- Advertisements

\- Victory screen

\- Failure screen

\- Loading screen



\---



\# Solver Responsibilities



The Solver determines:



\- Whether it is safe to throw

\- When to throw

\- Whether to wait

\- Whether to retry

\- Whether to continue



The Solver never reads image data directly.



\---



\# Automation Responsibilities



Automation performs:



\- Tap

\- Swipe

\- Wait

\- Recovery



Automation never performs detection.



\---



\# GUI Responsibilities



GUI provides:



\- Live Preview

\- FPS

\- Logs

\- Settings

\- Start

\- Stop

\- Debug Overlay



GUI never contains game logic.



\---



\# Target Detection



The detector must identify:



\- Center position

\- Radius

\- Rotation angle

\- Rotation direction

\- Rotation speed



Detection must remain stable even during animation.



\---



\# Projectile Detection



Every projectile must include:



\- Position

\- Angle

\- Confidence



\---



\# Safe Throw Prediction



The Solver predicts:



\- Next safe angle

\- Collision risk

\- Throw timing



The objective is to maximize successful throws.



\---



\# Game States



Supported states:



\- MENU

\- PLAYING

\- VICTORY

\- FAILURE

\- LOADING

\- ADVERTISEMENT

\- UNKNOWN



The current state must always be known.



\---



\# Advertisement Handling



The application should:



\- Detect advertisements

\- Wait if necessary

\- Detect close button

\- Return to gameplay



\---



\# Error Recovery



Recover automatically from:



\- Device disconnect

\- ADB timeout

\- scrcpy crash

\- Unexpected popup

\- Lost game state

\- Capture failure



The application should never terminate unexpectedly.



\---



\# Performance Goals



Live Preview:



60 FPS



Vision:



30 FPS minimum



Detection Accuracy:



99%



Target Tracking:



Stable



Memory:



Below 500 MB



CPU:



Below 20%



\---



\# Logging



Log:



\- Startup

\- Device connection

\- Frame capture

\- Detection

\- Solver decision

\- Tap execution

\- Advertisement

\- Recovery

\- Level completion



\---



\# Future Features



\- Statistics

\- Session reports

\- Performance graphs

\- Debug recorder

\- Automatic updates



\---



\# Success Criteria



A successful version of TreasureMasterBot can:



\- Detect the rotating target

\- Detect every embedded projectile

\- Predict safe throw timing

\- Complete levels automatically

\- Handle advertisements

\- Continue playing for many hours without user intervention



\---



\# Development Philosophy



Implement one feature at a time.



Never sacrifice stability for speed.



Prefer simple, reliable algorithms over complex solutions.



Every module must be independently testable.



Every architectural decision should improve maintainability.



The final objective is a stable, production-quality Treasure Master automation system.

