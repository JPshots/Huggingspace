import gradio as gr
import anthropic
import json
import os
from pathlib import Path

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Load framework files
def load_framework_files():
    framework_dir = Path("framework_files")
    framework_data = {}
    
    if framework_dir.exists():
        for file_path in framework_dir.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                framework_data[file_path.stem] = json.load(f)
    
    return framework_data

framework_data = load_framework_files()

# Generate prompt with framework context
def generate_prompt(product_info, framework_files=None):
    if not framework_files:
        framework_files = ["framework-config", "review-strategy", "content-structure", 
                          "personality-balance", "writing-process", "question-framework", 
                          "keyword-strategy"]
    
    # Create context from selected framework files
    framework_context = ""
    for file_name in framework_files:
        if file_name in framework_data:
            framework_context += f"\n\n# {file_name}.json\n"
            framework_context += json.dumps(framework_data[file_name], indent=2)
    
    # Create the prompt
    prompt = f"""You are an expert Amazon review writer following the Amazon Review Framework. 
Use the framework files below to create a high-quality review.

{framework_context}

The user has provided the following product information and experiences:
{product_info}

Based on this information and following the Amazon Review Framework guidelines:
1. First, identify information gaps and ask any necessary questions (following question-framework.json)
2. Once you have sufficient information, create a structured review following the framework
3. Ensure you maintain a balance of information and personality as per personality-balance.json
4. Include appropriate sections as defined in content-structure.json
5. Optimize for search visibility using keyword-strategy.json
6. Follow all quality guidelines from the framework files

Begin by assessing if you have enough information or if you need to ask questions first.
"""
    
    return prompt

# Generate review using Claude
def generate_review(product_info, selected_files):
    prompt = generate_prompt(product_info, selected_files)
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating review: {str(e)}"

# Create the Gradio interface
with gr.Blocks(title="Amazon Review Framework") as demo:
    gr.Markdown("# Amazon Review Framework Generator")
    gr.Markdown("Enter product information and experiences to generate a high-quality Amazon review following the framework.")
    
    with gr.Row():
        with gr.Column(scale=3):
            product_info = gr.Textbox(
                placeholder="Describe your product and experiences here. Include details such as: product name, features, how you used it, what you liked, what you didn't like, etc.",
                label="Product Information",
                lines=10
            )
        
        with gr.Column(scale=1):
            framework_files = gr.CheckboxGroup(
                choices=list(framework_data.keys()),
                value=["framework-config", "review-strategy", "content-structure", 
                      "personality-balance", "writing-process", "question-framework", 
                      "keyword-strategy"],
                label="Framework Files to Include"
            )
    
    generate_button = gr.Button("Generate Review")
    output = gr.Textbox(label="Generated Review", lines=20)
    
    generate_button.click(
        fn=generate_review,
        inputs=[product_info, framework_files],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch()