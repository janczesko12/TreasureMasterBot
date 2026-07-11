\# TESTING.md



\# TreasureMasterBot Testing Guide



\## Philosophy



Every feature must be testable before it is merged.



Never implement large features without verification.



Testing is mandatory.



\---



\# Testing Order



Always test in this order:



1\. Unit Tests

2\. Screenshot Tests

3\. Video Tests

4\. Live Device Tests

5\. Long Session Tests



Never skip steps.



\---



\# Unit Tests



Every independent module must have unit tests.



Examples:



\- Rotation calculations

\- Angle normalization

\- Collision prediction

\- Geometry helpers



Unit tests must not require:



\- Android device

\- scrcpy

\- GUI



\---



\# Screenshot Tests



Each Vision module must be tested using screenshots.



Folder:



tests/screenshots/



Example:



tests/screenshots/



level\_001.png



level\_002.png



victory.png



failure.png



menu.png



advertisement.png



Expected output:



DetectionResult



\---



\# Video Tests



Folder:



tests/videos/



Each detector should work on recorded gameplay.



Measure:



\- FPS

\- Detection accuracy

\- False positives

\- False negatives



\---



\# Live Device Tests



Verify:



ADB connection



Capture



Vision



Solver



Automation



Measure:



Frame latency



Tap latency



Detection latency



\---



\# Long Session Tests



Run:



30 minutes



1 hour



3 hours



8 hours



Verify:



No memory leaks



No crashes



No freezes



No FPS degradation



\---



\# Vision Validation



Target Detector



Must verify:



Center



Radius



Rotation



Confidence



Projectile Detector



Must verify:



Count



Position



Angle



Confidence



\---



\# Solver Validation



Verify:



Correct throw timing



Collision avoidance



Reaction time



Consistency



\---



\# Automation Validation



Verify:



Tap location



Tap timing



Recovery



Retry



Advertisement handling



\---



\# Performance Targets



Capture



60 FPS



Vision



30 FPS minimum



Solver



Below 1 ms



Memory



Below 500 MB



CPU



Below 20%



\---



\# Regression Tests



Every bug fixed should receive:



\- Screenshot

\- Video

\- Test case



Never reintroduce solved bugs.



\---



\# Bug Report Template



Bug:



Environment:



Screenshot:



Expected Result:



Actual Result:



Steps to Reproduce:



Priority:



Critical



High



Medium



Low



\---



\# Before Merge Checklist



☐ Code builds



☐ Imports valid



☐ Unit tests pass



☐ Screenshot tests pass



☐ Video tests pass



☐ No crashes



☐ No warnings



☐ Documentation updated



\---



\# Final Rule



If a feature cannot be tested,



it is not finished.

