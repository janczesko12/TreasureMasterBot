\# OPENCV.md



\# TreasureMasterBot OpenCV Guidelines



\## Purpose



This document defines how every Vision module should be implemented.



The goal is:



\- High FPS

\- Stable detection

\- Low CPU usage

\- Deterministic behavior

\- Easy debugging



Never sacrifice reliability for complexity.



\---



\# Image Format



Input



BGR



Resolution



Portrait



Expected Resolution



1080x2400



Never modify the original frame.



Always work on a copy.



\---



\# Processing Pipeline



Frame



↓



Crop



↓



Preprocess



↓



Detect



↓



Track



↓



Validate



↓



DetectionResult



Never skip validation.



\---



\# Preprocessing



Allowed



Gaussian Blur



Median Blur



Morphology



CLAHE



HSV Conversion



Canny



Threshold



Resize



ROI Cropping



Avoid:



Repeated conversions



Repeated resizing



Repeated allocations



\---



\# ROI



Always work inside Regions Of Interest whenever possible.



Never process the entire frame if only one area is required.



ROI must be updated dynamically.



\---



\# Target Detection



Preferred order



1\.



Contours



↓



2\.



Hough Circle



↓



3\.



Shape Matching



↓



4\.



Template Matching



Never rely on one detector.



Combine methods.



\---



\# Tracking



Prefer tracking over repeated detection.



Track



Target



Projectiles



Buttons



Game State



Reset tracking only when confidence drops.



\---



\# Confidence



Every detector returns



0.0



↓



1.0



Never use True / False.



\---



\# Performance



Target



<15 ms



Maximum



25 ms



If processing exceeds 25 ms:



Optimize before adding features.



\---



\# Thread Safety



Vision modules must be thread-safe.



Never share mutable state.



Never block capture thread.



\---



\# Memory



Avoid



Repeated allocations



Repeated copies



Repeated masks



Reuse buffers.



\---



\# Overlay



Overlay never modifies the source frame.



Always return:



Annotated Copy



Supported Layers



Bounding Boxes



Centers



Circles



Vectors



Labels



FPS



Confidence



\---



\# Tracking Rules



Track



Center



Rotation



Velocity



Direction



Projectile Count



Game State



Buttons



Advertisements



\---



\# Geometry



Always normalize angles.



Preferred Range



0°



↓



360°



Never compare floating angles directly.



Always use tolerances.



\---



\# Rotation



Store



Current Angle



Previous Angle



Angular Velocity



Angular Acceleration



Direction



Predict



Future Angle



\---



\# Detection Validation



Every detection must verify



Area



Aspect Ratio



Shape



Confidence



Location



History



Reject unstable detections.



\---



\# False Positives



Prefer



False Negative



over



False Positive.



It is better to miss one frame than execute a wrong tap.



\---



\# Timing



Vision should process



30+



FPS



Target



60 FPS



\---



\# Logging



Log



Detection Time



FPS



Confidence



Target Lost



Tracking Reset



State Changes



Never spam logs every frame.



\---



\# Debug



Support



Original



Gray



HSV



Mask



Edges



Contours



Tracking



Overlay



Heatmap



Every stage should be viewable independently.



\---



\# OpenCV Rules



Use



OpenCV



NumPy



Math



Geometry



Tracking



Avoid



OCR



Heavy AI



YOLO



TensorFlow



PyTorch



Unless explicitly approved.



\---



\# Final Rule



The Vision Engine must always be:



Fast



Deterministic



Stable



Debuggable



Reliable

