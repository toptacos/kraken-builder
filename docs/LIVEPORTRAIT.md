# LivePortrait and lip sync

LivePortrait (Kling / KwaiVGI, 2024) is **video-driven**. It copies motion from a driving video onto a source still. It does **not** read a waveform.

Lip sync is a second model that emits LivePortrait motion, then LivePortrait renders.

## What LivePortrait actually computes

Source image \(I_s\):

- appearance volume \(f_s = \mathcal{F}(I_s)\)
- canonical implicit keypoints \(x_{c,s} = \mathcal{M}(I_s)\)

Each driving frame \(I_{d,i}\):

- scale, expression deltas \(\delta\), translation \(t\), rotation \(R\)
- scalar conditions \(c_{d,\text{eyes}}\), \(c_{d,\text{lip}}\) (open/close ratios)

Warp \(f_s\) with the transformed keypoints, decode a frame. ~12.8 ms/frame on a 4090.

### Stitching

Small MLP predicts offset \(\Delta_{st}\) so the animated crop pastes back onto shoulders/neck without a seam.

### Eye / lip *retargeting* (not lip sync)

Cross-id problem: a driver with a small mouth cannot fully open a source with a large mouth.

MLP takes source ratio \(c_{s,\text{lip}}\) and target ratio \(c_{d,\text{lip}}\) and predicts \(\Delta_{\text{lip}}\). Same for eyes.

That is a **scalar**. “How open is the mouth.” It is not phonemes. Flags in Comfy / official CLI:

- `lip_retargeting` / multiplier
- `lip_zero` + threshold (kill micro jitter, then apply drive)
- `delta_multiplier` (1 = faithful, >1 exaggerates, 0 freezes)

Driving video rules from the official repo: 1:1 crop, head-only, little shoulder motion, **first frame frontal and neutral**.

## How people bolt on real lip sync

| Layer | Job | Reads audio? |
|---|---|---|
| LivePortrait renderer | warp + decode | no |
| Lip retarget MLP | open/close scalar | no |
| Wav2Lip / MuseTalk | paint the mouth on frames | yes |
| SadTalker ExpNet + PoseVAE | 3DMM exp + pose from audio | yes |
| LivePortraitTalker MappingNet | 3DMM → LivePortrait lip keypoints | yes (via 3DMM) |
| JoyVASA | wav2vec2 → diffusion motion in LivePortrait keypoint space | yes |
| KDTalker | audio → spatiotemporal diffusion of LivePortrait keypoints | yes |
| Whisper + flow-matching (LivePortrait-AudioDriven) | audio → keypoint sequence | yes |

### JoyVASA (best current pair)

1. Appearance encoder + motion encoder from LivePortrait on `now.jpg`.
2. wav2vec2 on the speech track.
3. Diffusion transformer samples identity-free motion in a sliding window.
4. Combine reference keypoints + sampled motion → driving keypoints.
5. LivePortrait warp/decode.

FasterLivePortrait wraps this as `run_audio_driving` → a `.pkl` motion stream → same renderer. Text path: Kokoro TTS → same JoyVASA.

Lip-only vs full-exp: maintainers noted a “strange nose” when only the lip region is animated; driving the full expression region looks more human.

### LivePortraitTalker (SadTalker mapping)

1. Audio → SadTalker 3DMM coefficients (ExpNet + PoseVAE).
2. MappingNet (trained on VoxCeleb2, L1) maps those coeffs to LivePortrait **lip-related canonical keypoints**.
3. LivePortrait renders.

Head pose can be synthetic (not predicted from audio) — author argument: pose is weakly correlated with the waveform, so sampling pose separately looks less mean-collapsed.

### Hybrid (Comfy / production)

Render a talking pass with Wav2Lip or MuseTalk, then use those frames as the **driving video** for LivePortrait so the rest of the face (blink, cheeks, micro-head) is LivePortrait-quality and the mouth is Wav2Lip-accurate. `lip_zero` on, retarget multiplier ~1.

## What Nyx should use

Identity plate: `website/img/nyx-real/now.jpg`  
Audio: `website/media/nyx-scratch.mp3`

On a CUDA box (8 GB+ for Wav2Lip, 12 GB+ for MuseTalk, 24 GB comfortable for JoyVASA+LP):

```
# FasterLivePortrait audio path
python run.py \
  --src_image website/img/nyx-real/now.jpg \
  --audio website/media/nyx-scratch.mp3 \
  --cfg configs/onnx_infer.yaml
```

Do not drive from the before-Kraken wrecked plates.

This sandbox has torch **without CUDA**. These weights will not run here.

## Failure modes

- Driving first frame not neutral → identity drift for the whole clip.
- Lip retarget multiplier > 1.2 → oval mouth.
- Audio-only pose from a weak mapper → bobblehead.
- Lip-region-only animation → nose/cheek swim (JoyVASA note).
- CPU LivePortrait → many minutes per second of video; not a product path.
