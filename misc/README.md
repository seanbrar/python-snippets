# Miscellaneous Utilities

[![MIT License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

Standalone scripts that don't fit into another category.

## Scripts

### transcript_elevenlabs.py
Transcribe video/audio files using the ElevenLabs API. Processes all supported media files in a directory.

**Dependencies:** `elevenlabs`, `python-dotenv` (optional)
**Requires:** `ELEVENLABS_API_KEY` environment variable (or `.env` file)

**Usage:**
```bash
python misc/transcript_elevenlabs.py /path/to/media/files
```

### ups_value.py
Evaluate how well a UPS unit matches a given load (watts, VA, runtime). Compares multiple UPS models and ranks them.

**Usage:**
```bash
python misc/ups_value.py
```

### ac_value_calcs.py
Calculate AC / SEER energy savings and return-on-investment based on local electricity costs and usage.

**Usage:**
```bash
python misc/ac_value_calcs.py
```

### base64_convert.py
Decode base64 and parse ASN.1 to extract r/s integer values (e.g. for ECDSA signatures).

**Usage:**
```bash
python misc/base64_convert.py
```

### elements_code.py
Extract metadata from Elements-style JSON exports.

**Usage:**
```bash
python misc/elements_code.py
```
