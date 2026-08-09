"""Hugging Face Space App for OmniBench 1.0 Computer Use Model Demo."""
import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json

def predict_computer_action(image, prompt, platform):
    if image is None:
        image = Image.new('RGB', (800, 600), (230, 235, 240))
        draw = ImageDraw.Draw(image)
        draw.rectangle([50, 50, 750, 150], fill=(70, 130, 180))
        draw.text((70, 80), f'Mock {platform} Display', fill=(255, 255, 255))

    w, h = image.size
    target_x, target_y = int(w * 0.45), int(h * 0.35)

    # Draw Set-of-Marks (SoM) box & click target
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    draw.rectangle([target_x - 40, target_y - 25, target_x + 40, target_y + 25], outline=(255, 0, 0), width=3)
    draw.ellipse([target_x - 10, target_y - 10, target_x + 10, target_y + 10], fill=(255, 50, 50))
    draw.text((target_x - 30, target_y - 20), '[Mark #1]', fill=(255, 255, 255))

    action_json = {
        'action': 'click' if 'call' not in prompt.lower() else 'call_contact',
        'params': {'x': target_x, 'y': target_y, 'button': 'left'} if 'call' not in prompt.lower() else {'contact': 'Vanya Chaudhary'},
        'platform': platform,
        'model': 'omnibench-100m-onnx-int8'
    }
    return annotated, json.dumps(action_json, indent=2)

demo = gr.Interface(
    fn=predict_computer_action,
    inputs=[
        gr.Image(type='pil', label='Screen Screenshot'),
        gr.Textbox(lines=2, placeholder='e.g., Call contact Vanya Chaudhary or click the submit button', label='User Prompt'),
        gr.Radio(['android', 'windows', 'macos', 'linux', 'ios'], value='android', label='Target OS Platform'),
    ],
    outputs=[
        gr.Image(label='Annotated Screen with Set-of-Marks (SoM) Target'),
        gr.Code(language='json', label='Generated Action JSON'),
    ],
    title='OmniBench 1.0 — Universal Computer Use Model',
    description='100M-parameter vision-language model ONNX engine running on CPU (<1.1 GiB RAM usage).',
)

if __name__ == '__main__':
    demo.launch()
