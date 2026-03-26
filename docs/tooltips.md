# KDS Lyric Performance Engine — Tooltip Reference

All tooltip strings defined in the application UI, organized by source file and location.

---

## Main Window Toolbar (`ui/main_window.py`)

### Row 1 — Project & File Actions

| Widget | Tooltip |
|--------|---------|
| Save | Save current project to file |
| Save As | Save project to a new location; creates folder-based project if enabled in Settings |
| Load | Load a project from a JSON file |
| Theme | Switch between dark and light theme |
| Settings | Open application settings (folder-based projects toggle) |
| Reveal Project | Open project folder in file manager |
| Export Fix Pack | Export all known fixes as a shareable zip for other machines |
| Import Fix Pack | Import a fix pack zip from another machine |
| Export Debug | Export a zip of logs, crash reports, and solution folders for debugging |
| Export Training | Export aligned audio + lyrics dataset for voice training |
| Reveal Autosave | Open the autosave folder in file manager |
| Reveal Backups | Open the backups folder in file manager |

### Row 2 — Render & Voice Controls

| Widget | Tooltip |
|--------|---------|
| Render Engine | Select the render engine mode for audio generation |
| Quality | Fast: fewer harmonics for real-time editing; High: full quality preview |
| Play Preview | Render and play audio preview for the current token, scope, and mode |
| Replay Last | Replay the last rendered preview audio |
| Singer | Select the active voice profile for synthesis |
| Personality | Vocal personality character applied to the singer |
| Mix Slider | Blend personality with base voice (0% = base only, 100% = full personality) |
| Auto Preview | Automatically play preview when sliders are released |

### Row 3 — Scope, Mode & Instrument Controls

| Widget | Tooltip |
|--------|---------|
| Scope: Section (disabled) | Select a range of tokens to enable Section scope |
| Pre-Roll Slider | Silence or context tokens added before the preview (0-2000ms) |
| Post-Roll Slider | Silence or context tokens added after the preview (0-2000ms) |
| Snap | Snap scope boundaries to the nearest word edges |
| Mode: Assist (disabled) | AI-assisted preview — coming later |
| Instrument Dropdown | Select an instrument patch to override voice-type synthesis |
| Edit Instrument | Open the Instrument Editor to adjust envelope, timbre, noise, and token defaults |
| Save As Instrument | Save current instrument settings as a new named instrument |
| Duplicate Instrument | Clone the selected instrument |
| Delete Instrument | Remove a user-created instrument (built-in presets cannot be deleted) |
| World Navigator | Open World Navigator globe overlay to switch workspaces visually |

---

## Inspector Panel (`ui/inspector_panel.py`)

### Parameter Sliders

| Widget | Tooltip |
|--------|---------|
| Duration Slider | How long the word sounds (0-2000ms) |
| Loudness Slider | Volume level for this token (0-200%) |
| Intensity Slider | Vocal energy and effort (0 = soft, 100 = maximum) |
| Pitch Offset Slider | Semitone shift from base pitch (-24 to +24) |

### Navigation Buttons

| Widget | Tooltip |
|--------|---------|
| OK | Lock this token with current settings and move on |
| Cancel | Revert changes to this token |
| Prev | Select the previous token |
| Next | Select the next token |

---

## Global Controls Panel (`ui/global_controls_panel.py`)

| Widget | Tooltip |
|--------|---------|
| Tempo Slider | Global tempo for the performance (40-240 BPM) |
| Key Dropdown | Musical key for the performance |
| Voice Type Dropdown | Voice type used for audio preview synthesis |

---

## Lyrics Panel (`ui/lyrics_panel.py`)

| Widget | Tooltip |
|--------|---------|
| Text Edit | Type or paste lyrics here, then click Tokenize to split into editable words |
| Tokenize Button | Split lyrics into individual word tokens for editing |

---

## Capture Panel (`ui/capture_panel.py`)

### Recording

| Widget | Tooltip |
|--------|---------|
| Record Sample | Record a vocal sample from the microphone |
| Import Audio | Import an existing audio file for analysis |
| Duration Spin | Maximum recording duration in seconds |
| Analyze | Run DSP analysis on the recorded/imported audio |

### Apply & Review

| Widget | Tooltip |
|--------|---------|
| Preview Apply | Preview the mapped parameters on tokens before committing |
| Commit | Lock the previewed parameter changes into tokens |
| Revert | Undo the previewed changes and restore original values |
| Apply | Apply captured parameters directly to selected tokens |

### Preset Matching

| Widget | Tooltip |
|--------|---------|
| Use Preset | Use the selected matching preset instead of creating a new one |
| Create New | Create a new style preset from this analysis |
| Compare | Show per-feature comparison between analysis and selected preset |
| Auto-Create Preset | Automatically create a new preset when no close match is found |
| Save Preset | Save the current analysis as a named style preset |

### Session Controls

| Widget | Tooltip |
|--------|---------|
| Start Session | Begin a multi-sample capture session |
| End Session | Finish the current capture session |
| Accept | Accept the selected session preset |
| Rename | Rename the selected session preset |
| Save All | Save all presets from this session |

---

## Tracks Panel (`ui/tracks_panel.py`)

### Track Item Controls

| Widget | Tooltip |
|--------|---------|
| Mute Checkbox | Mute |
| Solo Checkbox | Solo |

### Track Management

| Widget | Tooltip |
|--------|---------|
| Add Track | Add Track |
| Rename Track | Rename Track |
| Delete Track | Delete Track |
| Assign to Track | Assign the currently selected tokens to this track |
| Export Stems | Export each track as a separate audio stem file |

### Playback Scope

| Widget | Tooltip |
|--------|---------|
| Current | Preview only the selected track |
| Master | Preview the full master mix of all tracks |

---

## Render Panel (`ui/render_panel.py`)

| Widget | Tooltip |
|--------|---------|
| Export Script | Export the performance script as a JSON file for external render engines |
| Add Master | Add Master render job |
| Add Track | Add job for selected track |
| Run Selected | Run selected job |
| Run All | Run all pending jobs |
| Cancel | Cancel selected job |
| Job List Item | Output: {job.output_path} (dynamic) |

---

## Import Panel (`ui/import_panel.py`)

| Widget | Tooltip |
|--------|---------|
| Import Audio | Load an audio file (WAV/MP3/M4A) for alignment |
| Lyrics Edit | Paste the song lyrics here for forced alignment with the imported audio |
| Transcribe | Placeholder for offline ASR |
| Align | Run forced alignment on audio + lyrics |
| Target Track | Select the target track for auto-filled tokens |
| Auto-Fill | Map alignment to tokens and fill parameters via DSP |

---

## Reference Panel (`ui/reference_panel.py`)

### Import & Analysis

| Widget | Tooltip |
|--------|---------|
| Import Reference | Import reference song (wav/mp3/m4a) |
| Import Stem | Import vocal stem (optional) |
| Mode Dropdown | Analysis mode: Master Mix, Vocal Stem only, or both |
| Tone Dropdown | Emotional tone to tag the extracted template with |
| Extract Template | Analyze the reference audio and create a performance template |

### Template Actions

| Widget | Tooltip |
|--------|---------|
| Apply | Apply selected template to new lyrics |
| Reapply | Reapply template to current selection |
| Switch Tone | Switch emotional tone without breaking family structure |
| Create from Template | Create new song from selected template |
| Create from Family | Create new song from selected family averages |
| Manage Families | Create, rename, delete, and assign templates to families |

---

## Instrument Editor Dialog (`ui/instrument_editor.py`)

### General

| Widget | Tooltip |
|--------|---------|
| Name | Instrument patch name |

### Envelope (ADSR)

| Widget | Tooltip |
|--------|---------|
| Attack | Time for sound to reach peak level |
| Decay | Time for sound to drop from peak to sustain level |
| Sustain | Held volume level while note is sustained (0-1) |
| Release | Time for sound to fade out after note ends |

### Timbre

| Widget | Tooltip |
|--------|---------|
| Damping | String/resonance damping factor (higher = more muted) |
| Harmonics | Overtone richness (0 = pure sine, 1 = full harmonic series) |
| Lowpass | Low-pass filter cutoff frequency in Hz |
| Brightness | Overall tonal brightness (0 = dark, 1 = bright) |

### Noise

| Widget | Tooltip |
|--------|---------|
| Noise | Amount of breath/noise mixed into the sound |
| Click | Transient click intensity at note onset |

### Token Defaults

| Widget | Tooltip |
|--------|---------|
| Duration Min | Minimum token duration for this instrument |
| Duration Max | Maximum token duration for this instrument |
| Default Intensity | Default intensity applied to tokens using this instrument |
| Delivery Mode | Default delivery mode for tokens using this instrument |
| Vibrato | Enable vibrato by default for this instrument |

### Actions

| Widget | Tooltip |
|--------|---------|
| Audition | Preview how this instrument sounds with current settings |

---

## World Navigator Dialog (`ui/world_navigator.py`)

| Widget | Tooltip |
|--------|---------|
| Search Box | Filter workspaces by name |
| Sphere Widget | Drag to rotate the globe; click a workspace dot to switch |

---

## Selection Popover (`ui/selection_popover.py`)

### Parameter Checkboxes

| Widget | Tooltip |
|--------|---------|
| Duration | Include duration in the apply operation |
| Loudness | Include loudness in the apply operation |
| Intensity | Include intensity in the apply operation |
| Pitch Offset | Include pitch offset in the apply operation |

### Delivery

| Widget | Tooltip |
|--------|---------|
| Apply Delivery | Include delivery mode in the apply operation |

### Options

| Widget | Tooltip |
|--------|---------|
| Auto-preview on release | Automatically preview audio when a slider is released |

---

*Generated from project source. 121 tooltip definitions across 12 UI files.*
