\# VISION.md



\# TreasureMasterBot Vision System



\## Purpose



The Vision Engine is responsible for understanding the game screen.



It never performs game logic.



It never performs taps.



It only converts pixels into structured information.



\---



\# Input



Input:



Android Frame (BGR)



Resolution:



Portrait



Typical size:



1080x2400



\---



\# Output



Output:



DetectionResult



Containing:



\- GameState

\- Target

\- EmbeddedProjectiles

\- CurrentProjectile

\- Buttons

\- Advertisements

\- Confidence

\- Timestamp



\---



\# Vision Pipeline



Frame



↓



Crop



↓



Preprocessing



↓



Target Detection



↓



Center Detection



↓



Rotation Tracking



↓



Projectile Detection



↓



Game State Detection



↓



DetectionResult



\---



\# Stage 1



Preprocessing



Tasks



\- Resize if necessary

\- Gaussian Blur

\- Noise Reduction

\- Color Correction



Never destroy useful edges.



\---



\# Stage 2



Target Detection



Goal



Locate the rotating target.



Detect:



Center



Radius



Bounding Box



Confidence



Possible methods



\- Hough Circle

\- Contours

\- Edge Detection



The detector must be deterministic.



\---



\# Stage 3



Center Detection



Calculate:



center\_x



center\_y



radius



The center must remain stable.



Maximum error:



±2 pixels



\---



\# Stage 4



Rotation Tracking



Track:



Current Angle



Rotation Direction



Angular Velocity



Acceleration



Predict:



Next Position



Future Angle



\---



\# Stage 5



Projectile Detection



Detect:



Every embedded projectile.



Return:



Position



Angle



Bounding Box



Confidence



\---



\# Stage 6



Current Projectile



Detect:



Projectile ready to throw.



Return:



Position



Bounding Box



Confidence



\---



\# Stage 7



Game State Detection



Supported:



MENU



PLAYING



VICTORY



FAILURE



ADVERTISEMENT



LOADING



UNKNOWN



Exactly one state.



\---



\# Stage 8



Button Detection



Detect:



Next



Retry



Continue



Close



Skip



Play



Buttons should include:



Bounding Box



Confidence



Label



\---



\# Stage 9



Advertisement Detection



Detect:



Video Ads



Static Ads



Reward Ads



Close Button



Skip Button



Timer



Return:



AdvertisementState



\---



\# Tracking



Objects should persist between frames.



Never detect everything from scratch.



Track:



Target



Projectiles



Buttons



State



\---



\# Confidence



Every detection returns:



0.0



↓



1.0



Never use binary success/failure.



\---



\# Performance Goals



Target Detection



<5 ms



Projectile Detection



<5 ms



Tracking



<2 ms



Overlay



<2 ms



Total Vision



<15 ms



Target FPS



60 FPS



Minimum



30 FPS



\---



\# Debug Modes



Support



Original



Gray



HSV



Threshold



Edges



Contours



Target



Projectiles



Tracking



Overlay



Every mode should be switchable.



\---



\# Overlay



Display:



Center



Radius



Target



Projectile Count



Current Angle



Angular Velocity



Game State



FPS



Confidence



\---



\# Failure Handling



If target missing:



Return UNKNOWN



If projectile missing:



Return empty list



If state unknown:



Return UNKNOWN



Never crash.



\---



\# OpenCV Rules



Use:



Contours



HoughCircles



Canny



HSV



Morphology



Template Matching



Tracking



Avoid:



OCR



Deep Learning



Neural Networks



Heavy AI models



Unless explicitly requested.



\---



\# Long-Term Goal



The Vision Engine should understand the game with enough accuracy that the Solver only needs to decide:



Throw



Wait



Recover



Nothing else.

