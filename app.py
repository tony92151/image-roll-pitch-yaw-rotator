import math
import tempfile
from pathlib import Path

import cv2
import gradio as gr
import numpy as np


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


def transform_image(image: np.ndarray, roll: float, pitch: float, yaw: float):
    if image is None:
        return None, None

    h, w = image.shape[:2]
    f = max(w, h)

    corners_3d = np.array(
        [
            [-w / 2, -h / 2, 0],
            [w / 2, -h / 2, 0],
            [w / 2, h / 2, 0],
            [-w / 2, h / 2, 0],
        ],
        dtype=np.float32,
    )

    rot = _rotation_matrix(roll, pitch, yaw)
    rotated = corners_3d @ rot.T

    z_shift = 1.5 * f
    zs = rotated[:, 2] + z_shift

    projected = np.column_stack(
        [
            f * (rotated[:, 0] / zs) + w / 2,
            f * (rotated[:, 1] / zs) + h / 2,
        ]
    ).astype(np.float32)

    src = np.array(
        [[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(src, projected)
    transformed = cv2.warpPerspective(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )

    output_dir = Path(tempfile.gettempdir()) / "rpy_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"rotated_r{int(roll)}_p{int(pitch)}_y{int(yaw)}.png"

    cv2.imwrite(str(output_file), cv2.cvtColor(transformed, cv2.COLOR_RGB2BGR))
    return transformed, str(output_file)


with gr.Blocks(title="Roll Pitch Yaw Image Rotator") as demo:
    gr.Markdown("# Image Roll/Pitch/Yaw Rotator")
    gr.Markdown("上傳一張圖片後，使用拉桿調整 roll / pitch / yaw，右側即時顯示結果並可下載。")

    with gr.Row():
        with gr.Column(scale=1):
            input_image = gr.Image(type="numpy", label="上傳照片")
            roll = gr.Slider(-45, 45, value=0, step=1, label="Roll (°)")
            pitch = gr.Slider(-45, 45, value=0, step=1, label="Pitch (°)")
            yaw = gr.Slider(-45, 45, value=0, step=1, label="Yaw (°)")
            reset_btn = gr.Button("重設角度")
        with gr.Column(scale=1):
            output_image = gr.Image(type="numpy", label="即時結果")
            download_file = gr.File(label="下載圖片")

    inputs = [input_image, roll, pitch, yaw]
    outputs = [output_image, download_file]

    for component in inputs:
        component.change(fn=transform_image, inputs=inputs, outputs=outputs)

    reset_btn.click(
        fn=lambda: (0, 0, 0),
        inputs=None,
        outputs=[roll, pitch, yaw],
    )


demo.launch()
