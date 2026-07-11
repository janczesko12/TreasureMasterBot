\# ROADMAP.md



\# TreasureMasterBot Roadmap



Current Version



v0.1



Current Status



Project initialization.



Architecture and documentation are completed.



No game logic has been implemented yet.



\---



\# Version 0.1



Goal



Project Foundation



Tasks



\- Project structure

\- Documentation

\- Dependencies

\- Logging

\- Configuration

\- Main application

\- Thread architecture



Status



Completed



\---



\# Version 0.2



Goal



Device Communication



Tasks



\- Detect Android device

\- Verify ADB connection

\- Device information

\- Automatic reconnect

\- Error handling



Target



Reliable communication with Android.



\---



\# Version 0.3



Goal



Screen Capture



Tasks



\- scrcpy integration

\- High-speed frame capture

\- Frame buffering

\- Stable FPS

\- Capture thread



Target



Stable 60 FPS preview.



\---



\# Version 0.4



Goal



Vision Foundation



Tasks



\- DetectionResult models

\- Target model

\- Projectile model

\- GameState model

\- Overlay renderer

\- Vision Engine skeleton



Target



Ready for object detection.



\---



\# Version 0.5



Goal



Target Detection



Tasks



\- Detect rotating target

\- Detect center

\- Detect radius

\- Estimate confidence

\- Stable tracking



Target



Reliable target detection.



\---



\# Version 0.6



Goal



Rotation Tracking



Tasks



\- Rotation direction

\- Angular velocity

\- Current angle

\- Temporal tracking

\- Smoothing



Target



Accurate rotation estimation.



\---



\# Version 0.7



Goal



Projectile Detection



Tasks



\- Detect embedded projectiles

\- Calculate projectile angles

\- Confidence estimation

\- Ignore false positives



Target



Reliable projectile detection.



\---



\# Version 0.8



Goal



Safe Throw Prediction



Tasks



\- Collision prediction

\- Safe angle calculation

\- Timing prediction

\- Throw window estimation



Target



Know exactly when to throw.



\---



\# Version 0.9



Goal



Automation



Tasks



\- Tap execution

\- Wait handling

\- Human-like delays

\- Verification after tap



Target



Automatic gameplay.



\---



\# Version 1.0



Goal



Autonomous Gameplay



Tasks



\- Complete levels

\- Detect victory

\- Detect failure

\- Press Next

\- Continue automatically



Target



Play Treasure Master without user interaction.



\---



\# Version 1.1



Goal



Advertisement Handling



Tasks



\- Detect ads

\- Wait until skippable

\- Detect close button

\- Return to game

\- Recover from failures



\---



\# Version 1.2



Goal



Statistics



Track



\- Runtime

\- Levels completed

\- Success rate

\- Failed throws

\- Average level time

\- FPS

\- CPU

\- RAM



\---



\# Version 1.3



Goal



Developer Tools



Features



\- Overlay modes

\- FPS monitor

\- Frame recorder

\- Screenshot capture

\- Detection visualizer

\- Debug logs



\---



\# Version 1.4



Goal



Performance Optimization



Tasks



\- Optimize OpenCV

\- Reduce CPU usage

\- Reduce memory usage

\- Improve capture latency

\- Faster processing



Target



Stable long-term execution.



\---



\# Version 1.5



Goal



Recovery System



Recover from



\- Device disconnect

\- ADB timeout

\- Lost capture

\- Unknown game state

\- Advertisement

\- App restart



Target



Bot never crashes.



\---



\# Version 2.0



Goal



Production Release



Requirements



\- Stable detection

\- Stable tracking

\- Stable automation

\- Stable recovery

\- Long runtime

\- Production-quality code



\---



\# Development Rules



Implement one version at a time.



Never skip unfinished milestones.



Never rewrite working modules.



Always test each feature before starting the next one.



Generate production-quality code only.



Never introduce placeholder implementations.



Every version must be fully functional before moving to the next.

