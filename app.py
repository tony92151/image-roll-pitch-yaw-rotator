import math
import tempfile
from datetime import datetime
from pathlib import Path

import cv2
import gradio as gr
import numpy as np


PREVIEW_MAX_SIDE = 960


def _rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """Return combined 3D rotation matrix using Z(roll), X(pitch), Y(yaw)."""
    r = math.radians(roll)
    p = math.radians(pitch)
    y = math.radians(yaw)

    rz = np.array(
        [
            [math.cos(r), -math.sin(r), 0],
            [math.sin(r), math.cos(r), 0],
            [0, 0, 1],
        ],
        dtype=np.float32,
    )

    rx = np.array(
        [
            [1, 0, 0],
            [0, math.cos(p), -math.sin(p)],
            [0, math.sin(p), math.cos(p)],
        ],
        dtype=np.float32,
    )

    ry = np.array(
        [
            [math.cos(y), 0, math.sin(y)],
            [0, 1, 0],
            [-math.sin(y), 0, math.cos(y)],
        ],
        dtype=np.float32,
    )

    return rz @ rx @ ry


def _perspective_matrix(width: int, height: int, roll: float, pitch: float, yaw: float) -> np.ndarray:
    f = max(width, height)

    corners_3d = np.array(
        [
            [-width / 2, -height / 2, 0],
            [width / 2, -height / 2, 0],
            [width / 2, height / 2, 0],
            [-width / 2, height / 2, 0],
        ],
        dtype=np.float32,
    )

    rot = _rotation_matrix(roll, pitch, yaw)
    rotated = corners_3d @ rot.T

    z_shift = 1.5 * f
    zs = rotated[:, 2] + z_shift

    projected = np.column_stack(
        [
            f * (rotated[:, 0] / zs) + width / 2,
            f * (rotated[:, 1] / zs) + height / 2,
        ]
    ).astype(np.float32)

    src = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )

    return cv2.getPerspectiveTransform(src, projected)


def _transform_image(image: np.ndarray, roll: float, pitch: float, yaw: float) -> np.ndarray:
    h, w = image.shape[:2]
    matrix = _perspective_matrix(w, h, roll, pitch, yaw)
    return cv2.warpPerspective(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def _downscale_for_preview(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    max_side = max(h, w)
    if max_side <= PREVIEW_MAX_SIDE:
        return image

    scale = PREVIEW_MAX_SIDE / max_side
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def preview_transform(image: np.ndarray, roll: float, pitch: float, yaw: float):
    if image is None:
        return None, None

    preview_image = _downscale_for_preview(image)
    transformed_preview = _transform_image(preview_image, roll, pitch, yaw)
    # 角度改變後清掉舊檔案，避免下載到舊圖
    return transformed_preview, None


def render_full_resolution(image: np.ndarray, roll: float, pitch: float, yaw: float):
    if image is None:
        return None

    transformed = _transform_image(image, roll, pitch, yaw)

    output_dir = Path(tempfile.gettempdir()) / "rpy_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    output_file = output_dir / f"rotated_r{int(roll)}_p{int(pitch)}_y{int(yaw)}_{timestamp}.png"

    cv2.imwrite(str(output_file), cv2.cvtColor(transformed, cv2.COLOR_RGB2BGR))
    return str(output_file)


with gr.Blocks(title="Roll Pitch Yaw Image Rotator") as demo:
    gr.Markdown("# Image Roll/Pitch/Yaw Rotator")
    gr.Markdown(
        "上傳一張圖片後，拖曳拉桿會先用快取預覽解析度即時顯示；按下『下載原解析度』時才輸出原圖尺寸。"
    )

    with gr.Row():
        with gr.Column(scale=1):
            input_image = gr.Image(type="numpy", label="上傳照片")
            roll = gr.Slider(-45, 45, value=0, step=1, label="Roll (°)")
            pitch = gr.Slider(-45, 45, value=0, step=1, label="Pitch (°)")
            yaw = gr.Slider(-45, 45, value=0, step=1, label="Yaw (°)")
            reset_btn = gr.Button("重設角度")
        with gr.Column(scale=1):
            output_image = gr.Image(type="numpy", label="即時結果（預覽解析度）")
            render_btn = gr.Button("下載原解析度")
            download_file = gr.File(label="下載圖片")

    inputs = [input_image, roll, pitch, yaw]

    for component in inputs:
        component.change(fn=preview_transform, inputs=inputs, outputs=[output_image, download_file])

    render_btn.click(
        fn=render_full_resolution,
        inputs=inputs,
        outputs=download_file,
    )

    reset_btn.click(
        fn=lambda: (0, 0, 0),
        inputs=None,
        outputs=[roll, pitch, yaw],
    )


demo.launch()
