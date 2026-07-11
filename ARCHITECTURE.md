\# ARCHITECTURE.md



\# TreasureMasterBot Architecture



\## Purpose



TreasureMasterBot is a modular desktop application for automating the Android game Treasure Master.



The architecture prioritizes:



\- Reliability

\- Performance

\- Readability

\- Maintainability

\- Separation of responsibilities



Every module has exactly one responsibility.



\---



\# High-Level Architecture



```

Android Device

&#x20;       │

&#x20;       ▼

ADB / scrcpy

&#x20;       │

&#x20;       ▼

Frame Capture

&#x20;       │

&#x20;       ▼

Vision Engine

&#x20;       │

&#x20;       ▼

Detection Result

&#x20;       │

&#x20;       ▼

Solver

&#x20;       │

&#x20;       ▼

Action

&#x20;       │

&#x20;       ▼

Automation

&#x20;       │

&#x20;       ▼

ADB Input

```



\---



\# Project Structure



```

TreasureMasterBot/



app/



core/



vision/



solver/



automation/



gui/



utils/



assets/



tests/



logs/

```



\---



\# Core Module



Responsibilities:



\- Device detection

\- ADB communication

\- scrcpy

\- Screen capture

\- Thread management



Never:



\- detect game objects

\- perform game logic

\- make decisions



\---



\# Vision Module



Responsibilities:



\- Detect rotating target

\- Detect target center

\- Detect rotation

\- Detect projectiles

\- Detect UI

\- Detect advertisements

\- Detect game state



Returns only structured data.



Never:



\- tap

\- swipe

\- solve the game



\---



\# Solver Module



Input:



DetectionResult



Output:



Action



Responsibilities:



\- Evaluate timing

\- Predict collisions

\- Decide when to throw

\- Decide when to wait

\- Decide recovery actions



Never:



\- read images

\- access OpenCV

\- access ADB



\---



\# Automation Module



Responsibilities:



\- Execute Tap

\- Execute Swipe

\- Execute Wait

\- Execute Recovery



Never:



\- detect objects

\- solve gameplay



\---



\# GUI Module



Responsibilities:



\- Live Preview

\- Debug Overlay

\- FPS

\- Logs

\- Settings

\- Controls



Never:



\- detect objects

\- execute ADB

\- contain solver logic



\---



\# Vision Pipeline



```

Frame



↓



Preprocessing



↓



Target Detection



↓



Projectile Detection



↓



Rotation Tracking



↓



Game State Detection



↓



DetectionResult

```



\---



\# Solver Pipeline



```

DetectionResult



↓



Timing Prediction



↓



Collision Check



↓



Decision



↓



Action

```



\---



\# Automation Pipeline



```

Action



↓



ADB Command



↓



Android Device

```



\---



\# Thread Model



Main Thread



↓



GUI



Capture Thread



↓



Vision Thread



↓



Solver Thread



↓



Automation Thread



No thread should block another.



\---



\# Data Flow



```

Frame



↓



Vision



↓



DetectionResult



↓



Solver



↓



Action



↓



Automation



↓



ADB

```



\---



\# DetectionResult



Contains:



\- GameState

\- Target

\- Projectiles

\- Confidence

\- Timestamp



\---



\# Target Model



Fields:



\- center\_x

\- center\_y

\- radius

\- rotation\_angle

\- angular\_velocity

\- rotation\_direction

\- confidence



\---



\# Projectile Model



Fields:



\- angle

\- position

\- confidence



\---



\# Action Model



Supported actions:



\- TapAction

\- SwipeAction

\- WaitAction

\- IdleAction



Automation executes Actions only.



\---



\# Performance Goals



Capture:



60 FPS



Vision:



30 FPS minimum



Solver:



Below 1 ms



Automation:



Instant



Memory:



Below 500 MB



CPU:



Below 20%



\---



\# Error Recovery



Recover from:



\- Device disconnect

\- ADB timeout

\- scrcpy crash

\- Lost frame

\- Unknown game state

\- Advertisement



The application should never terminate unexpectedly.



\---



\# Logging



Log:



\- Startup

\- Capture

\- Detection

\- Solver

\- Automation

\- Recovery

\- Errors



\---



\# Debug Modes



Support:



\- Original

\- Grayscale

\- Threshold

\- Edges

\- Contours

\- Target

\- Projectiles

\- Overlay



Developer mode should allow switching between all views.



\---



\# Design Principles



\- Single Responsibility Principle

\- Separation of Concerns

\- Composition over Inheritance

\- Immutable detection results

\- Type-safe models

\- Modular design



\---



\# Coding Rules



Never duplicate code.



Never mix responsibilities.



Never use global mutable state.



Always use dataclasses.



Always use type hints.



Always document public APIs.



Always keep modules independent.



\---



\# Final Goal



A stable automation system capable of:



\- Detecting the game state

\- Tracking the rotating target

\- Predicting safe throw timing

\- Completing levels autonomously

\- Recovering from errors

\- Running continuously for many hours

