# Kingdom Digital Systems - Lyric Performance Engine: User Manual

## Table of Contents

1. [Overview](#overview)
2. [Main Interface](#main-interface)
3. [Toolbar Reference](#toolbar-reference)
4. [Book & Chapter Navigation](#book--chapter-navigation)
5. [Composition Book](#composition-book)
6. [Performance Book](#performance-book)
7. [Tracks Book](#tracks-book)
8. [Reference Book](#reference-book)
9. [Import Book](#import-book)
10. [Rendering Book](#rendering-book)
11. [Wisdom & Knowledge Base Book](#wisdom--knowledge-base-book)
12. [World Navigator](#world-navigator)
13. [Instrument System](#instrument-system)
14. [Token Editing](#token-editing)
15. [Audio Preview System](#audio-preview-system)
16. [Performance Capture](#performance-capture)
17. [Style Presets](#style-presets)
18. [Reference Templates](#reference-templates)
19. [Project Management](#project-management)
20. [Logging & Debugging](#logging--debugging)
21. [Troubleshooting](#troubleshooting)
22. [Advanced Configuration](#advanced-configuration)

---

## Overview

The Lyric Performance Engine (LPE) is a cross-platform desktop application for composing, editing, and previewing vocal/instrument performances from text lyrics. It tokenizes lyrics into individually controllable words, each with parameters for duration, loudness, intensity, pitch, delivery style, and more.

The app runs entirely offline with no external dependencies beyond PySide6. All audio synthesis is done in real-time using lightweight DSP algorithms.

---

## Main Interface

The application window consists of:

- **Menu Bar** - Help menu with links to documentation
- **Toolbars** (3 rows) - All controls for project management, preview, voice selection, scope/mode, and instruments
- **Sidebar** - Book navigation (7 books) with keyboard shortcuts Ctrl/Cmd+1 through Ctrl/Cmd+7
- **Central Area** - Stacked pages, one per book, each with chapter tabs
- **Console Panel** - Scrollable log output at the bottom of most book pages

---

## Toolbar Reference

### Row 1: Main Toolbar

| Button | Behavior |
|--------|----------|
| **Save Project** | Saves to current project file (or prompts Save As if no file set) |
| **Save As...** | Opens file dialog; creates folder-based project if setting enabled |
| **Load Project** | Opens file dialog to load `.json` project |
| **Reveal Project** | Opens project folder in OS file manager (enabled after Save As) |
| **Toggle Theme** | Switches between dark and light theme |
| **Settings** | Opens settings dialog (folder-based projects toggle) |
| **Debug Bundle** | Exports a zip of logs, crash reports, and solution folders |
| **Export Training Pack** | Exports aligned audio + lyrics for voice training |
| **Render Mode** | Dropdown: A Convert, B Synthesize, C AI Assist (placeholder), D Live Convert (placeholder) |
| **Quality** | Fast or High (controls harmonic count and envelope precision) |
| **Play Preview** | Renders and plays preview for current token/scope/mode |
| **World** | Opens the World Navigator globe overlay |

### Row 2: Singer Toolbar

| Control | Behavior |
|---------|----------|
| **Singer** | Dropdown to select voice profile (Default Singer, Singer A/B/C) |
| **Personality** | Neutral, Warm, Edgy, Smooth (affects synthesis character) |
| **Mix** | Slider 0-100% blending personality with base voice |
| **Auto Preview** | Checkbox: auto-play preview when sliders are released |
| **Fix Pack Export** | Exports fix registry as shareable zip |
| **Fix Pack Import** | Imports fix pack zip from another machine |
| **Reveal Autosave** | Opens autosave folder in file manager |
| **Reveal Backups** | Opens backups folder in file manager |

### Row 3: Preview Scope & Instruments

| Control | Behavior |
|---------|----------|
| **Scope** | Word / From Word / Line / Section (Section requires range selection) |
| **Pre-Roll** | Slider 0-2000ms - silence before preview |
| **Post-Roll** | Slider 0-2000ms - silence after preview |
| **Snap to words** | Checkbox: snaps scope boundaries to word edges |
| **Mode** | Single / Forward / Assist (placeholder) |
| **Replay Last** | Replays the last rendered audio |
| **Instrument** | Dropdown: (None - use Voice Type), Default Vocal, Palm-Dusted Piano, or custom |
| **Edit...** | Opens Instrument Editor dialog for selected instrument |
| **Save As...** | Creates a new instrument from current editor state |
| **Duplicate** | Clones the selected instrument |
| **Delete** | Removes a user-created instrument (built-ins cannot be deleted) |

---

## Book & Chapter Navigation

The interface is organized into 7 Books, each accessed via the left sidebar or keyboard shortcuts:

| # | Book | Shortcut | Chapters |
|---|------|----------|----------|
| 1 | Composition | Ctrl+1 | Lyrics & Tokens, Inspector, Global Controls |
| 2 | Performance | Ctrl+2 | Capture Panel, Mode D (Live Convert placeholder) |
| 3 | Tracks | Ctrl+3 | Track Routing, Stem Export |
| 4 | Reference | Ctrl+4 | Reference Templates & Families |
| 5 | Import | Ctrl+5 | Audio Import & Alignment |
| 6 | Rendering | Ctrl+6 | Render Queue, Performance Script |
| 7 | Wisdom & KB | Ctrl+7 | Debug Bundle, Fix Registry, Solutions |

Click any book name in the sidebar or press the shortcut. The active book is highlighted. Book selection persists across sessions.

---

## Composition Book

### Lyrics & Tokens Chapter

**Lyrics Input** - Type or paste lyrics into the text area. Click **Tokenize** to split text into word tokens.

**Token List** - Each token is a clickable item. Click to select; Shift+Click for range selection; drag to select multiple.

**Token Behavior:**
- Selected token is highlighted in the list
- Inspector panel shows all parameters for the selected token
- Range selection enables Section scope and shows a popover

**Repeat Inheritance** - When a word appears multiple times and the first occurrence is locked, subsequent occurrences inherit its parameters.

### Inspector Chapter

Displays and edits parameters for the selected token:

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| Duration | 50-5000 ms | 500 ms | How long the word sounds |
| Loudness | 0-200% | 100% | Volume level |
| Intensity | 0-100 | 50 | Vocal energy/effort |
| Pitch Offset | -24 to +24 st | 0 | Semitone shift from base |
| Delivery | Whisper/Normal/Yell/Scream/Bravado | Normal | Vocal delivery style |
| Bravado Subtype | Confident/Aggressive/Triumphant/Defiant | Confident | Sub-style when Bravado selected |

**Buttons:**
- **OK** - Locks the token with current settings
- **Cancel** - Reverts changes
- **Prev/Next** - Navigate between tokens
- **Undo/Redo** - Full undo/redo stack

### Global Controls Chapter

| Control | Options |
|---------|---------|
| **Tempo** | 20-300 BPM |
| **Key** | C through B, Major/Minor |
| **Voice Type (Preview)** | Male, Female, Robot, Family Bathroom, Muted Percussive Piano |

Voice Type changes the formant set and base frequency used for synthesis. Selecting "Muted Percussive Piano" switches to a percussive piano synthesizer with no formants.

---

## Performance Book

### Capture Panel Chapter

**Recording:**
- **Record Sample** - Records from microphone (default max 10 seconds)
- **Stop Recording** - Stops and saves the recording
- **Import Audio File** - Loads a WAV file for analysis

**Analysis:**
- **Analyze** - Runs DSP analysis on captured/imported audio
- Displays: RMS loudness, peak amplitude, pitch (Hz), vibrato rate/depth, spectral centroid/rolloff, envelope duration
- Confidence indicators for pitch and vibrato

**Apply Targets:**
- **Single** - Apply to current token only
- **Range** - Apply to selected range
- **Forward** - Apply to current token and all after it

**Preview/Commit:**
- **Preview Apply** - Shows yellow highlight on affected tokens; does not commit
- **Commit** - Finalizes the parameter changes
- **Revert** - Undoes the preview

### Mode D Chapter

Placeholder for Live Convert (real-time singing conversion). Not yet implemented.

---

## Tracks Book

### Track Routing Chapter

Default tracks: Vocal 1, Vocal 2, Instruments, Master.

- Select a track from the list
- Select tokens in the Composition book
- Click **Assign to Track** to route those tokens
- Tracks can be enabled/disabled and soloed
- Color coding distinguishes tracks in the token list

### Stem Export Chapter

- **Export Stems** - Renders each track as a separate WAV file
- Output: `<project_folder>/stems/<track_name>.wav`

---

## Reference Book

### Reference Templates & Families Chapter

**Templates** capture the performance characteristics of a reference audio file (duration distribution, loudness envelope, pitch contour, vibrato behavior, delivery tendencies, intensity distribution).

**Families** group related templates together (e.g., "Worship Songs", "Ballads").

**Emotional Tones**: loving, compassionate, reverent, sorrowful, joyful, triumphant, warlike, prophetic (plus custom tones).

**Actions:**
- **Import Reference** - Load reference audio
- **Import Vocal Stem** - Load isolated vocal stem
- **Extract Template** - Analyze reference and create template
- **Apply Template** - Apply template parameters to all tokens
- **Reapply Template** - Re-apply with updated tone
- **Switch Tone** - Change emotional tone; adjusts intensity, loudness, delivery
- **Create from Template** - Generate new template variant
- **Manage Families** - Create/rename/delete families, assign templates

---

## Import Book

### Audio Import & Alignment Chapter

1. **Import Audio** - Load a song WAV file
2. **Run Alignment** - Energy-based forced alignment maps words to audio timestamps
3. **Auto-Fill Tokens** - Transfers alignment timing and DSP analysis to token parameters

The alignment engine uses energy envelope detection to find word boundaries. Results include per-word start/end times and confidence scores.

---

## Rendering Book

### Render Queue Chapter

- **Add Master Render** - Creates a render job for all tokens
- **Add Track Render** - Creates a render job for a specific track
- **Run Selected** / **Run All** - Execute render jobs
- **Cancel** - Cancel running job

Jobs show status: Pending, Running, Done, Failed, Cancelled.

Output: `<project_folder>/audio/renders/<job_label>.wav`

### Performance Script Chapter

- **Export Script** - Exports `performance_script.json` containing all token data, track assignments, voice profiles, tempo, key, and render settings.

---

## Wisdom & Knowledge Base Book

### Debug Bundle Chapter

- **Export Debug Bundle** - Creates a zip containing app logs, latest crash report, and latest solution folder
- Output: `exports/debug_bundle_<timestamp>.zip`

### Fix Registry Chapter

- **Fix Pack Export** - Exports all known fixes as a shareable zip
- **Fix Pack Import** - Imports fixes from another machine
- When an error occurs, its fingerprint (SHA-256 hash) is checked against the fix registry
- If a known fix exists, a popup shows the title, root cause, and fix steps

### Solutions Chapter

Each error creates a solution folder containing:
- `error_report.txt` - Stack trace + system info
- `repro_steps.md` - Template for reproduction steps
- `context.json` - Project state, selection, UI mode
- `notes.md` - Template for fix documentation
- `fingerprint.txt` - Error fingerprint for matching

---

## World Navigator

Click the **World** button (top-right of toolbar row 1) to open the World Navigator overlay.

**Features:**
- 2D sphere visualization rendered with QPainter
- Drag to rotate the sphere
- 5 workspace hotspots positioned on the globe: Audio, Video, Editor, Assets, Master
- Hotspots are labeled and fade when behind the sphere
- Search box at the top filters workspaces by keyword
- Click a hotspot or search result to switch to the corresponding Book

**Workspace-to-Book Mapping:**

| Workspace | Book |
|-----------|------|
| Audio | Performance (Book 2) |
| Video | Rendering (Book 6) |
| Editor | Composition (Book 1) |
| Assets | Reference (Book 4) |
| Master | Rendering (Book 6) |

---

## Instrument System

### Overview

Instruments are reusable synthesis parameter sets that override the default voice-type synthesis. When an instrument is selected, its parameters (ADSR envelope, timbre, noise, etc.) are applied to all preview audio.

### Instrument Parameters

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| attack_ms | float | 0.1-500 | Attack time |
| decay_ms | float | 1-2000 | Decay time |
| sustain_level | float | 0-1.0 | Sustain amplitude |
| release_ms | float | 1-2000 | Release time |
| damping | float | 0-1.0 | High-frequency damping |
| harmonics_level | float | 0-1.0 | Harmonic richness |
| lowpass_hz | float | 100-20000 | Lowpass filter cutoff |
| brightness | float | 0-1.0 | Spectral brightness |
| noise_amount | float | 0-1.0 | Noise mix level |
| transient_click | float | 0-1.0 | Initial click transient |
| default_duration_ms_min | int | 10-5000 | Min suggested duration |
| default_duration_ms_max | int | 10-5000 | Max suggested duration |
| default_intensity | int | 0-100 | Default intensity |
| default_delivery_mode | str | Normal/Whisper/etc. | Default delivery |
| default_vibrato_on | bool | true/false | Enable vibrato |

### Built-in Presets

**Default Vocal**: Long attack (25ms), high sustain (0.8), rich harmonics (0.85), bright (0.6), wide lowpass (8000Hz), vibrato ON.

**Palm-Dusted Piano**: Fast attack (3ms), rapid decay (55ms), low sustain (0.04), high damping (0.85), sparse harmonics (0.2), narrow lowpass (1600Hz), transient click (0.35), vibrato OFF.

### Storage

- **Built-in** presets are always available and cannot be deleted
- **Global** instruments: `~/.kds_lpe/instruments/*.json`
- **Project** instruments: `<project_folder>/instruments/*.json`
- Project instruments override global instruments with the same name

### Instrument Editor

Click **Edit...** to open the editor dialog. Sections:

1. **Envelope (ADSR)** - Attack, Decay, Sustain Level, Release sliders
2. **Timbre / Damping** - Damping, Harmonics Level, Lowpass Hz, Brightness
3. **Noise / Transient** - Noise Amount, Transient Click
4. **Token Defaults** - Duration range, Intensity, Delivery Mode, Vibrato toggle

Click **Audition** to preview the current settings without committing. Click OK to apply.

### Synthesis Priority

When a token is rendered:
1. If an **InstrumentPatch** is selected -> uses `_synthesize_instrument()`
2. Else if Voice Type is **Muted Percussive Piano** -> uses `_synthesize_muted_piano()`
3. Else -> uses `_synthesize_vocal()` with formant filtering

---

## Token Editing

### Single Token Editing

1. Tokenize lyrics in the Composition book
2. Click a token in the list
3. Adjust parameters in the Inspector panel (sliders and dropdowns)
4. Click **OK** to lock the token
5. Preview plays automatically if Auto Preview is enabled

### Range Selection

1. Click-drag across multiple tokens, or Shift+Click
2. A popover appears near the selection with:
   - Scope/Mode buttons
   - Apply (lock all in range) and Cancel buttons
3. Section scope is enabled when a range is selected

### Delivery Modes

| Mode | Amplitude | Noise Mix | Harmonics | Description |
|------|-----------|-----------|-----------|-------------|
| Whisper | 0.25 | 0.55 | 6 | Breathy, quiet |
| Normal | 0.50 | 0.03 | 12 | Standard singing voice |
| Yell | 0.80 | 0.08 | 16 | Loud, forceful |
| Scream | 0.95 | 0.18 | 20 | Maximum intensity |
| Bravado | 0.75 | 0.05 | 14 | Bold, confident |

### Boundary Markers

- **Normal** - Standard word boundary
- **Hard Stop** - Abrupt cutoff after word
- **Powerful Start** - Emphasized attack on word

---

## Audio Preview System

### Preview Scopes

| Scope | Behavior |
|-------|----------|
| **Word** | Plays only the selected token |
| **From Word** | Plays from selected token to end of line |
| **Line** | Plays all tokens on the same line |
| **Section** | Plays the selected range of tokens |

### Preview Modes

| Mode | Behavior |
|------|----------|
| **Single** | Plays scope once and stops |
| **Forward** | Plays scope, then triggers preview render automatically |
| **Assist** | Placeholder for AI-assisted preview |

### Pre-Roll / Post-Roll

- Pre-Roll adds silence/context tokens before the scope
- Post-Roll adds silence/context tokens after the scope
- Adjustable 0-2000ms via sliders

### Voice Types

| Type | Base Freq | Character |
|------|-----------|-----------|
| Male | 120 Hz | Low formants, natural vibrato |
| Female | 220 Hz | High formants, natural vibrato |
| Robot | 150 Hz | Narrow bandwidth formants, square wave component, minimal vibrato |
| Family Bathroom | 155 Hz | Wide bandwidth formants (reverb-like diffusion) |
| Muted Percussive Piano | 261 Hz (C4) | No formants, fast ADSR, string damping filter |

---

## Performance Capture

### Workflow

1. Go to Performance > Capture Panel
2. Record a vocal sample or import an audio file
3. Click Analyze to extract DSP features
4. Review confidence indicators
5. Choose apply target (Single/Range/Forward)
6. Preview Apply to see highlighted changes
7. Commit or Revert

### DSP Features Extracted

- RMS loudness, peak amplitude
- Pitch (Hz) with autocorrelation + confidence
- Vibrato rate/depth with confidence
- Spectral centroid and rolloff
- Envelope duration

### Closest Preset Matching

After analysis, the system computes a 9-dimensional feature vector and compares against all stored presets using confidence-weighted Euclidean distance. Top 3 matches are shown with similarity scores. Options: Use Existing, Create New, Compare Details.

---

## Style Presets

Style presets capture analyzed performance parameters for reuse.

**Storage**: `~/.kds_lpe/style_presets/*.json`

**Fields**: loudness_pct, intensity, pitch_offset, duration_ms, delivery, analysis_features, feature_vector

**Feature Vector** (9 dimensions): rms_norm, peak_norm, pitch_median_st, vibrato_rate, vibrato_depth, centroid_norm, rolloff_norm, env_duration_norm, delivery_id

---

## Reference Templates

Templates capture macro-level performance characteristics from reference audio.

**Fields**: duration distribution (mean/std/min/max), loudness envelope (mean RMS, peak RMS, dynamic range), pitch contour (median Hz, mean/std/range in semitones), vibrato behavior (rate, depth, presence ratio), delivery tendencies (per-mode weights), intensity distribution.

**Families** group templates. Family summaries aggregate tempo range, intensity, delivery tendencies, and emotional tone distribution across all member templates.

**Emotional Tones**: When switching tone, the system adjusts intensity, loudness, and delivery weights based on the tone's character.

---

## Project Management

### Auto-Save

- Saves to `~/.kds_lpe/autosave.json` every 60 seconds
- Restored automatically on next launch
- Timestamp shown in toolbar ("Saved 12:14:33")

### Timestamped Backups

- Created alongside each auto-save
- Stored in `~/.kds_lpe/backups/`
- Pruned to keep latest 50 backups

### Folder-Based Projects

When enabled (default), Save As creates a project directory:

```
MyProject/
  project.json
  audio/
    captures/
    renders/
    imports/
    reference/
  presets/
  exports/
  stems/
  instruments/     (project-level instruments)
```

### Settings

- **Use Folder-Based Projects** toggle (default ON)
- Accessed via Settings button in toolbar

---

## Logging & Debugging

### Log Files

- `logs/app.log` - Rotating log file (2MB max, 5 backups)
- Console output mirrors INFO-level messages
- All operations logged with timestamps

### Crash Reports

- Auto-generated on unhandled exceptions
- Saved to `logs/crashes/crash_<timestamp>.txt`
- Include: system info, stack trace, app state, error fingerprint

### Solution Folders

- Created for each error in `solutions_and_learning/`
- Contains: error_report.txt, repro_steps.md, context.json, notes.md, fingerprint.txt

### Fix Registry

- `solutions_and_learning/fix_registry.json`
- SHA-256 fingerprints map errors to known fixes
- Portable via Fix Pack Export/Import

### Debug Bundle

- Single zip containing logs, latest crash, latest solution folder
- Export via toolbar button or Wisdom & KB book

---

## Troubleshooting

### No Sound on Preview

1. Check that tokens exist (Tokenize first)
2. Check that a token is selected
3. Check system audio output device
4. Check Quality setting (try switching between Fast/High)
5. Check Voice Type is not set to an unsupported option

### Preview Sounds the Same After Changing Instrument

- The preview cache may need invalidation. Switch away from and back to the instrument, or click Play Preview again.

### Tokens Not Appearing

- Ensure lyrics text is not empty
- Click the Tokenize button
- Check console for error messages

### Import Alignment Fails

- Ensure the audio file is a valid WAV (16-bit PCM)
- Ensure lyrics are tokenized before running alignment
- Check that word count roughly matches audio content

### Project Won't Save

- Check disk space
- Check write permissions on the target directory
- Try Save As to a different location

### Application Crashes

1. Check `logs/app.log` for error details
2. Look in `logs/crashes/` for crash report
3. Export Debug Bundle and review
4. Check if fix exists in Fix Registry

### Fix Pack Not Importing

- Ensure the zip contains `fix_registry.json` at the root level
- File must be a valid ZIP archive

---

## Advanced Configuration

### Global Configuration Directories

| Path | Purpose |
|------|---------|
| `~/.kds_lpe/autosave.json` | Auto-save state |
| `~/.kds_lpe/backups/` | Timestamped backups |
| `~/.kds_lpe/style_presets/` | Style presets |
| `~/.kds_lpe/instruments/` | Global instruments |
| `~/.kds_lpe/reference_templates/` | Templates and families |

### Preview Quality Modes

**Fast**: Reduced harmonic count (max 6-8), shorter attack/release envelopes, suitable for real-time editing.

**High**: Full harmonic count (12-20), longer envelopes, more accurate formant rendering, suitable for final preview.

### Voice Type Customization

Voice types are defined in `engines/audio_synth.py`:
- `FORMANTS` dict maps voice type -> vowel -> list of (freq_hz, bandwidth_hz, amplitude) tuples
- `VOICE_TYPE_BASE_FREQ` maps voice type -> fundamental frequency
- `DELIVERY_PARAMS` maps delivery mode -> amplitude, noise_mix, harmonic_count, harmonic_decay

### Singer Frequency Offsets

Each singer profile has a frequency offset applied to the base voice type frequency:
- default: +0 Hz
- singer_a: -15 Hz
- singer_b: +30 Hz
- singer_c: -30 Hz

### Instrument JSON Format

```json
{
  "format_version": 1,
  "name": "My Instrument",
  "created_at": 1700000000.0,
  "attack_ms": 10.0,
  "decay_ms": 100.0,
  "sustain_level": 0.5,
  "release_ms": 80.0,
  "damping": 0.3,
  "harmonics_level": 0.6,
  "lowpass_hz": 5000.0,
  "brightness": 0.5,
  "noise_amount": 0.02,
  "transient_click": 0.1,
  "default_duration_ms_min": 200,
  "default_duration_ms_max": 600,
  "default_intensity": 50,
  "default_delivery_mode": "Normal",
  "default_vibrato_on": true
}
```

### Project JSON Format

Projects are saved as JSON with the following top-level keys:
- `lyrics` - Raw lyrics text
- `tokens` - Array of token objects with all parameters
- `render_mode`, `engine_quality`, `auto_preview`
- `singer`, `personality`, `personality_mix`
- `tempo`, `key`, `theme`
- `preview_mode`
- `project_folder`, `folder_based`
- `active_book`
- `tracks` - Array of track definitions
- `track_assignments` - Array of token-to-track mappings

### Extending Voice Types

To add a new voice type:
1. Add formant data to `FORMANTS` dict in `engines/audio_synth.py`
2. Add base frequency to `VOICE_TYPE_BASE_FREQ`
3. Add the name to `VOICE_TYPES` list
4. Add to the dropdown in `ui/global_controls_panel.py`

### Extending Emotional Tones

Custom emotional tones can be added via the Reference Templates UI. They are stored in `~/.kds_lpe/reference_templates/custom_tones.json`.
