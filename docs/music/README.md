# QAF Music Lab v0.1 - GoToGym
Author / proposed integration: Juan Manuel Goenaga Castro. 22 October 2026.

## Observed weakness
The earlier `qaf_video.audio.procedural_score` creates a slow ambient chord bed without a drum kit or a separately editable bass. The user found the music insufficiently current/cool. One comment diagnoses a product need; it does not establish a population trend. This extension supplies an executable research workflow, **not a trained neural music generator or a certified hit-making system**.

## Five linked papers and implemented contracts
| Paper | Question | Python module |
|---|---|---|
| M01 | Which dated reference features fit the audience and brand? | preference.py |
| M02 | How to compose differentiated original editable sketches? | synthesis.py |
| M03 | How to align musical section cues without shifting narration? | arrangement.py |
| M04 | How to retain groove while protecting speech? | mixing.py + existing audio.py |
| M05 | How to test preference, record rights and reject unsupported claims? | evaluation.py |

PDFs: `papers/`. Editable LaTeX: `source/`. Build: `python docs/music/build_papers.py` (XeLaTeX required). The full neural/flow formulation in M02 is a **future research proposal**, not silently implemented by the DSP sketch renderer.

## Install and execute
Python 3.11+, NumPy and FFmpeg; install the existing repository with `python -m pip install .`.

```bash
mkdir -p outputs
python -m qaf_video.music_research select examples/music/running_brief.json
python -m qaf_video.music_research align --bpm 124 --cues 13 29 50 > outputs/music-plan.json
python -m qaf_video.music_research sketch --preset run_club --out outputs/run-club --plan outputs/music-plan.json
python -m qaf_video.music_research sketch --preset coastal_pulse --out outputs/coastal
python -m qaf_video.music_research sketch --preset future_stride --out outputs/future
python -m qaf_video.music_research mix --voice /private/running-voice.wav --music outputs/run-club/preview.wav --out outputs/running-mix.wav --bpm 124
python -m qaf_video.music_research evaluate /private/paired-ratings.json
python -m unittest discover -s tests -p test_music_research.py -v
```
Create `outputs/` before redirecting JSON. `sketch` returns four isolated 16-bit stereo stems plus a preview and SHA-256 manifest; defaults to 60 seconds / 48 kHz. Match `--seconds` and preset BPM when providing a plan. The three style names are **creative directions**, not evidence of 2026 popularity or regional authenticity. Brief feature numbers are explicitly illustrative and cannot promote a commercial release.

## Existing production integration
`mix` calls the existing `mix_audio` implementation, using sidechain compression and two-pass loudness with beat-relative release. It records final measured LUFS / true peak and pending human approval. Output WAV may replace the episode's music mix only after an audition and technical checks. This change does **not** automatically replace the accepted Running MP4 or change picture/voice timing. The cinematic project may point to a newly auditioned music WAV through its existing music asset field; preserve its source and checksum and invalidate audio/editorial approval after any change.

M01's `feasible` flag is an editorial input, not a rights validator. Before commercial synchronization, separately run `rights` against the exact chosen asset and complete an editorial listening review. The rights checker verifies declared permissions, dates and hash; it cannot authenticate a contract. Never commit private contracts or voices.

## Evaluation protocol
Compare the old ambient bed, a curated licensed professional track and the new candidate with matched narration and final loudness; hide method labels and randomize order. Measure modernity, desire to keep watching, brand fit and word transcription separately. Multiple episodes per listener; pilot first, preregister sample size from observed variance. The implemented listener bootstrap is conditional on tested episodes and cannot claim generalization across campaigns. No human ratings or conversion results have been collected in this release.

## IP and scientific limits
The QAF source framework and CSRA / MPS-TDVP-RDM manuscripts supplied by Juan Manuel were consulted. CSRA explicitly admits a classical control with the same contextual statistics; those benchmark numbers are **not musical results**. Current decision state is rho=diag(p), fixed alternatives, no identifiable off-diagonal phase. Classical enumeration/DP receive identical relations. QAF-positive, classical-positive, non-identifiable and computational-breakdown regions must be established on real music experiments, not assigned by brand name.

Keep credit to Antoni Bancells for the prior technical MPS/TDVP/QUBO manuscript as already documented in this repository; do not transfer third-party authorship to GoToGym. The implementation adds orchestration, objective design, original DSP patterns and traceability. It makes no patentability, exclusivity or legal ownership determination. NumPy, FFmpeg, established synthesis, music theory and algorithms retain their third-party origins. Copyright-sensitive raw references, performer consent and contracts belong in private storage.

MusicGen is a research reference, not an activated commercial backend: its published weight license is noncommercial. Do not equate code license with weight or synchronized-output rights. Future neural training requires authorized multitrack audio, composition/master/synchronization rights, exact model license, producer curation, GPU training and independent listening tests. No downloaded music, samples, credentials or weights are bundled.

## Sources (checked 22 October 2026)
- Goenaga Castro, QAF (2025); CSRA and Motor completo MPS/TDVP/RDM (2026), supplied manuscripts. Source inventory/hashes in `validation.json`; originals not redistributed.
- Copet et al., *Simple and Controllable Music Generation*, NeurIPS 2023: https://arxiv.org/abs/2306.05284
- Meta, weight license: https://github.com/facebookresearch/audiocraft/blob/main/LICENSE_weights
- ITU-R BS.1770-5: https://www.itu.int/rec/R-REC-BS.1770-5-202311-I/
- ITU-R BS.1534-3: https://www.itu.int/rec/R-REC-BS.1534
- FFmpeg filters: https://ffmpeg.org/ffmpeg-filters.html

## Entrega verificada

100 pruebas de la suite completa y 12 de música aprobadas localmente; cinco PDF de cuatro páginas revisados tras render. `test-results.txt` contiene la ejecución específica y `validation.json` las medidas de demos y hashes de fuentes consultadas. Las tres muestras MP3 de 60 segundos están en el paquete descargable; se regeneran desde el código. No hay estudio humano realizado.
