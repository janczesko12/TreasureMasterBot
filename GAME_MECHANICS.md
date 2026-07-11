\# GAME\_MECHANICS.md



\# Treasure Master Game Mechanics



\## Purpose



This document describes the gameplay mechanics of Treasure Master.



The Vision Engine and Solver must strictly follow these rules.



Never assume game behavior that is not described here.



\---



\# Game Overview



Treasure Master is a real-time timing game.



The player throws projectiles toward a rotating target.



Each tap launches exactly one projectile.



The objective is to successfully embed every projectile into the rotating target.



The game becomes progressively faster and more difficult.



\---



\# Gameplay Loop



Level Starts



↓



Target Appears



↓



Target Rotates



↓



Player Throws Projectile



↓



Projectile Embeds



↓



Repeat



↓



Level Complete



↓



Next Level



\---



\# Player Input



The player has only one interaction:



Tap the screen.



Each tap launches exactly one projectile.



There is no dragging.



There is no aiming.



Timing is everything.



\---



\# Rotating Target



The target:



\- rotates continuously

\- may rotate clockwise

\- may rotate counter-clockwise

\- may change speed

\- may reverse direction

\- always rotates around its center



The center must be detected precisely.



\---



\# Projectiles



Projectiles become attached to the rotating target.



Each embedded projectile becomes a new obstacle.



Projectiles rotate together with the target.



\---



\# Collision Rules



A throw fails if:



\- the projectile hits another projectile

\- the projectile hits a forbidden obstacle



A successful throw:



\- embeds the projectile

\- increases projectile count



\---



\# Level Completion



A level is completed when:



All required projectiles are embedded successfully.



After completion the game shows:



\- Victory animation

\- Continue button

\- Next level



\---



\# Failure



Failure occurs after a collision.



The game may show:



\- Retry

\- Continue

\- Advertisement



The bot must recover automatically.



\---



\# Advertisements



Advertisements may appear:



\- after victory

\- after failure

\- randomly



The bot should:



\- detect advertisements

\- wait if necessary

\- detect close button

\- return to gameplay



\---



\# Detectable Objects



Vision must detect:



Target



Target Center



Embedded Projectiles



Current Projectile



Buttons



Advertisements



Menus



Popups



\---



\# Target Properties



Target contains:



Center



Radius



Rotation Direction



Angular Velocity



Current Angle



Confidence



\---



\# Projectile Properties



Every projectile contains:



Position



Angle



Confidence



Bounding Box



\---



\# Rotation



The bot must estimate:



Current Angle



Angular Velocity



Rotation Direction



Prediction Accuracy



\---



\# Solver Goal



The Solver must determine:



Should throw now?



Should wait?



Will the next throw collide?



When is the safest throw?



\---



\# Automation Goal



Automation executes only:



Tap



Wait



Recovery



Automation never makes gameplay decisions.



\---



\# Game States



Supported states:



MENU



PLAYING



VICTORY



FAILURE



ADVERTISEMENT



LOADING



UNKNOWN



Exactly one state should be active.



\---



\# Vision Goal



The Vision Engine should transform:



Frame



↓



DetectionResult



Containing:



GameState



Target



Projectiles



Buttons



Confidence



Timestamp



\---



\# Solver Goal



The Solver transforms:



DetectionResult



↓



Action



Supported actions:



Tap



Wait



Idle



\---



\# Performance Goal



Target Detection



99%



Projectile Detection



99%



Rotation Tracking



Stable



Solver Decision



< 1 ms



Vision



30 FPS minimum



Preview



60 FPS



\---



\# Long-Term Goal



TreasureMasterBot should:



Play indefinitely.



Complete levels autonomously.



Recover from failures.



Recover from advertisements.



Require no human interaction after startup.



Run for many hours continuously.



\---



\# Important Rule



Never guess game mechanics.



If uncertainty exists:



Return UNKNOWN.



Never invent gameplay behavior.



Always rely on observed game state.

