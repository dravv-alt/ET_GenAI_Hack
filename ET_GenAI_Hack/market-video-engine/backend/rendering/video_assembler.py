"""Assembles frame sequences into an MP4 with optional audio."""

from __future__ import annotations

import os
import tempfile

from moviepy import AudioFileClip, ImageSequenceClip


def assemble_video(
	frame_bytes_list: list[bytes],
	output_path: str,
	fps: int = 15,
	audio_path: str | None = None,
) -> str:
	"""Creates an MP4 from PNG frame bytes and optional audio."""
	if not frame_bytes_list:
		raise ValueError("No frames provided for video assembly")

	with tempfile.TemporaryDirectory() as tmpdir:
		frame_paths: list[str] = []
		for idx, frame_bytes in enumerate(frame_bytes_list):
			frame_path = os.path.join(tmpdir, f"frame_{idx:04d}.png")
			with open(frame_path, "wb") as frame_file:
				frame_file.write(frame_bytes)
			frame_paths.append(frame_path)

		clip = ImageSequenceClip(frame_paths, fps=fps)

		if audio_path and os.path.exists(audio_path):
			audio_clip = AudioFileClip(audio_path)
			duration = min(clip.duration, audio_clip.duration)
			clip = clip.subclipped(0, duration).with_audio(audio_clip.subclipped(0, duration))

		clip.write_videofile(
			output_path,
			fps=fps,
			codec="libx264",
			audio_codec="aac",
			logger=None,
		)

	return output_path
