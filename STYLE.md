\# STYLE.md



\# TreasureMasterBot Coding Style Guide



\## Philosophy



Write code as if it will be maintained for many years.



Prioritize:



\- Readability

\- Simplicity

\- Maintainability

\- Performance

\- Testability



Never optimize prematurely.



\---



\# General Rules



Always use:



\- Python 3.14+

\- Type hints

\- Dataclasses

\- Enum

\- Logging

\- pathlib



Avoid:



\- global variables

\- mutable globals

\- duplicated code

\- magic numbers

\- deeply nested functions



\---



\# Imports



Import order:



1\. Standard Library

2\. Third-party Libraries

3\. Local Imports



Example



```python

from dataclasses import dataclass

from pathlib import Path



import cv2

import numpy as np



from app.vision.objects import DetectionResult

```



Never use wildcard imports.



Never import inside functions unless necessary.



\---



\# Naming



Classes



PascalCase



Example



VisionEngine



TargetDetector



RotationTracker



Methods



snake\_case



Example



detect\_target()



estimate\_rotation()



Variables



snake\_case



Constants



UPPER\_CASE



\---



\# Dataclasses



Prefer dataclasses whenever possible.



Example



```python

@dataclass(slots=True)

class Target:

&#x20;   center\_x: int

&#x20;   center\_y: int

&#x20;   radius: int

```



Prefer immutable models where possible.



\---



\# Functions



One function should perform one task.



Maximum recommended length:



40 lines



Split larger functions.



\---



\# Classes



One class



One responsibility



Avoid giant classes.



Maximum recommended size:



300 lines



\---



\# Documentation



Every public class must have:



\- Purpose

\- Parameters

\- Return values



Example



```python

class VisionEngine:

&#x20;   """Main image processing pipeline."""

```



\---



\# Type Hints



Always use type hints.



Bad



```python

def detect(frame):

```



Good



```python

def detect(frame: np.ndarray) -> DetectionResult:

```



\---



\# Logging



Never use print().



Use logging.



Example



```python

logger.info("Target detected")

```



\---



\# Error Handling



Never ignore exceptions.



Bad



```python

except:

&#x20;   pass

```



Good



```python

except RuntimeError as exc:

&#x20;   logger.exception(exc)

```



\---



\# OpenCV Rules



Never modify the original frame.



Always work on copies.



Prefer vectorized operations.



Avoid unnecessary loops.



\---



\# Performance



Avoid:



Repeated allocations



Repeated conversions



Repeated copies



Cache reusable data.



\---



\# Threading



No shared mutable state.



Use queues or signals.



Never block the GUI thread.



\---



\# Testing



Every module must be testable independently.



No module should require GUI to run.



\---



\# Comments



Explain WHY.



Not WHAT.



Bad



```python

\# Increase x

x += 1

```



Good



```python

\# Move to the next projectile position

x += 1

```



\---



\# Code Generation Rules



Generate complete files.



Never omit imports.



Never generate placeholders.



Never leave TODO comments.



Always generate runnable code.



\---



\# Final Rule



If two implementations are possible:



Choose the simpler one.



Readable code is better than clever code.

