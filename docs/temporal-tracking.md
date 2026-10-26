# Experimental temporal ball association

## Pure Python rules

BallTracker consumes bounded candidate batches and original source frame indices
and timestamps. It does not import OpenCV, NumPy, HTTP, or inference frameworks.
Each video owns its own tracker; no shared global tracking state exists.

Initialization requires three consecutive unique, temporally coherent candidates
with net image displacement above 0.8% of the source diagonal. Static fragments
and isolated detections do not become an observed track. Persistent moving false
objects can still satisfy these rules; association is not proof of ball identity.

Once initialized, constant image-velocity prediction gates candidates by residual
distance and maximum source-time-based displacement. Gates and ambiguity margins
scale with the image diagonal. They are experimental image parameters, not
physical ball speeds or confidence probabilities. Component size never chooses
the winner. Close competing candidates and truncated batches remain ambiguous.

A gap up to 0.18 seconds may retain track identity; the output contains a separate
prediction, never a measured observation. Longer gaps expire identity and require
new confirmation. Source-index discontinuities and recovered detections mark
break_before so renderers must not draw a solid line across missing evidence.

The statuses are searching, tentative, observed, predicted, and ambiguous. Only
observed carries an associated measured candidate. Prediction fields are separate;
out-of-image predictions are omitted. Newly confirmed tracks do not retroactively
turn earlier tentative frames into observations. IDs are local to one video.

The service validates monotonic source time/index and finite source coordinates
before mutating state. Explicit reset clears all video state.

## Initial verification

Thirteen service checks cover confirmation, static false objects, a distant
competing object, nearby ambiguity, candidate overflow, short-gap recovery,
long-gap identity reset, skipped frame indices, impossible jumps, irregular
source intervals, invalid input, reset/isolation, and interrupted initialization.
These tests establish rule behavior; real-video association evaluation is a
separate next increment. They do not establish tracking accuracy on real footage.

Contacts, racket strikes, rallies, 3D geometry, and physical speed are not inferred.
Camera drift is not compensated; any future trail is in raw image coordinates.
