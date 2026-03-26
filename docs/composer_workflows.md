# Composer Workflow Guide

## Building a Multi-Song Set (e.g., Psalms Continuity Workflow)

A multi-song set shares musical DNA across songs while allowing individual expression. Use template families and emotional tones to maintain cohesion.

### Setup

1. Create a master project folder structure:
   ```
   ~/Documents/KDS_Projects/
     Psalms_Collection/
       Psalm_23/
       Psalm_91/
       Psalm_150/
   ```

2. Start with the first song. Import a reference recording, align lyrics, and extract a template.

3. Create a template family:
   - Open Reference Template panel > Manage Families
   - Create family: "Psalms Collection"
   - Add a description: "Worship psalms series - reverent base tone"

4. Assign the first template to the family.

### Adding Songs to the Set

For each new psalm:

1. Create a new project with Save As (e.g., "Psalm_91").
2. Use "Create From Family" > select "Psalms Collection".
   - This initializes tokens with the family's shared characteristics (average tempo, intensity distribution, delivery tendencies).
3. Customize per-song:
   - Adjust emotional tone (e.g., Psalm 23 = "loving", Psalm 91 = "triumphant", Psalm 150 = "joyful").
   - Fine-tune individual tokens.
4. Extract a template from the finished song and add it to the family.
   - The family summary updates automatically with each new template.

### Maintaining Continuity

- Check family summary periodically (Manage Families > select family).
- The summary shows tempo range, intensity distribution, delivery tendencies, and emotional tone distribution across all songs.
- If a new song drifts too far from the family baseline, use Reapply to bring tokens closer to the family average.

---

## Using Reference Templates for Stylistic Cohesion

Reference templates capture the "feel" of a performance: timing patterns, loudness contours, pitch tendencies, vibrato characteristics, and delivery style distribution.

### Extract a Template from a Reference Song

1. Import the reference audio (Import Song panel > Import Audio).
2. Paste the lyrics and click Tokenize.
3. Run alignment to match words to audio.
4. Click Auto-Fill Tokens to populate parameters from the audio analysis.
5. Click "Extract Template" in the Reference Template panel.
6. Name the template (e.g., "Gospel Ballad Style") and select an emotional tone.

### Apply to a New Song

1. Open or create your new project.
2. Enter and tokenize lyrics.
3. Select all tokens (Shift+Click from first to last).
4. Choose the reference template from the dropdown.
5. Click "Apply" to set all token defaults from the template.
6. Preview and fine-tune individual words as needed.

### Template Layering

For complex arrangements:

1. Extract separate templates from different reference songs.
2. Apply Template A to verse tokens.
3. Apply Template B to chorus tokens.
4. This creates dynamic contrast while maintaining individual section cohesion.

---

## Switching Emotional Tone While Maintaining Family Structure

Emotional tones are variations within a family. Each tone applies specific modifiers:

| Tone | Intensity Modifier | Loudness Modifier | Delivery Tendency |
|------|-------------------|-------------------|-------------------|
| loving | -10 | +5% | Leans Normal/Whisper |
| compassionate | -5 | +0% | Leans Normal |
| reverent | -15 | -5% | Leans Whisper/Normal |
| sorrowful | -20 | -10% | Leans Whisper |
| joyful | +10 | +10% | Leans Normal/Yell |
| triumphant | +20 | +15% | Leans Yell/Bravado |
| warlike | +25 | +20% | Leans Scream/Bravado |
| prophetic | +15 | +5% | Leans Bravado |

### Switching Tone

1. Select a range of tokens.
2. Click "Switch" in the Reference Template panel.
3. Choose the new emotional tone.
4. The system adjusts intensity, loudness, and delivery based on the tone modifiers.
5. The family assignment remains unchanged.

### Mid-Song Tone Shifts

For songs that transition emotionally:

1. Select verse 1 tokens > Switch to "sorrowful".
2. Select chorus tokens > Switch to "triumphant".
3. Select bridge tokens > Switch to "prophetic".
4. Preview each section to verify the emotional arc.

---

## Creating Alternate Singer Versions (Male/Female/Choir)

### Single Singer Variants

1. Complete your base song project (e.g., "HolyHoly_Female").
2. Save As "HolyHoly_Male".
3. Change Voice Type (Preview) to "Male".
4. Adjust pitch offsets:
   - Male voices typically sit -12 to -7 semitones lower than female.
   - Select all tokens, use range edit to shift pitch offset.
5. Adjust delivery:
   - Male versions may need slightly longer durations for lower register.
6. Export stems for the male version.

### Choir Arrangement

1. Start with a lead vocal project.
2. Add tracks: "Soprano", "Alto", "Tenor", "Bass".
3. For each section:
   - Assign all tokens to each track.
   - For Soprano/Alto: use Female voice type, adjust pitch offsets (+3 to +7 for soprano, -2 to +2 for alto).
   - For Tenor/Bass: use Male voice type, adjust pitch offsets (0 to +3 for tenor, -7 to -3 for bass).
4. Use mute/solo to preview individual parts.
5. Export stems for each vocal part.
6. The Master track plays all parts together.

### Quick Duplication Method

1. Export performance script from the lead vocal.
2. Create a new project for each voice part.
3. Load the same lyrics and tokenize.
4. Apply a template extracted from the lead vocal.
5. Adjust voice type and pitch offsets for the target part.

---

## Creating Historical vs Modern Instrument Variants

Use the Instrument track layer to separate arrangements:

### Historical Arrangement

1. Create an Instrument track named "Lyre" (placeholder).
2. Create another named "Harp" (placeholder).
3. Set global controls: Tempo 60 BPM, Key appropriate for the psalm.
4. Assign relevant token ranges to each instrument track.
5. Export stems -- each instrument track renders separately.

### Modern Arrangement

1. Save As a new project (e.g., "Psalm23_Modern").
2. Rename/add Instrument tracks: "Piano", "Guitar", "Strings".
3. Adjust tempo and key for modern feel.
4. Re-assign tokens to modern instrument tracks.
5. Export stems.

### Comparison Workflow

Keep both projects in the same family. Use the family summary to see how tempo and intensity distributions differ between historical and modern arrangements.

---

## Preparing Data for AI Voice Training

The Export Training Pack feature creates clean datasets for future voice/singing model training.

### Best Practices for Training Data

1. **Use clean vocal stems**: Import isolated vocal recordings rather than full mixes.
   - Import Stem is preferred over Import Audio for cleaner training data.

2. **Align carefully**: Run alignment and verify word timestamps visually.
   - Check alignment.json for accurate start/end times.
   - Words with low confidence scores may need manual adjustment.

3. **Choose segmentation wisely**:
   - "By line" (8 words per segment): Good for sentence-level training.
   - "By phrase" (300ms gap threshold): Good for natural breath-group training.
   - "None": Exports the full vocal file without segmentation.

4. **Include metadata**:
   - Performer name: identifies the voice in the training set.
   - Notes: describe recording conditions, microphone type, vocal style.

5. **Export multiple takes**: Record the same song multiple times with slight variations to increase training data diversity.

6. **Build a corpus**:
   ```
   ~/Documents/KDS_Projects/
     TrainingCorpus/
       Song01/exports/training_pack/
       Song02/exports/training_pack/
       Song03/exports/training_pack/
   ```

### Training Pack Contents

| File | Purpose |
|------|---------|
| `vocals.wav` | Full vocal audio |
| `segments/*.wav` | Per-line or per-phrase audio clips |
| `alignment.json` | Word-level timestamps with confidence scores |
| `performance_script.json` | Complete token parameters and track data |
| `reference_template.json` | Style/performance template data |
| `metadata.json` | Sample rate, performer, notes, duration |
| `manifest.json` | Complete file listing |

---

## Recommended Folder/Project Organization

### Single Song Project

```
~/Documents/KDS_Projects/
  MySong/
    project.json           # Main project file
    audio/
      captures/            # Mic recordings
      renders/             # Render queue output
      imports/             # Imported reference audio
      reference/           # Reference audio tracks
    presets/                # Style presets
    exports/               # Performance scripts, training packs
    stems/                 # Per-track WAV exports
```

### Multi-Song Collection

```
~/Documents/KDS_Projects/
  PsalmsCollection/
    Psalm_023_Shepherd/
      project.json
      audio/...
      exports/...
      stems/...
    Psalm_091_Refuge/
      project.json
      audio/...
    Psalm_150_Praise/
      project.json
      audio/...
```

### Training Corpus

```
~/Documents/KDS_Projects/
  VoiceTraining_SingerA/
    Song01/
      exports/training_pack/
    Song02/
      exports/training_pack/
    Song03/
      exports/training_pack/
```

### Template and Preset Locations

These are stored globally (shared across all projects):

| Store | Location |
|-------|----------|
| Reference templates | `~/.kds_lpe/reference_templates/templates/` |
| Template families | `~/.kds_lpe/reference_templates/families/` |
| Custom tones | `~/.kds_lpe/reference_templates/custom_tones.json` |
| Style presets | `~/.kds_lpe/style_presets/` |
| Auto-save | `~/.kds_lpe/autosave.json` |
| Backups | `~/.kds_lpe/backups/` |
