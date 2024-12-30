
import gradio as gr
import asyncio
import Main
import os 
os.system('playwright install')
os.system('playwright install-deps')

def greet(name, intensity):
    return "Hello, " + name + "!" * int(intensity)

demo = gr.Interface(
    fn=greet,
    inputs=["text", "slider"],
    outputs=["text"],
    live=True
)

asyncio.run(Main.main())
demo.launch(share=True)

# Start the WebSocket server 