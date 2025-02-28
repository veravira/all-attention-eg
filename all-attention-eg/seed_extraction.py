import replicate
import os
client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))
output = replicate.run(
    "veravira/vera:395766afe680dfe63d9cd235471145fbf08d69e46abf99921409a782a538370d",
    input={
        "model": "dev",
        "prompt": "vera is in the museum d'Orsay in Paris",
        "go_fast": False,
        "lora_scale": 1,
        "megapixels": "1",
        "num_outputs": 1,
        "aspect_ratio": "1:1",
        "output_format": "webp",
        "guidance_scale": 3,
        "output_quality": 80,
        "prompt_strength": 0.61,
        "extra_lora_scale": 1,
        "num_inference_steps": 26
    }
)
print(output)