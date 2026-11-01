# Privacy and Safety

## Data minimization

- Only collect data required for the stated learning-support purpose.
- Separate raw events from derived hypotheses.
- Do not place raw dialogue, health signals or identity data on-chain.
- Keep tenant and runtime databases outside version control.

## Language evidence

Language output contains candidate evidence, not facts. It must retain:

- original span;
- model version;
- confidence;
- alternative explanations;
- user correction;
- follow-up verification.

Language evidence alone cannot change knowledge mastery, determine personality,
or produce a clinical diagnosis.

## High-risk behavior

Explicit self-harm, violence, abuse or immediate-danger signals must use a
deterministic escalation path to a trained human. A language model must not be
the final decision-maker.

## Minors and families

Production use with minors requires verifiable guardian consent, purpose
limitation, retention limits, access review and age-appropriate explanations.

## Research limits

Synthetic tests validate software behavior, not real-world educational efficacy.
Public benchmark results must report complete tradeoffs, including AUC,
log-loss, calibration and confidence intervals.

## Screen and media context

- Screen reading requires an explicit user confirmation phrase and a short-lived scope.
- Visible window metadata, accessible text and screenshots are separate scopes.
- Screenshots remain in memory and are never written to DAOQL.
- Hidden tabs, password fields, clipboard, camera, microphone, key logging and other accounts are outside coverage.
- OCR, transcription and video analysis only process files explicitly selected by the user.
- Raw files, window text and full transcripts remain local. Only coarse derived signals may reach the ambient planner.
- Refusing authorization is not evidence of concealment, avoidance or a psychological condition.
