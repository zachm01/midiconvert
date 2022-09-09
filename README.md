# midiconvert
A collection of midi conversions

# Current functions
The current functions are `midi_to_csv`, `csv_to_midi`, `midi_to_png`, and `png_to_midi`.
More functions will be added soon, including `midi_to_wav`, `wav_to_midi`, and a more diverse selection of file formats.

# How to use
Download this file into a project folder. Use `import midiconvert` or `from midiconvert import ...` to access functions

## Specific function usage
  #### midi_to_csv
  ```
  from midiconvert import midi_to_csv

  midi_to_csv(csv_path, midi_path_out)
  ```

  #### csv_to_midi
  ```
  from midiconvert import csv_to_midi

  csv_to_midi(csv_path, midi_path_out)
  ```
  
  #### midi_to_png
  ```
  from midiconvert import midi_to_png
  
  midi_to_png(midi_path, png_path_out)
  ```
  
  #### png_to_midi
  ```
  from midiconvert import png_to_midi
  
  png_to_midi(png_path, midi_path_out)
  ```
