# Kingdom Digital Systems - Lyric Performance Engine: Quick Start Guide

## Prerequisites

- Python 3.10 or later
- PySide6 installed (`pip install PySide6`)

## Launch the Application

```bash
cd lyric-performance-engine
python main.py
```

The main window opens with the Composition book active.

---

## Step 1: Enter Lyrics

1. You start in **Composition > Lyrics & Tokens**
2. Type or paste lyrics into the text area (one line per phrase)
3. Click **Tokenize**

Each word becomes a token in the list below. Tokens are the building blocks of your performance.

---

## Step 2: Select and Edit a Token

1. Click any token in the list to select it
2. The **Inspector** panel (Composition > Inspector tab) shows its parameters:
   - **Duration** (ms) - how long the word sounds
   - **Loudness** (%) - volume
   - **Intensity** (0-100) - vocal energy
   - **Pitch Offset** (semitones) - raise or lower pitch
   - **Delivery** - Whisper, Normal, Yell, Scream, or Bravado
3. Adjust sliders and dropdowns
4. Click **OK** to lock the token

---

## Step 3: Preview Your Performance

1. Select a token
2. Choose a **Voice Type** in Global Controls: Male, Female, Robot, Family Bathroom, or Muted Percussive Piano
3. Click **Play Preview** in the toolbar (or press the button)
4. Audio plays through your speakers

**Preview Scope** controls what gets played:
- **Word** - just the selected token
- **From Word** - selected token through end of line
- **Line** - entire line
- **Section** - a selected range (Shift+Click to select multiple tokens)

**Preview Mode** controls behavior:
- **Single** - plays once
- **Forward** - plays and auto-triggers next render

---

## Step 4: Use an Instrument

1. In the toolbar, find the **Instrument** dropdown
2. Select "Default Vocal" or "Palm-Dusted Piano"
3. Click **Play Preview** to hear the difference
4. Click **Edit...** to open the Instrument Editor and tweak parameters
5. Click **Save As...** to save a custom instrument

---

## Step 5: Save Your Project

1. Click **Save As...** in the toolbar
2. Choose a location and name
3. A project folder is created with subdirectories for audio, presets, stems, and exports
4. Auto-save runs every 60 seconds to `~/.kds_lpe/autosave.json`

To reopen: click **Load Project** and select the `project.json` file.

---

## Step 6: Export

**Render audio:**
1. Go to **Rendering** book (Ctrl+6)
2. Click **Add Master Render**
3. Click **Run All**
4. Output WAV appears in `<project>/audio/renders/`

**Export performance script:**
1. In the Rendering book, click **Export Script**
2. A JSON file with all token data and settings is saved

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+1 through Ctrl+7 | Switch between Books |
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |
| Escape | Clear token selection |

---

## Next Steps

- Read the [User Manual](USER_MANUAL.md) for full feature reference
- Read the [Architecture Guide](ARCHITECTURE.md) for technical details
- Explore the **World Navigator** (globe button) to quickly switch workspaces
- Try **Performance Capture** to record your voice and auto-map parameters
- Build **Reference Templates** from existing songs to guide your performance style
