# Images API

> **Source**: https://platform.openai.com/docs/api-reference/images
> **Last Updated**: September 17, 2025

## Overview

Given a prompt and/or an input image, the model will generate a new image. The Images API provides three methods for interacting with images:

- **Creating images** from a text prompt using DALL·E
- **Creating edited versions** of images by having the model replace some areas of a pre-existing image based on a new text prompt
- **Creating variations** of an existing image

## Create Image

Creates an image given a text prompt.

### HTTP Request
```
POST https://api.openai.com/v1/images/generations
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | A text description of the desired image(s). Maximum length is 1000 characters for DALL·E 2 and 4000 characters for DALL·E 3. |
| `model` | string | No | The model to use for image generation. Defaults to `dall-e-2`. |
| `n` | integer | No | The number of images to generate. Must be between 1 and 10. For DALL·E 3, only `n=1` is supported. |
| `quality` | string | No | The quality of the image that will be generated. `hd` creates images with finer details and greater consistency across the image. This param is only supported for DALL·E 3. |
| `response_format` | string | No | The format in which the generated images are returned. Must be one of `url` or `b64_json`. Defaults to `url`. |
| `size` | string | No | The size of the generated images. |
| `style` | string | No | The style of the generated images. Must be one of `vivid` or `natural`. Defaults to `vivid`. This param is only supported for DALL·E 3. |
| `user` | string | No | A unique identifier representing your end-user. |

### Image Sizes

#### DALL·E 3
- `1024x1024` (default)
- `1792x1024`
- `1024x1792`

#### DALL·E 2
- `256x256`
- `512x512`
- `1024x1024` (default)

### Example Requests

#### Basic Image Generation
```python
from openai import OpenAI

client = OpenAI()

response = client.images.generate(
    model="dall-e-3",
    prompt="A cute baby sea otter",
    size="1024x1024",
    quality="standard",
    n=1
)

image_url = response.data[0].url
print(f"Generated image URL: {image_url}")
```

#### High-Quality Image with Style
```python
from openai import OpenAI

client = OpenAI()

response = client.images.generate(
    model="dall-e-3",
    prompt="A futuristic cityscape at sunset with flying cars and neon lights",
    size="1792x1024",
    quality="hd",
    style="vivid",
    n=1
)

image_url = response.data[0].url
revised_prompt = response.data[0].revised_prompt

print(f"Generated image URL: {image_url}")
print(f"Revised prompt: {revised_prompt}")
```

#### Multiple Images with DALL·E 2
```python
from openai import OpenAI

client = OpenAI()

response = client.images.generate(
    model="dall-e-2",
    prompt="A serene mountain landscape with a lake",
    size="1024x1024",
    n=4
)

for i, image_data in enumerate(response.data):
    print(f"Image {i+1}: {image_data.url}")
```

#### Base64 Response Format
```python
import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI

client = OpenAI()

response = client.images.generate(
    model="dall-e-3",
    prompt="A beautiful garden with colorful flowers",
    size="1024x1024",
    response_format="b64_json",
    n=1
)

# Decode and save image
image_data = base64.b64decode(response.data[0].b64_json)
image = Image.open(BytesIO(image_data))
image.save("generated_image.png")

print("Image saved as generated_image.png")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "dall-e-3",
    "prompt": "A white siamese cat",
    "n": 1,
    "size": "1024x1024"
  }'
```

### Response Object

```json
{
  "created": 1589478378,
  "data": [
    {
      "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/...",
      "revised_prompt": "A realistic image of a white Siamese cat with blue eyes, sitting gracefully on a soft cushion."
    }
  ]
}
```

## Create Image Edit

Creates an edited or extended image given an original image and a prompt.

### HTTP Request
```
POST https://api.openai.com/v1/images/edits
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | file | Yes | The image to edit. Must be a valid PNG file, less than 4MB, and square. |
| `mask` | file | No | An additional image whose fully transparent areas indicate where image should be edited. Must be a valid PNG file, less than 4MB, and have the same dimensions as image. |
| `prompt` | string | Yes | A text description of the desired image(s). Maximum length is 1000 characters. |
| `model` | string | No | The model to use for image generation. Only `dall-e-2` is supported. |
| `n` | integer | No | The number of images to generate. Must be between 1 and 10. |
| `size` | string | No | The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`. |
| `response_format` | string | No | The format in which the generated images are returned. Must be one of `url` or `b64_json`. |
| `user` | string | No | A unique identifier representing your end-user. |

### Example Requests

#### Basic Image Edit
```python
from openai import OpenAI

client = OpenAI()

response = client.images.edit(
    model="dall-e-2",
    image=open("original_image.png", "rb"),
    mask=open("mask.png", "rb"),
    prompt="A sunlit indoor lounge area with a pool",
    n=1,
    size="1024x1024"
)

image_url = response.data[0].url
print(f"Edited image URL: {image_url}")
```

#### Edit Without Mask
```python
from openai import OpenAI

client = OpenAI()

# When no mask is provided, the entire image is considered for editing
response = client.images.edit(
    model="dall-e-2",
    image=open("room_image.png", "rb"),
    prompt="Same room but with modern furniture and bright lighting",
    n=2,
    size="1024x1024"
)

for i, image_data in enumerate(response.data):
    print(f"Edited image {i+1}: {image_data.url}")
```

#### Creating a Mask Programmatically
```python
from PIL import Image, ImageDraw
import numpy as np
from openai import OpenAI

def create_circular_mask(image_path, center, radius):
    """Create a circular mask for image editing"""
    # Load the original image
    img = Image.open(image_path)
    width, height = img.size

    # Create a new image for the mask
    mask = Image.new('RGBA', (width, height), (0, 0, 0, 255))  # Black background
    draw = ImageDraw.Draw(mask)

    # Draw a white circle (transparent area for editing)
    left = center[0] - radius
    top = center[1] - radius
    right = center[0] + radius
    bottom = center[1] + radius

    draw.ellipse([left, top, right, bottom], fill=(0, 0, 0, 0))  # Transparent circle

    return mask

# Create mask and edit image
original_image_path = "portrait.png"
mask = create_circular_mask(original_image_path, (512, 512), 200)
mask.save("circular_mask.png")

client = OpenAI()

response = client.images.edit(
    model="dall-e-2",
    image=open(original_image_path, "rb"),
    mask=open("circular_mask.png", "rb"),
    prompt="A person wearing a stylish hat",
    n=1,
    size="1024x1024"
)

print(f"Edited image URL: {response.data[0].url}")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/images/edits \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F image="@otter.png" \
  -F mask="@mask.png" \
  -F prompt="A cute baby sea otter wearing a beret" \
  -F n=2 \
  -F size="1024x1024"
```

## Create Image Variation

Creates a variation of a given image.

### HTTP Request
```
POST https://api.openai.com/v1/images/variations
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | file | Yes | The image to create a variation of. Must be a valid PNG file, less than 4MB, and square. |
| `model` | string | No | The model to use for image generation. Only `dall-e-2` is supported. |
| `n` | integer | No | The number of images to generate. Must be between 1 and 10. |
| `response_format` | string | No | The format in which the generated images are returned. Must be one of `url` or `b64_json`. |
| `size` | string | No | The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`. |
| `user` | string | No | A unique identifier representing your end-user. |

### Example Requests

#### Basic Image Variation
```python
from openai import OpenAI

client = OpenAI()

response = client.images.create_variation(
    image=open("original_image.png", "rb"),
    n=2,
    size="1024x1024"
)

for i, image_data in enumerate(response.data):
    print(f"Variation {i+1}: {image_data.url}")
```

#### Multiple Variations with Base64
```python
import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI

client = OpenAI()

response = client.images.create_variation(
    image=open("source_image.png", "rb"),
    n=4,
    size="1024x1024",
    response_format="b64_json"
)

for i, image_data in enumerate(response.data):
    # Decode and save each variation
    image_bytes = base64.b64decode(image_data.b64_json)
    image = Image.open(BytesIO(image_bytes))
    image.save(f"variation_{i+1}.png")

print(f"Generated {len(response.data)} variations")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/images/variations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F image="@image.png" \
  -F n=2 \
  -F size="1024x1024"
```

## Advanced Use Cases

### Batch Image Generation
```python
from openai import OpenAI
import time
import requests
from pathlib import Path

client = OpenAI()

class BatchImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_images_from_prompts(self, prompts, model="dall-e-3"):
        """Generate images from a list of prompts"""
        results = []

        for i, prompt in enumerate(prompts):
            print(f"Generating image {i+1}/{len(prompts)}: {prompt[:50]}...")

            try:
                response = client.images.generate(
                    model=model,
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard" if model == "dall-e-3" else None,
                    n=1
                )

                # Download and save image
                image_url = response.data[0].url
                image_response = requests.get(image_url)

                if image_response.status_code == 200:
                    filename = f"image_{i+1:03d}.png"
                    file_path = self.output_dir / filename

                    with open(file_path, "wb") as f:
                        f.write(image_response.content)

                    result = {
                        "prompt": prompt,
                        "file_path": str(file_path),
                        "url": image_url,
                        "success": True
                    }

                    if model == "dall-e-3":
                        result["revised_prompt"] = response.data[0].revised_prompt

                    results.append(result)
                    print(f"  ✓ Saved to {filename}")

                else:
                    results.append({
                        "prompt": prompt,
                        "error": f"Failed to download image: {image_response.status_code}",
                        "success": False
                    })

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                results.append({
                    "prompt": prompt,
                    "error": str(e),
                    "success": False
                })
                print(f"  ✗ Error: {e}")

        return results

# Example usage
prompts = [
    "A serene mountain lake at sunrise",
    "A futuristic robot gardening in a greenhouse",
    "An abstract painting with bold colors and geometric shapes",
    "A cozy library with floating books and magical lighting",
    "A steampunk airship flying through cloudy skies"
]

generator = BatchImageGenerator()
results = generator.generate_images_from_prompts(prompts)

# Print summary
successful = sum(1 for r in results if r["success"])
print(f"\nGenerated {successful}/{len(prompts)} images successfully")
```

### Image Style Transfer Workflow
```python
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO

client = OpenAI()

class StyleTransferWorkflow:
    def __init__(self):
        self.client = client

    def create_style_variations(self, base_prompt, styles, model="dall-e-3"):
        """Create multiple style variations of the same concept"""
        variations = []

        for style in styles:
            styled_prompt = f"{base_prompt}, {style}"
            print(f"Generating: {styled_prompt}")

            try:
                response = self.client.images.generate(
                    model=model,
                    prompt=styled_prompt,
                    size="1024x1024",
                    quality="hd" if model == "dall-e-3" else None,
                    n=1
                )

                variations.append({
                    "style": style,
                    "prompt": styled_prompt,
                    "url": response.data[0].url,
                    "revised_prompt": response.data[0].revised_prompt if model == "dall-e-3" else None
                })

            except Exception as e:
                print(f"Error generating {style}: {e}")

        return variations

    def download_and_display_grid(self, variations, grid_size=(2, 2)):
        """Download images and create a comparison grid"""
        images = []

        for variation in variations[:grid_size[0] * grid_size[1]]:
            try:
                response = requests.get(variation["url"])
                img = Image.open(BytesIO(response.content))
                images.append(img)
            except Exception as e:
                print(f"Error downloading {variation['style']}: {e}")

        if not images:
            return None

        # Create grid
        img_width, img_height = images[0].size
        grid_width = grid_size[1] * img_width
        grid_height = grid_size[0] * img_height
        grid_image = Image.new('RGB', (grid_width, grid_height))

        for i, img in enumerate(images):
            row = i // grid_size[1]
            col = i % grid_size[1]
            x = col * img_width
            y = row * img_height
            grid_image.paste(img, (x, y))

        return grid_image

# Example usage
styles = [
    "in the style of Van Gogh",
    "photorealistic",
    "anime art style",
    "watercolor painting"
]

workflow = StyleTransferWorkflow()
variations = workflow.create_style_variations(
    "A peaceful garden with cherry blossoms",
    styles
)

# Create and save comparison grid
grid = workflow.download_and_display_grid(variations)
if grid:
    grid.save("style_comparison_grid.png")
    print("Style comparison grid saved!")
```

### Interactive Image Editor
```python
from openai import OpenAI
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
from io import BytesIO
import threading

class InteractiveImageEditor:
    def __init__(self):
        self.client = OpenAI()
        self.root = tk.Tk()
        self.root.title("AI Image Editor")
        self.root.geometry("800x600")

        self.current_image = None
        self.mask_image = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Image frame
        image_frame = ttk.LabelFrame(main_frame, text="Image", padding="10")
        image_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.image_label = ttk.Label(image_frame, text="No image loaded")
        self.image_label.grid(row=0, column=0)

        # Controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Buttons
        ttk.Button(controls_frame, text="Load Image", command=self.load_image).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(controls_frame, text="Create Mask", command=self.create_mask).grid(row=0, column=1, padx=5)
        ttk.Button(controls_frame, text="Generate Variation", command=self.generate_variation).grid(row=0, column=2, padx=5)

        # Prompt frame
        prompt_frame = ttk.LabelFrame(main_frame, text="Edit Prompt", padding="10")
        prompt_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.prompt_var = tk.StringVar()
        prompt_entry = ttk.Entry(prompt_frame, textvariable=self.prompt_var, width=60)
        prompt_entry.grid(row=0, column=0, padx=(0, 5))

        ttk.Button(prompt_frame, text="Edit Image", command=self.edit_image).grid(row=0, column=1)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=3, column=0, columnspan=2, sticky=tk.W)

    def load_image(self):
        """Load an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.display_image(self.current_image)
                self.status_var.set(f"Loaded: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def display_image(self, image):
        """Display image in the UI"""
        # Resize for display
        display_image = image.copy()
        display_image.thumbnail((400, 400), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(display_image)
        self.image_label.configure(image=photo, text="")
        self.image_label.image = photo  # Keep a reference

    def create_mask(self):
        """Create a simple mask (placeholder for more complex mask creation)"""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        # Create a simple circular mask in the center
        width, height = self.current_image.size
        mask = Image.new('RGBA', (width, height), (0, 0, 0, 255))  # Black background
        draw = ImageDraw.Draw(mask)

        # Draw white circle (transparent area)
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 4

        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], fill=(0, 0, 0, 0))

        self.mask_image = mask
        self.status_var.set("Mask created (center circle)")

    def generate_variation(self):
        """Generate a variation of the current image"""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        def generate():
            try:
                self.status_var.set("Generating variation...")

                # Save image temporarily
                temp_path = "temp_image.png"
                self.current_image.save(temp_path)

                response = self.client.images.create_variation(
                    image=open(temp_path, "rb"),
                    n=1,
                    size="1024x1024"
                )

                # Download and display result
                image_url = response.data[0].url
                image_response = requests.get(image_url)
                result_image = Image.open(BytesIO(image_response.content))

                self.current_image = result_image
                self.display_image(result_image)
                self.status_var.set("Variation generated successfully")

            except Exception as e:
                self.status_var.set(f"Error: {e}")
                messagebox.showerror("Error", f"Failed to generate variation: {e}")

        # Run in separate thread to avoid blocking UI
        threading.Thread(target=generate, daemon=True).start()

    def edit_image(self):
        """Edit the image with the given prompt"""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        prompt = self.prompt_var.get().strip()
        if not prompt:
            messagebox.showwarning("Warning", "Please enter an edit prompt")
            return

        def edit():
            try:
                self.status_var.set("Editing image...")

                # Save images temporarily
                temp_image_path = "temp_image.png"
                self.current_image.save(temp_image_path)

                edit_params = {
                    "model": "dall-e-2",
                    "image": open(temp_image_path, "rb"),
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024"
                }

                if self.mask_image:
                    temp_mask_path = "temp_mask.png"
                    self.mask_image.save(temp_mask_path)
                    edit_params["mask"] = open(temp_mask_path, "rb")

                response = self.client.images.edit(**edit_params)

                # Download and display result
                image_url = response.data[0].url
                image_response = requests.get(image_url)
                result_image = Image.open(BytesIO(image_response.content))

                self.current_image = result_image
                self.display_image(result_image)
                self.status_var.set("Image edited successfully")

            except Exception as e:
                self.status_var.set(f"Error: {e}")
                messagebox.showerror("Error", f"Failed to edit image: {e}")

        # Run in separate thread
        threading.Thread(target=edit, daemon=True).start()

    def run(self):
        """Start the application"""
        self.root.mainloop()

# Usage
if __name__ == "__main__":
    editor = InteractiveImageEditor()
    editor.run()
```

## Error Handling

### Common Errors and Solutions

```python
from openai import OpenAI
import openai

client = OpenAI()

def safe_image_generation(prompt, **kwargs):
    """Generate image with comprehensive error handling"""
    try:
        response = client.images.generate(
            prompt=prompt,
            **kwargs
        )
        return {"success": True, "data": response.data}

    except openai.BadRequestError as e:
        error_message = str(e).lower()
        if "content policy" in error_message:
            return {"success": False, "error": "Prompt violates content policy"}
        elif "prompt" in error_message and "long" in error_message:
            return {"success": False, "error": "Prompt too long"}
        else:
            return {"success": False, "error": f"Bad request: {e}"}

    except openai.RateLimitError:
        return {"success": False, "error": "Rate limit exceeded"}

    except openai.AuthenticationError:
        return {"success": False, "error": "Invalid API key"}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}

def safe_image_edit(image_path, prompt, mask_path=None, **kwargs):
    """Edit image with error handling"""
    try:
        edit_params = {
            "image": open(image_path, "rb"),
            "prompt": prompt,
            **kwargs
        }

        if mask_path:
            edit_params["mask"] = open(mask_path, "rb")

        response = client.images.edit(**edit_params)
        return {"success": True, "data": response.data}

    except FileNotFoundError as e:
        return {"success": False, "error": f"Image file not found: {e}"}

    except openai.BadRequestError as e:
        error_message = str(e).lower()
        if "image" in error_message and "size" in error_message:
            return {"success": False, "error": "Image must be PNG, square, and under 4MB"}
        elif "mask" in error_message:
            return {"success": False, "error": "Mask must be PNG with same dimensions as image"}
        else:
            return {"success": False, "error": f"Bad request: {e}"}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}

# Usage examples
result = safe_image_generation("A beautiful sunset over mountains")
if result["success"]:
    print(f"Generated image: {result['data'][0].url}")
else:
    print(f"Error: {result['error']}")

edit_result = safe_image_edit("image.png", "Add a rainbow in the sky")
if edit_result["success"]:
    print(f"Edited image: {edit_result['data'][0].url}")
else:
    print(f"Error: {edit_result['error']}")
```

## Best Practices

### Prompt Engineering for Images
- Be specific and descriptive
- Include style, mood, and technical details
- Use composition terms (close-up, wide shot, etc.)
- Specify lighting and color preferences
- Include artistic styles or references

### Cost Optimization
- Use DALL·E 2 for experimentation and iterations
- Use DALL·E 3 for final, high-quality images
- Cache and reuse generated images when possible
- Use smaller sizes for prototyping

### Technical Considerations
- Ensure images are PNG format for editing
- Keep images under 4MB for API limits
- Use square images for best results
- Prepare proper masks for targeted editing

### Content Policy Compliance
- Avoid generating images of public figures
- Don't create misleading or harmful content
- Respect copyright and intellectual property
- Follow OpenAI's usage policies

---

*This documentation covers the complete Images API including DALL·E 2 and DALL·E 3 image generation, editing, and variation creation. Use these APIs to build powerful image generation applications.*
