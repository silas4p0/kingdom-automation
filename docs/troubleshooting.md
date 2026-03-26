# Troubleshooting Guide

## Alignment Failures

### Symptoms
- "Run Alignment" produces no results or all tokens have identical timestamps.
- Console shows alignment completed but word timestamps look incorrect.

### Causes and Fixes

**No energy detected in audio**
- The audio file may be very quiet or contain mostly silence.
- Fix: Normalize the audio before importing. Ensure the WAV file has audible content.

**Lyrics do not match audio**
- The alignment engine distributes words across detected energy regions. If the lyrics have more words than the audio contains, words get crammed into available regions with low confidence.
- Fix: Make sure the lyrics match the actual words being sung. Remove any sections not present in the audio.

**Audio format issues**
- The engine reads PCM WAV files (16-bit or 8-bit, mono or stereo).
- Fix: Convert your audio to 16-bit PCM WAV at 44100 Hz before importing. Use `ffmpeg -i input.mp3 -ar 44100 -ac 1 -sample_fmt s16 output.wav`.

**Very short audio**
- Audio shorter than 1 second may not have enough energy variation for meaningful alignment.
- Fix: Use audio clips of at least 3-5 seconds for reliable alignment.

### Checking Alignment Quality

After running alignment, check the console for the word count and audio duration. If alignment.json shows all words with confidence below 0.5, the alignment is unreliable.

---

## Low Confidence Pitch Detection

### Symptoms
- DSP analysis shows pitch_hz = 0 or pitch_confidence below 0.3.
- Auto-filled pitch_offset values are all 0.

### Causes and Fixes

**Noisy recording**
- Background noise interferes with autocorrelation-based pitch detection.
- Fix: Record in a quiet environment. Use a close-mic technique.

**Non-pitched content**
- Percussive sounds, whispering, or speech without clear pitch will produce low confidence.
- Fix: This is expected for non-pitched content. Manually set pitch_offset for these tokens.

**Very short segments**
- Pitch detection requires at least 128 samples (~3ms at 44100 Hz). Very short word segments may not provide enough data.
- Fix: If a word is too short, try adjusting the alignment by editing lyrics or extending the audio.

**Second-best peak too close**
- When the autocorrelation second-best peak is within 90% of the best peak, confidence is penalized by 30%.
- This indicates ambiguous pitch (possibly octave error).
- Fix: Listen to the segment manually and set pitch_offset by ear if needed.

---

## Missing Audio Files

### Symptoms
- "Export Stems" produces empty files.
- "Export Training Pack" says "no vocal path found."
- Preview is silent even with tokens selected.

### Causes and Fixes

**No audio imported**
- Stem export and training pack export require audio to be loaded.
- Fix: Import an audio file first (Import Song > Import Audio), or record a sample in the Capture panel.

**File moved or deleted**
- If the original audio file was moved after import, the path stored in the project becomes invalid.
- Fix: Re-import the audio file from its new location. The project stores the path at import time.

**Project folder not created**
- Exports require a project folder. If you have not used Save As, there is no folder to export to.
- Fix: Click Save As first to create a project folder.

**Stem audio is empty**
- Tokens are not assigned to the track, so the track has nothing to render.
- Fix: Select tokens and click "Assign to Track" before exporting stems.

---

## Track Routing Confusion

### Symptoms
- Preview plays wrong tokens or no sound.
- Muted tracks still play.
- Solo mode does not isolate correctly.

### Causes and Fixes

**Mute/Solo logic**
- If any track has Solo enabled, only soloed tracks play.
- If no track is soloed, all enabled (non-muted) tracks play.
- Fix: Check that the correct tracks have their mute/solo checkboxes set as intended.

**Playback Track Scope**
- "Current" plays only the selected track's assigned tokens.
- "Master" plays all audible tracks.
- Fix: Make sure the Playback Track Scope toggle (bottom of Tracks panel) is set to your intended mode.

**Unassigned tokens**
- Tokens not assigned to any track play through Master but not through individual track preview.
- Fix: Assign all tokens to at least one track for consistent routing.

---

## Export Errors

### Symptoms
- Export buttons do nothing or console shows "no project folder."
- Exported files are missing or incomplete.

### Causes and Fixes

**No project folder**
- All exports write to subdirectories of the project folder.
- Fix: Use Save As to create a project folder first.

**Permission denied**
- The target directory may not be writable.
- Fix: Check file permissions on `~/Documents/KDS_Projects/`. Ensure the app has write access.

**Incomplete training pack**
- If no alignment data exists, alignment.json is skipped.
- If no reference template is selected, reference_template.json is skipped.
- Fix: This is normal. Only available data is exported. Import audio and run alignment first for a complete pack.

**Render job fails**
- Check the console for error messages. The render job status changes to "Failed" with an error string.
- Fix: Verify that tokens exist in the specified range and that the track has assigned tokens.

---

## Template Application Issues

### Symptoms
- "Apply" does nothing or tokens do not change.
- Template values seem wrong.
- Family structure breaks after editing.

### Causes and Fixes

**No template selected**
- The template dropdown may be empty or no template is highlighted.
- Fix: Extract a template first, or ensure the template store has templates. Check `~/.kds_lpe/reference_templates/templates/` for JSON files.

**No tokens selected**
- Apply works on the current selection. If no tokens are selected, nothing changes.
- Fix: Click on a token or select a range before clicking Apply.

**Emotional tone not switching**
- The "Switch" button requires tokens to be selected and a template to be assigned.
- Fix: Select tokens first, then click Switch and choose the new tone.

**Template extracted with wrong data**
- Templates capture the current state of alignment analysis. If alignment was poor, the template will reflect poor data.
- Fix: Re-extract the template after improving alignment or manually adjusting tokens.

---

## Autosave / Restore Issues

### Symptoms
- App does not restore previous session on launch.
- Autosave label does not update.
- Backups folder is empty.

### Causes and Fixes

**Autosave file missing**
- If `~/.kds_lpe/autosave.json` does not exist, no session is restored.
- Fix: This is normal on first launch. The first autosave creates the file after 60 seconds.

**Corrupted autosave**
- If the autosave JSON is malformed, restore silently fails.
- Fix: Delete `~/.kds_lpe/autosave.json` and restart. The app starts fresh.

**Backups not appearing**
- Backups are created on every save (manual or auto). If no saves have occurred, no backups exist.
- Fix: Perform a manual Save to trigger the first backup.

**Disk full**
- Autosave and backups fail silently if the disk is full.
- Fix: Free up disk space. The app auto-prunes to 50 backups, but logs and crash reports also consume space.

**Wrong project restored**
- Autosave always stores the last active project. If you had multiple projects open in different sessions, only the last one is restored.
- Fix: Use Load Project to open a specific project file.

---

## General Tips

1. **Check the console**: Most operations log messages to the Console panel. Read the latest entries for clues.
2. **Export a debug bundle**: Click Debug Bundle to collect logs, crash reports, and solution folders into a single zip for sharing.
3. **Use the fix registry**: If you solve a recurring issue, click "Save Fix" in the fix dialog to record the solution for future reference.
4. **Clear the preview cache**: If audio sounds stale, change a parameter slightly and change it back. This invalidates the cache entry.
5. **Restart the app**: If the UI becomes unresponsive, close and relaunch. Your session auto-restores from the last autosave.
