# Tender Desktop Overlay

The optional Windows overlay displays short ambient prompts above the taskbar
and keeps a small conversation dock. It observes normalized local activity
categories only; raw window titles are not uploaded.

Run the API first, then:

```powershell
.\start_overlay.ps1 -Student S01 -Scenario gaokao_registration
```

The overlay is a prototype. Production deployment requires signed binaries,
accessibility review, stricter privacy controls and user-controlled retention.
